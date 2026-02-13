import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
import tempfile
from src.resolver import MibResolver
from src.config import settings

class TestMibResolverLoading(unittest.TestCase):
    def setUp(self):
        # 一時ディレクトリの作成
        self.test_dir = tempfile.mkdtemp()
        self.original_mib_dir = settings.mib_dir
        settings.mib_dir = self.test_dir

    def tearDown(self):
        # 一時ディレクトリの削除と設定の復元
        shutil.rmtree(self.test_dir)
        settings.mib_dir = self.original_mib_dir

    @patch('src.resolver.builder.MibBuilder')
    @patch('src.resolver.view.MibViewController')
    def test_load_modules_from_directory(self, mock_view_controller, mock_builder_class):
        # モックの設定
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        
        # ダミーのMIBファイルを作成
        with open(os.path.join(self.test_dir, 'TEST-MIB.py'), 'w') as f:
            f.write("# Dummy MIB")
        
        with open(os.path.join(self.test_dir, 'ANOTHER-MIB.py'), 'w') as f:
            f.write("# Another Dummy MIB")
            
        # 無視されるべきファイル
        with open(os.path.join(self.test_dir, '__init__.py'), 'w') as f:
            f.write("")
        with open(os.path.join(self.test_dir, 'README.txt'), 'w') as f:
            f.write("")

        # Resolverのインスタンス化（ここでロード処理が走る）
        resolver = MibResolver()

        # 検証
        # TEST-MIB と ANOTHER-MIB がロードされたことを確認
        # 呼び出し順序はos.listdir依存なので、AnyOrderで確認するか、呼び出しリストを取得して検証
        
        loaded_modules = []
        for call in mock_builder.loadModules.call_args_list:
            args, _ = call
            loaded_modules.append(args[0])
            
        self.assertIn('TEST-MIB', loaded_modules)
        self.assertIn('ANOTHER-MIB', loaded_modules)
        self.assertNotIn('__init__', loaded_modules)
        self.assertNotIn('README', loaded_modules)
        
        # 標準MIBがハードコードされていないことも確認（ロード呼び出しに含まれていないこと、
        # あるいはディレクトリに存在しない限り呼ばれないこと）
        # ただし、pysnmpが内部的に何かロードする可能性はあるが、明示的な呼び出しはここだけのはず
        
    @patch('src.resolver.builder.MibBuilder')
    @patch('src.resolver.view.MibViewController')
    def test_empty_directory(self, mock_view_controller, mock_builder_class):
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        
        # 空のディレクトリで実行
        resolver = MibResolver()
        
        # loadModulesが呼ばれていないこと（または呼ばれても空リストではないことの確認など）
        # 実装ではループ内で呼ばれるので、ファイルがなければ呼ばれないはず
        self.assertEqual(mock_builder.loadModules.call_count, 0)

if __name__ == '__main__':
    unittest.main()
