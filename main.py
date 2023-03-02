import os
from datetime import datetime

import phonenumbers

from fast_app import app
from fastapi import FastAPI, BackgroundTasks, Query, Depends, HTTPException
from worker.celery_worker import defs_post_client, send_message_task
from worker.celery_app import celery_app
from schemas.schemas import Client as SchemaClient
from schemas.schemas import MailingList as SchemaMailingList
from schemas.schemas import Msg as SchemaMsg
from schemas.schemas import Message as SchemaMessage
from models import Client as ModelClient
from models import Msg as ModelMsg
from models import Message as ModelMessage
from models import MailingList as ModelMailingList
from fastapi_sqlalchemy import db
from crud import get_items, get_client_by_tag, get_item, delete_item, filter_of_messages
import requests
from fast_app import Users, get_current_user, RoleChecker
from phonenumbers import geocoder, carrier


def celery_on_message(body):
    print(body)


def background_on_message(task):
    print(task.get(on_message=celery_on_message, propagate=False))


# @app.get("/{word}")
# async def root(word: str, background_task: BackgroundTasks):
#     celery_app.conf.timezone = 'Europe/Moscow'
#     task = celery_app.send_task(
#         "worker.celery_worker.test_celery", args=[word], eta=datetime(2023, 1, 8, 1, 44))
#     print(task)
#     background_task.add_task(background_on_message, task)
#     return {"message": "Word received"}


# @app.post('/clientss', response_model=SchemaClient)
# async def client(client: SchemaClient):
#     db_client = ModelClient(tel_num=client.tel_num, tag=client.tag, timezone=client.timezone, mob_code=client.mob_code)
#     db.session.add(db_client)
#     db.session.commit()
#
#     return db_client


@app.post('/client/', tags=['Client'])
async def post_client(client: SchemaClient):
    phoneNumber = phonenumbers.parse(client.tel_num, 'GB')
    region = geocoder.description_for_number(phoneNumber, 'en')
    region_code = phonenumbers.format_number(phoneNumber, phonenumbers.PhoneNumberFormat.INTERNATIONAL).split()[1]
    db_client = ModelClient(tel_num=client.tel_num, tag=client.tag, mob_code=region_code, timezone=region)
    db.session.add(db_client)
    db.session.commit()
    db.session.refresh(db_client)
    return 'CLIENT SAVED'


@app.get('/client/', dependencies=[Depends(RoleChecker(['admin', 'manager']))], tags=['Client'])
async def client(current_user: Users = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return get_items(ModelClient)


@app.put('/client/{client_id}', tags=['Client'])
async def client(client_id: int, client: SchemaClient):
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
    # if client.timezone != 'string':
    #     db_client.timezone = client.timezone
    # else:
    #     db_client.timezone = db_client.timezone
    # if client.mob_code != 0:
    #     db_client.mob_code = client.mob_code
    # else:
    #     db_client.mob_code = db_client.mob_code
    db.session.commit()
    db.session.refresh(db_client)
    return db.session.get(ModelClient, client_id)


@app.delete('/client/', tags=['Client'])
async def client(client_id: int):
    return delete_item(ModelClient, client_id)


@app.get('/filtered_client/', tags=['Client'])
async def client(client_tag: str):
    client = get_client_by_tag(client_tag)
    if client == []:
        return f'No such clients with tag: {client_tag}'
    else:
        return client


@app.post('/send_message', tags=['Message'])
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


@app.get('/message/', tags=['Message'])
async def message():
    return get_items(ModelMessage)


@app.post('/mailinglist', tags=['Mailinglist'])
async def mailinglist(mailing_list: SchemaMailingList):
    db_mailinglist = ModelMailingList(time_created=mailing_list.time_created, text=mailing_list.text,
                                      tag=mailing_list.tag,
                                      mob_code=mailing_list.mob_code,
                                      time_finished='in process...')
    start_time = mailing_list.time_created
    if db.session.query(ModelClient).filter(ModelClient.tag == mailing_list.tag).all() == []:
        clients = get_items(ModelClient)
        items = []
        for i in clients:
            if i.tag not in items:
                items.append(i.tag)
        return f'No such tag,choose one of this: {items}'
    elif db.session.query(ModelClient).filter(ModelClient.mob_code == mailing_list.mob_code).all() == []:
        clients = get_items(ModelClient)
        items = []
        for i in clients:
            if i.mob_code not in items:
                items.append(i.mob_code)
        return f'No such mob_code,choose one of this: {items}'
    db.session.add(db_mailinglist)
    db.session.commit()
    from datetime import timedelta
    three_hours = timedelta(hours=3)
    task = send_message_task.apply_async((db_mailinglist.id,),
                                         eta=datetime(start_time.year, start_time.month, start_time.day,
                                                      start_time.hour,
                                                      start_time.minute) - three_hours)

    print(task.state)
    return db_mailinglist


@app.get('/mailinglist', tags=['Mailinglist'])
async def mailinglist():
    return get_items(ModelMailingList)


@app.get('/all_mailinglist_statistics', tags=['Mailinglist'])
async def get_all_stats():
    mailing_lists = get_items(ModelMailingList)
    stats = []
    for i in mailing_lists:
        messages_sent = filter_of_messages(i.id, 'sent')
        messages_unsent = filter_of_messages(i.id, 'unsent')
        messages_in_process = filter_of_messages(i.id, 'in process...')
        stats.append(
            {f'id_of_mailinglist: {i.id}': {'mob_code': i.mob_code, 'tag': i.tag,
                                            'sent_messages': messages_sent.count(),
                                            'unsent_messages': messages_unsent.count(),
                                            'messages_in_process': messages_in_process.count()}})

    return stats


@app.get('/one_mailinglist_statistic', tags=['Mailinglist'])
async def one_mailinglist_stats(id: int):
    if not get_item(ModelMailingList, id):
        return f'No such id of mailing as: {id}, try correct id'
    messages = db.session.query(ModelMessage).filter(ModelMessage.mailing_id == id).all()
    messages_sent = filter_of_messages(id, 'sent')
    messages_unsent = filter_of_messages(id, 'unsent')
    messages_in_process = filter_of_messages(id, 'in process...')
    mailinglist = get_item(ModelMailingList, id)
    messages.insert(0,
                    {f'id_of_mailinglist: {id}': {'mob_code': mailinglist.mob_code, 'tag': mailinglist.tag,
                                                  'sent_messages': messages_sent.count(),
                                                  'unsent_messages': messages_unsent.count(),
                                                  'messages_in_process': messages_in_process.count()}})
    return messages


@app.put('/mailinglist', tags=['Mailinglist'])
async def client(mailing_id: int, text: str | None = Query(default=None),
                 tag: str | None = Query(default=None), mob_code: int | None = Query(default=None)):
    db_mailinglist = get_item(ModelMailingList, mailing_id)
    if text != None:
        db_mailinglist.text = text
    else:
        db_mailinglist.text = db_mailinglist.text
    if tag != None:
        if db.session.query(ModelClient).filter(ModelClient.tag == tag).all() == []:
            clients = get_items(ModelClient)
            items = []
            for i in clients:
                if i.tag not in items:
                    items.append(i.tag)
            return f'No such tag,choose one of this: {items}'
        db_mailinglist.tag = tag
    else:
        db_mailinglist.tag = db_mailinglist.tag
    if mob_code != None:
        if db.session.query(ModelClient).filter(ModelClient.mob_code == mob_code).all() == []:
            clients = get_items(ModelClient)
            items = []
            for i in clients:
                if i.mob_code not in items:
                    items.append(i.mob_code)
            return f'No such mob_code,choose one of this: {items}'
        db_mailinglist.mob_code = mob_code
    else:
        db_mailinglist.mob_code = db_mailinglist.mob_code
    db.session.commit()
    db.session.refresh(db_mailinglist)
    return get_item(ModelMailingList, mailing_id)


@app.delete('/curren_task')
def delete_task(id: int):
    if not get_item(ModelMailingList, id):
        return f'No such mailing with id: {id}'
    data = celery_app.control.inspect()
    tasks = dict()
    for i in list(eval(str(data.scheduled())).values())[0]:
        tasks[int(*i['request']['args'])] = i['request']['id']
        print(i['request']['id'], *i['request']['args'])
    celery_app.control.revoke(tasks[id], terminate=True, signal='SIGKILL')
    db_mailinglist = get_item(ModelMailingList, id)
    db_mailinglist.time_finished = 'REVOKED'
    db.session.commit()
    db.session.refresh(db_mailinglist)
    return f"Task with ID: {tasks[id]} REVOKED"
