from typing import Optional
from phonenumbers import NumberParseException, PhoneNumberFormat, PhoneNumberType, format_number, is_valid_number, \
    number_type, parse as parse_phone_number
import phonenumbers
from crud import get_client_by_tag
from pydantic import BaseModel, ValidationError, EmailStr, constr, validator
from phonenumbers import geocoder, carrier
from datetime import datetime

MOBILE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE


class Client(BaseModel):
    tel_num: Optional[str] = None
    tag: Optional[str] = None

    # mob_code: Optional[int] = None
    # timezone: Optional[str] = None

    @validator('tel_num')
    def check_phone_number(cls, v):
        if v == 'string':
            return v
        try:
            n = parse_phone_number(v, 'GB')
        except NumberParseException as e:
            raise ValueError('Пожалуйста проверьте правильность ввода номера телефона') from e

        if not is_valid_number(n) or number_type(n) not in MOBILE_NUMBER_TYPES:
            print(v)
            raise ValueError('Пожалуйста проверьте правильность ввода номера телефона')

        return format_number(n, PhoneNumberFormat.NATIONAL if n.country_code == 44 else PhoneNumberFormat.INTERNATIONAL)

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

    # time_finished: Optional[str] = None

    @validator('time_created')
    def check_time_created(cls, v):
        try:
            v = datetime.strptime(v, '%Y %m %d %H:%M')
        except AttributeError as e:
            raise ValueError('Введите дату и время в формате: 2023 02 15 01:28') from e
        return v

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
