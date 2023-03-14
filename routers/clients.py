import phonenumbers
from fastapi import Depends, HTTPException,APIRouter
from fastapi_sqlalchemy import db
from phonenumbers import geocoder

from crud import get_items, delete_item, get_client_by_tag
from routers.auth import get_current_user, RoleChecker
from models import Client as ModelClient
from schemas.schemas import Client as SchemaClient, Users

ROUTER = APIRouter(
    prefix="/clients",
    tags=["Client"])


@ROUTER.post('/create')
async def post_client(client: SchemaClient):
    phoneNumber = phonenumbers.parse(client.tel_num, 'GB')
    region = geocoder.description_for_number(phoneNumber, 'en')
    region_code = phonenumbers.format_number(phoneNumber, phonenumbers.PhoneNumberFormat.INTERNATIONAL).split()[1]
    db_client = ModelClient(tel_num=client.tel_num, tag=client.tag, mob_code=region_code, timezone=region)
    db.session.add(db_client)
    db.session.commit()
    db.session.refresh(db_client)
    return 'CLIENT SAVED'


@ROUTER.get('/get', dependencies=[Depends(RoleChecker(['admin', 'manager']))])
async def get_client(current_user: Users = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return get_items(ModelClient)


@ROUTER.put('/change')
async def put_client(client_id: int, client: SchemaClient):
    db_client = db.session.query(ModelClient).get(client_id)
    if client.tag != 'string':
        db_client.tag = client.tag
    else:
        db_client.tag = db_client.tag
    if client.tel_num != 'string':
        phoneNumber = phonenumbers.parse(client.tel_num, 'GB')
        region = geocoder.description_for_number(phoneNumber, 'en')
        db_client.tel_num = client.tel_num
        db_client.timezone = region
        new_mob_code = phonenumbers.format_number(phoneNumber, phonenumbers.PhoneNumberFormat.INTERNATIONAL).split()[1]
        db_client.mob_code = int(new_mob_code)
    else:
        db_client.tel_num = db_client.tel_num
    db.session.commit()
    db.session.refresh(db_client)
    return db.session.get(ModelClient, client_id)


@ROUTER.delete('/del')
async def del_client(client_id: int):
    return delete_item(ModelClient, client_id)


@ROUTER.get('/filter')
async def filter_client(client_tag: str):
    client = get_client_by_tag(client_tag)
    if client == []:
        return f'No such clients with tag: {client_tag}'
    else:
        return client
