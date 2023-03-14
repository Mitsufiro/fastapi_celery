from datetime import datetime

from fastapi import Query, APIRouter
from fastapi_sqlalchemy import db

from crud import get_items, filter_of_messages, get_item

from models import MailingList as ModelMailingList, Client as ModelClient, Message as ModelMessage
from schemas.schemas import MailingList as SchemaMailingList
from worker.celery_app import celery_app
from worker.celery_worker import send_message_task

ROUTER = APIRouter(
    prefix="/mailinglist",
    tags=["Mailinglist"])


@ROUTER.post('/create')
async def post_mailinglist(mailing_list: SchemaMailingList):
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


@ROUTER.get('/get')
async def get_mailinglist():
    return get_items(ModelMailingList)


@ROUTER.get('/all_mailinglist_statistics')
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


@ROUTER.get('/one_mailinglist_statistic')
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


@ROUTER.put('/change')
async def change_mailing(mailing_id: int, text: str | None = Query(default=None),
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


@ROUTER.delete('/curren_task')
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
