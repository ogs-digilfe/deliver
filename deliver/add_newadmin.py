import os, json, getpass, hashlib, base64
from pathlib import Path
from datetime import datetime
from typing import Union


CURRENT_DIR = Path(os.path.abspath(__file__)).parent
PJ_DIR = CURRENT_DIR
WS_DIR = PJ_DIR.parent
USERDB_DIR = WS_DIR / "userdb"
USERDB_FNAME = "users"
TSFORMAT = "%Y-%m-%d %H:%M:%S"

class PasswordMismatchError(Exception):
    pass
    
def input_admin_info():
    username =           input("           user: ")
    password = getpass.getpass("       password: ")
    retyped  = getpass.getpass("retype password: ")
    
    if password != retyped:
        raise PasswordMismatchError("パスワードがマッチしません")
    
    return {
        "username": username,
        "password": password,
    }

def read_userdb():
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

# 生成したsaltを使ってsalthased_passwordを生成する
def generate_hashed_password(raw_password: str):
    binary_salt = os.urandom(16)
    salt = base64.b64encode(binary_salt).decode('utf-8')
    
    return salt, hashlib.sha256(binary_salt + raw_password.encode()).hexdigest()

# passwordとsaltからhased_passwordを計算する
def get_hashed_password(salt: Union[str, bytes], raw_password: str):
    if type(salt) == type("string"):
        binary_salt = base64.b64decode(salt)
    else:
        binary_salt = salt
    
    print(type(binary_salt))
    
    return hashlib.sha256(binary_salt + raw_password.encode()).hexdigest()
    

def add_newadmin():
    newadmin_dct = input_admin_info()
    userdb_dct = read_userdb()

    new_admin_username = newadmin_dct["username"]
    new_admin_password = newadmin_dct["password"]
    
    if new_admin_username in userdb_dct.keys():
        raise ValueError(f'ユーザ{new_admin_username}はすでにユーザデータベースに登録されています')
    
    salt, hashed_password = generate_hashed_password(new_admin_password)
    
    timestamp = datetime.now().strftime(TSFORMAT)
    
    userdb_dct[new_admin_username] = {
        "username": new_admin_username,
        "hashed_password": hashed_password,
        "salt": salt,
        "role": "admin",
        "status": "active",
        "registered": timestamp,
        "updated": timestamp
    }

    fp = str(USERDB_DIR/USERDB_FNAME)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(userdb_dct, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    add_newadmin()
    
    '''
    userdb_dct = read_userdb()
    print(json.dumps(userdb_dct, indent=4, ensure_ascii=False))
    
    db_hashed_password = userdb_dct["ogs-digilife"]["hashed_password"]
    db_salt = userdb_dct["ogs-digilife"]["salt"]
    hased_password = get_hashed_password(db_salt, secret)
    
    print(f'db_hashed_password={db_hashed_password}, calucurated_hased_password={hased_password}')
    '''
    