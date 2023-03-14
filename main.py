from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sqlalchemy import db
from starlette import status
from dotenv import load_dotenv
from fastapi_sqlalchemy import DBSessionMiddleware
import os
from routers import clients, mailinglist, message
from models import User as ModelUser, Token as ModelToken
from routers.auth import authenticate_user_from_db, create_access_token, get_current_active_user, get_password_hash
from schemas.schemas import Token, Users

load_dotenv('.env')
app = FastAPI(title='Mailing Service', version='0.0.1')
app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])
app.include_router(clients.ROUTER)
app.include_router(mailinglist.ROUTER)
app.include_router(message.ROUTER)


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
