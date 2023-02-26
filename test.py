import phonenumbers
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    format_number,
    is_valid_number,
    number_type,
    parse as parse_phone_number,
)
from phonenumbers import geocoder, carrier
from pydantic import BaseModel, EmailStr, constr, validator

MOBILE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE
# Parsing String to Phone number
from typing import Optional


# return format_number(n, PhoneNumberFormat.NATIONAL if n.country_code == 44 else PhoneNumberFormat.INTERNATIONAL)
phoneNumber = phonenumbers.parse('+447986123456','GB')
# Getting carrier of a phone number
Carrier = carrier.name_for_number(phoneNumber, 'ru')
print(phonenumbers.is_valid_number(phoneNumber))
Region = geocoder.description_for_number(phoneNumber, 'en')
international_f = phonenumbers.format_number(phoneNumber, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
print(international_f.split()[1])
print(number_type(phoneNumber),123)
# print(Carrier)
print(Region)
# if len(Carrier) == 0:
#     print('Такого мобильного оператора нет')
# else:
#     print(Carrier)


# class Client(BaseModel):
#     tel_num: str
#     tag: Optional[str] = None
#     mob_code: Optional[int] = None
#     timezone: Optional[str] = None
#
#     @validator('mob_code')
#     def check_mob_code(cls, v):
#         if len(str(v)) != 3 and len(str(v)) != 4:
#             print(len(str(v)))
#             raise ValueError('Такого мобильного оператора нет')
#         else:
#             print(len(str(v)))
#             return v
#
#
#
# print(Client(mob_code=4434, tel_num='234234'))
