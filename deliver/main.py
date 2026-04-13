####
# $ uvicorn main:app --reload --host 0.0.0.0 --port 8080
####
import secrets, os
from typing import Annotated, Literal
from pydantic import BaseModel
from datetime import date
import polars as pl
from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse

from lib_deliver import UserDb, get_hashed_password

# global objects
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

USERDB = UserDb()

TOKENDB = {}

# path
from pathlib import Path
CURRENT_DIR =  Path(os.path.abspath(__file__)).parent

# dataディレクトリ
DATA_DIR = CURRENT_DIR / "data"
data_dir = str(DATA_DIR)
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# download用一時ディレクトリ
TMP_DIR = CURRENT_DIR / "tmp"
tmp_dir = str(TMP_DIR)
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)


### 型定義
class UserInDb(BaseModel):
    username: str
    hashed_password: str
    salt: str
    role: Literal["admin", "user", "guest"]
    status: Literal["active", "inactive"]
    registered: str
    updated: str


### Tokenの発行
### usernameとpasswordがマッチしたTokenを発行してTOKENDBにtokenをキーとして
### ログイン有効なユーザを登録する
@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = USERDB.userdb.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # debug
    print("debug:")
    print(user_dict)
    print()
    
    
    user = UserInDb(**user_dict)
    hashed_password = get_hashed_password(user.salt, form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # ランダムなトークンを発行
    access_token = secrets.token_hex(32)
    
    # usernameとpasswordがマッチしたら発行したTokenをキーとして該当ユーザ(=tokenが発行されたユーザ)をtokens_dbに保存
    TOKENDB[access_token] = user

    return {"access_token": access_token, "token_type": "bearer"}

### 認証関数
def decode_token(token: str):
    # 指定したトークンのキーがトークンデータベースに存在するかを確認し、
    # Tokenがあったら対応するユーザーを返す
    # ない場合はToeknがアンマッチなのでraise HTTPExceptionする
    user = TOKENDB.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return decode_token(token)

async def get_current_active_user(
    current_user: Annotated[UserInDb, Depends(get_current_user)],
):
    if current_user.status == "inactive":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: Annotated[UserInDb, Depends(get_current_active_user)]):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Fobiden")
    return current_user

### end points
# test用
@app.get("/logintest")
async def read_users_me(
    current_user: Annotated[UserInDb, Depends(get_current_active_user)]
):
    return current_user

# file update
@app.post("/upload/")
async def upload_file(
    current_admin_user: Annotated[UserInDb, Depends(get_admin_user)],
    file: UploadFile=File(...), 
):
    fp = os.path.join(data_dir, file.filename)
    
    with open(fp, "wb") as b:
        b.write(await file.read())
    
    return {
        "user": current_admin_user,
        "upload_file": file.filename
    }

@app.post("/upload-kabutan-kessan/")
async def upload_shikiho_online_file(
    current_admin_user: Annotated[UserInDb, Depends(get_admin_user)],
    file: UploadFile=File(...), 
):
    fp = DATA_DIR / "html" / "kabutan-kessan" / file.filename
    
    with open(fp, "wb") as b:
        b.write(await file.read())
    
    return {
        "user": current_admin_user,
        "upload_file": file.filename
    }

@app.post("/upload-shikiho/")
async def upload_shikiho_online_file(
    current_admin_user: Annotated[UserInDb, Depends(get_admin_user)],
    file: UploadFile=File(...), 
):
    output_dir = DATA_DIR / "html" / "shikiho"
    fp = DATA_DIR / "html" / "shikiho" / file.filename

    # ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(fp, "wb") as b:
        b.write(await file.read())
    
    return {
        "user": current_admin_user,
        "upload_file": file.filename
    }

@app.post("/upload-shikiho-online/")
async def upload_shikiho_online_file(
    current_admin_user: Annotated[UserInDb, Depends(get_admin_user)],
    file: UploadFile=File(...), 
):
    fp = DATA_DIR / "html" / "shikiho-online" / file.filename
    
    with open(fp, "wb") as b:
        b.write(await file.read())
    
    return {
        "user": current_admin_user,
        "upload_file": file.filename
    }

# file download
@app.get("/download/")
async def download_file(
    current_admin_user: Annotated[UserInDb, Depends(get_current_active_user)],
    filename: str,
):
    fp = os.path.join(data_dir, filename)

    # ファイルが存在するか確認
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail="File not found")    
    
    # ファイルをレスポンスとして返す
    return FileResponse(fp, media_type='application/octet-stream', filename=filename)

@app.get("/download-kabutan-kessan/")
async def download_kabutan_kessan_file(
    current_admin_user: Annotated[UserInDb, Depends(get_current_active_user)],
):
    filename = "kabutan_kessan.zip"
    fp = DATA_DIR / "html" / "kabutan-kessan" / filename

    # ファイルが存在するか確認
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail="File not found")    
    
    # ファイルをレスポンスとして返す
    return FileResponse(fp, media_type='application/octet-stream', filename=filename)

@app.get("/download-shikiho-online/")
async def download_shikiho_online_file(
    current_admin_user: Annotated[UserInDb, Depends(get_current_active_user)],
    filename: str,
):
    fp = DATA_DIR / "html" / "shikiho-online" / filename

    # ファイルが存在するか確認
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail="File not found")    
    
    # ファイルをレスポンスとして返す
    return FileResponse(fp, media_type='application/octet-stream', filename=filename)
