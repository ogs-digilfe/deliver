import os, hashlib, json, base64
from pathlib import Path
from typing import Union

CURRENT_DIR = Path(os.path.abspath(__file__)).parent
PJ_DIR = CURRENT_DIR
WS_DIR = PJ_DIR.parent
USERDB_DIR = WS_DIR / "userdb"
USERDB_FNAME = "users"

def get_hashed_password(salt: Union[str, bytes], raw_password: str):
    if type(salt) == type("string"):
        binary_salt = base64.b64decode(salt)
    else:
        binary_salt = salt
    
    return hashlib.sha256(binary_salt + raw_password.encode()).hexdigest()

class UserDb():
    def __init__(self):
        self.userdb = self.read_userdb()
    
    def read_userdb(self):
        dp = str(USERDB_DIR)
        fp = str(USERDB_DIR/USERDB_FNAME)
        
        # dirがなければ作成
        if not os.path.exists(dp):
            os.makedirs(dp)
            return {}
        
        # fileが無ければ空の辞書を返す
        elif not os.path.exists(fp):
            return {}
        
        # fileが存在する場合は、json形式のファイルを読み込んで辞書で返す
        else:
            with open(fp, "r", encoding="utf-8") as f:
                user_dct = json.load(f)
            return user_dct