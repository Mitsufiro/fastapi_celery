# build a schema using pydantic
from typing import Optional

from pydantic import BaseModel


class Client(BaseModel):
    tel_num: Optional[int] = None
    tag: Optional[str] = None
    mob_code: Optional[int] = None
    timezone: Optional[str] = None

    class Config:
        orm_mode = True


class Message(BaseModel):
    status: str
    mailing_id: int
    client_id: int

    class Config:
        orm_mode = True


class MailingList(BaseModel):
    time_created: Optional[str] = None
    text: Optional[str] = None
    tag: Optional[str] = None
    mob_code: Optional[str] = None
    time_finished: Optional[str] = None

    class Config:
        orm_mode = True


class Msg(BaseModel):
    id: int
    phone: int
    text: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    user_id: int | None = None
    access_token: str

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    username: str | None = None

    class Config:
        orm_mode = True


class Users(BaseModel):
    username: str
    hashed_password: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    role: str | None = None

    class Config:
        orm_mode = True


class UserInDB(Users):
    hashed_password: str

    class Config:
        orm_mode = True
