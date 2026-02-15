import sys
import os
import logging

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
    test_oid = "1.3.6.1.4.1.99999.1"
    
    print(f"Resolving OID: {test_oid}")
    result = resolver.resolve(test_oid)
    
    print("Resolution Result:")
    print(result)
    
    if result.get("mib") == "TEST-MIB" and result.get("name") == "testObject":
        print("SUCCESS: OID resolved correctly using TEST-MIB.")
        sys.exit(0)
    else:
        print("FAILURE: OID resolution did not return expected MIB or object name.")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
