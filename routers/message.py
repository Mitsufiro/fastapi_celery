import requests
from fastapi import APIRouter
from crud import get_items
from models import Message as ModelMessage
from schemas.schemas import Msg as SchemaMsg

ROUTER = APIRouter(
    prefix="/message",
    tags=["Message"])

@ROUTER.post('/send_message')
async def send_message(message: str, phone: int, data: SchemaMsg):
    data.text = message
    data.phone = phone
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDE0Mjc4OTEsImlzcyI6ImZhYnJpcXVlIiwibmFtZSI6Im1pdHN1ZmlybyJ9.RG4IhQQi0v1adt5pZPfGZ5GMTjKcsObihpb2j9wcNMQ',
    }
    url = f'https://probe.fbrq.cloud/v1/send/{message}'
    responce = requests.post(url=url, headers=headers, json=data.dict())
    print(type(data))
    return responce.content


@ROUTER.get('/get_message')
async def message():
    return get_items(ModelMessage)
