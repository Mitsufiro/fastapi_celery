from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi_sqlalchemy import DBSessionMiddleware, db
import os
from fastapi.logger import logger
from database import db_context
from schemas.schemas import Users, TokenData, UserInDB, Token
from models import Token as ModelToken
from models import User as ModelUser

load_dotenv('.env')
app = FastAPI(title='Mailing Service',version='0.0.1')
app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])

from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "420e67554ffba171509b6209139d2320711a8627a8a4f68c5747dbcd3f695b2b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@example.com",
#         "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
#         "disabled": False,
#     }
# }

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def get_user_from_db(username: str):
    with db_context() as db:
        user = db.query(ModelUser).filter(ModelUser.username == username).first()
        return Users(username=user.username, hashed_password=user.hashed_password, role=user.role, email=user.email,
                     disabled=user.disabled, full_name=user.full_name)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def authenticate_user_from_db(username: str, password: str):
    user = get_user_from_db(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_from_db(username=token_data.username)
    # print(user)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Users = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Users = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            logger.debug(f"User with role {user.role} not in {self.allowed_roles}")
            raise HTTPException(status_code=403,
                                detail="Operation not permitted. You don't have sufficient rights to use this method")


# admin_create_resource = RoleChecker(role: str)


@app.post("/token", response_model=Token, tags=['User'])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user_from_db(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=Users, tags=['User'])
async def read_users_me(current_user: Users = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items/", tags=['User'])
async def read_own_items(current_user: Users = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.post('/create_user', tags=['User'])
async def create_user(username: str, password: str):
    password_hash = get_password_hash(password)
    db_user = ModelUser(username=username, hashed_password=password_hash)
    db.session.add(db_user)
    db.session.commit()
    db.session.refresh(db_user)
    token_data = Users(username=username, hashed_password=password_hash)
    access_token = create_access_token(token_data.dict())
    db_token = ModelToken(user_id=db_user.id, access_token=access_token)
    db.session.add(db_token)
    db.session.commit()
    db.session.refresh(db_token)
    return db_token.access_token


@app.put('/update_user', tags=['User'])
async def update_user(user_id: int,
                      disabled: bool | None = Query(default=False), role: str | None = Query(default=None)):
    client = db.session.query(ModelUser).get(user_id)
    if disabled != None:
        client.disabled = disabled
    else:
        client.disabled = client.disabled
    if role != None:
        client.role = role
    else:
        client.role = client.role
    db.session.commit()
    return db.session.get(ModelUser, user_id)
