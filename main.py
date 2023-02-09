import os
from datetime import datetime
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
from dotenv import load_dotenv
from crud import get_items, get_client_by_tag, get_item, delete_item, filter_of_messages
import requests
from fast_app import Users, get_current_user, RoleChecker


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
async def post_client(tel_num: int, tag: str, mob_code: int, timezone: str, background_task: BackgroundTasks):
    # task = defs_post_client.delay(tel_num, tag, mob_code, timezone)
    db_client = ModelClient(tel_num=tel_num, tag=tag, mob_code=mob_code, timezone=timezone)
    db.session.add(db_client)
    db.session.commit()
    db.session.refresh(db_client)
    # kwargs=[client['tel_num'], client['tag'], client['mob_code'], client['timezone']])
    # print(task)
    # print(tel_num, tag, mob_code, timezone)
    # background_task.add_task(background_on_message, task)
    # print(task)
    return 'CLIENT SAVED'


@app.get('/client/', dependencies=[Depends(RoleChecker(['admin', 'manager']))], tags=['Client'])
async def client(current_user: Users = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return get_items(ModelClient)


@app.put('/client/{client_id}', tags=['Client'])
async def client(client_id: int, tel_num: int | None = Query(default=None),
                 tag: str | None = Query(default=None), mob_code: int | None = Query(default=None),
                 timezone: str | None = Query(default=None)):
    db_client = db.session.query(ModelClient).get(client_id)
    if tag != None:
        db_client.tag = tag
    else:
        db_client.tag = db_client.tag
    if tel_num != None:
        db_client.tel_num = tel_num
    else:
        db_client.tel_num = db_client.tel_num
    if timezone != None:
        db_client.timezone = timezone
    else:
        db_client.timezone = db_client.timezone
    if mob_code != None:
        db_client.mob_code = mob_code
    else:
        db_client.mob_code = db_client.mob_code
    db.session.commit()
    db.session.refresh(db_client)
    return db.session.get(ModelClient, client_id)


@app.delete('/client/', tags=['Client'])
async def client(client_id: int):
    return delete_item(ModelClient, client_id)


@app.get('/filtered_client/', tags=['Client'])
async def client(client_tag: str):
    return get_client_by_tag(client_tag)


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


@app.post('/mailinglist/', response_model=SchemaMailingList, tags=['Mailinglist'])
async def mailinglist(mailinglist: SchemaMailingList):
    db_mailinglist = ModelMailingList(time_created=mailinglist.time_created, text=mailinglist.text, tag=mailinglist.tag,
                                      mob_code=mailinglist.mob_code,
                                      time_finished=mailinglist.time_finished)
    print(datetime.now())
    start_time = datetime.strptime(db_mailinglist.time_created, '%Y %m %d %H:%M')
    db.session.add(db_mailinglist)
    db.session.commit()
    from datetime import timedelta
    three_hours = timedelta(hours=3)
    task = send_message_task.apply_async((db_mailinglist.id,),
                                         eta=datetime(start_time.year, start_time.month, start_time.day,
                                                      start_time.hour,
                                                      start_time.minute) - three_hours)

    print(task.state)
    print(datetime.now())
    return db_mailinglist


@app.get('/mailinglist/', tags=['Mailinglist'])
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
    if tag != None:
        db_mailinglist.text = text
    else:
        db_mailinglist.text = db_mailinglist.text
    if tag != None:
        db_mailinglist.tag = tag
    else:
        db_mailinglist.tag = db_mailinglist.tag
    if mob_code != None:
        db_mailinglist.mob_code = mob_code
    else:
        db_mailinglist.mob_code = db_mailinglist.mob_code
    db.session.commit()
    db.session.refresh(db_mailinglist)
    return get_item(ModelMailingList, mailing_id)


@app.delete('/curren_task')
def delete_task(id: int):
    data = celery_app.control.inspect()
    tasks = dict()
    for i in eval(str(data.scheduled()))['celery@f089dff0e626']:
        tasks[int(*i['request']['args'])] = i['request']['id']
        print(i['request']['id'], *i['request']['args'])
    celery_app.control.revoke(tasks[id], terminate=True, signal='SIGKILL')
    return f"{tasks[id]} revoked"
