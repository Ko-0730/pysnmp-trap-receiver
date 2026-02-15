import os
import sys
import glob
from pysmi.reader import FileReader, HttpReader
from pysmi.searcher import StubSearcher
from pysmi.writer import PyFileWriter
from pysmi.parser import SmiStarParser
from pysmi.codegen import PySnmpCodeGen
from pysmi.compiler import MibCompiler

def compile_mibs(src_dir, dest_dir):
    """
    指定されたソースディレクトリにあるすべてのMIBファイルをコンパイルし、
    指定された出力ディレクトリに保存します。
    """
    if not os.path.exists(src_dir):
        print(f"Source directory not found: {src_dir}")
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    print(f"Initializing MibCompiler with output to {dest_dir}")
    # pysmiのMibCompilerを使用
    mibCompiler = MibCompiler(
        SmiStarParser(),
        PySnmpCodeGen(),
        PyFileWriter(dest_dir)
    )

    # ローカルのMIBソースディレクトリを探索して追加
    print(f"Scanning source directory: {src_dir}")
    source_dirs = set()
    mib_modules = []
    
    # os.walkで再帰的に探索
    for root, dirs, files in os.walk(src_dir):
        # MIBファイルを含むディレクトリをソースとして追加するため記録
        has_mib = False
        for f in files:
            # 拡張子チェック (.mib, .my, .txt)
            if f.endswith(('.mib', '.my', '.txt')) and not f.startswith('.'):
                has_mib = True
                filename = os.path.basename(f)
                # 拡張子を取り除く
                module_name = os.path.splitext(filename)[0]
                mib_modules.append(module_name)
        
        if has_mib:
            source_dirs.add(root)
    
    if not source_dirs:
        print(f"No MIB files found in {src_dir} or its subdirectories")
        return

    # 各ディレクトリをソースとして追加
    for d in source_dirs:
        print(f"Adding source directory: {d}")
        try:
            # pysmi >= 1.0.0 uses add_sources
            mibCompiler.add_sources(FileReader(d))
        except AttributeError:
            # pysmi < 1.0.0 uses addSources
            mibCompiler.addSources(FileReader(d))

    # 標準的なMIBソースも追加（依存関係解決のため）
    # 注: インターネット接続が必要
    print("Adding HTTP source: https://mibs.pysnmp.com/asn1/@mib@")
    try:
        try:
            mibCompiler.add_sources(HttpReader('https://mibs.pysnmp.com/asn1/@mib@'))
        except AttributeError:
            mibCompiler.addSources(HttpReader('https://mibs.pysnmp.com/asn1/@mib@'))
    except Exception as e:
        print(f"Warning: Could not add HTTP source: {e}")

    # 検索パスの設定（ローカル優先）
    try:
        mibCompiler.add_searchers(StubSearcher(*list(source_dirs)))
    except AttributeError:
        mibCompiler.addSearchers(StubSearcher(*list(source_dirs)))

    if not mib_modules:
        print(f"No MIB files found in {src_dir}")
        return

    print(f"Compiling {len(mib_modules)} MIB modules from {src_dir} to {dest_dir}...")
    
    # コンパイル実行
    try:
        results = mibCompiler.compile(*mib_modules)
        
        success_count = 0
        fail_count = 0
        
        # resultsはdict {module_name: status}
        for module_name, status in results.items():
            if status == 'compiled':
                success_count += 1
                print(f"  [OK] {module_name}")
            elif status == 'failed':
                fail_count += 1
                print(f"  [FAIL] {module_name}")
            elif status == 'untouched': # Already up to date
                print(f"  [SKIP] {module_name} (Up to date)")
                success_count += 1
            else:
                # 'borrowed' or other statuses
                print(f"  [{status}] {module_name}")
                success_count += 1

        print(f"Compilation finished: {success_count} succeeded, {fail_count} failed.")
        
        if fail_count > 0:
            print("Warning: Some MIBs failed to compile.")
            
    except Exception as e:
        print(f"Error during compilation: {e}")
        # スクリプト自体のエラーは終了コード1
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compile_mibs.py <src_dir> <dest_dir>")
        sys.exit(1)
    
    src_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    compile_mibs(src_dir, dest_dir)
