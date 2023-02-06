import datetime
from time import sleep
from celery import current_task
import requests
from models import Client as ModelClient
from models import Message as ModelMessage
from models import MailingList as ModelMailingList
from .celery_app import celery_app
from database import db_context


# @celery_app.task(acks_late=True)
# def test_celery(word: str) -> str:
#     for i in range(1, 11):
#         sleep(1)
#         current_task.update_state(state='PROGRESS',
#                                   meta={'process_percent': i * 10})
#     return f"test task return {word}"


# def client(client: SchemaClient):
#     db_client = ModelClient(tel_num=client.tel_num, tag=client.tag, timezone=client.timezone, mob_code=client.mob_code)
#     db.session.add(db_client)
#     db.session.commit()
#
#     return db_client
# @celery_app.task(acks_late=True)
# def def_hello(word: str, my_word: str):
#     print('hello')
#     return word, my_word


@celery_app.task(acks_late=True, bind=True)
def defs_post_client(self, tel_num: int, tag: str, mob_code: int, timezone: str):
    db_client = ModelClient(tel_num=tel_num, tag=tag, mob_code=mob_code, timezone=timezone)
    with db_context() as db:
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
    # current_task.update_state(state='PROGRESS',
    #                           meta={'process_precent': 0})
    # current_task.update_state(state='PROGRESS',
    #                           meta={'process_percent': client})
    # x = db.session.query(ModelClient).all()
    return 'CLIENT SAVED'
    # return db.session.query(ModelClient).all()


@celery_app.task(acks_late=True, retry_policy={
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2, })
def send_message_task(text_message: str, client_tag: str, mob_code: str, mailing_id: int):
    with db_context() as db:
        clients = db.query(ModelClient).filter(ModelClient.tag == client_tag).filter(
            ModelClient.mob_code == mob_code).all()
        # filtred_clients = list(map(lambda x: x.mob_code == mob_code, clients))
        # print(filtred_clients)
        for client in clients:
            db_message = ModelMessage(status='sent', mailing_id=mailing_id,
                                      client_id=client.id,
                                      time_created=str(datetime.datetime.now().strftime('%Y %m %d %X')))
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            data = {'id': db_message.id,
                    'phone': client.id,
                    'text': text_message}
            headers = {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDE0Mjc4OTEsImlzcyI6ImZhYnJpcXVlIiwibmFtZSI6Im1pdHN1ZmlybyJ9.RG4IhQQi0v1adt5pZPfGZ5GMTjKcsObihpb2j9wcNMQ',
            }
            url = f'https://probe.fbrq.cloud/v1/send/{db_message.id}'
            responce = requests.post(url=url, headers=headers, json=data)
            print(client.tag, client.mob_code)
            print(responce.content, responce.status_code)
    mailinglist = db.query(ModelMailingList).filter(ModelMailingList.id == mailing_id).first()
    mailinglist.time_finished = str(datetime.datetime.now().strftime('%Y %m %d %X'))
    db.commit()
    db.refresh(mailinglist)
    print(mailinglist.id)
    return responce.content, text_message, client_tag, mob_code
