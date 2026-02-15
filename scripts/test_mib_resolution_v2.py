import sys
import os
import logging
from pysnmp.proto.rfc1902 import ObjectIdentifier

# プロジェクトルートをPYTHONPATHに追加
sys.path.append(os.getcwd())

# ログ設定
logging.basicConfig(level=logging.DEBUG)

try:
    from src.resolver import MibResolver
    
    print("Initializing MibResolver...")
    resolver = MibResolver()
    
    # テスト対象のOID (TEST-MIB::testObject)
    # .1.3.6.1.4.1.99999.1
    test_oid_str = "1.3.6.1.4.1.99999.1"
    
    # 文字列の代わりにタプルで渡してみる
    test_oid_tuple = tuple(int(x) for x in test_oid_str.split('.'))
    
    print(f"Resolving OID (tuple): {test_oid_tuple}")
    result = resolver.resolve(test_oid_tuple)
    
    print("Resolution Result:")
    print(result)
    
    if result.get("mib") == "TEST-MIB" and result.get("name") == "testObject":
        print("SUCCESS: OID resolved correctly using TEST-MIB.")
        sys.exit(0)
    else:
        print("FAILURE: OID resolution did not return expected MIB or object name.")
        sys.exit(1)

except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
