import datetime

import pytz as pytz
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv('.env')
celery_app = Celery(
    "worker",
    backend="db+postgresql+psycopg2://postgres:1488@localhost/goo_sheets",
    broker="pyamqp://guest:guest@localhost//"
)

celery_app.conf.task_routes = {
    'worker.celery_worker.defs_post_client': 'test-queue',
    'worker.celery_worker.send_message_task': 'test-queue'
}
celery_app.conf.update(task_track_started=True)
# celery_app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': 'worker.celery_worker.def_hello',
#         'schedule': crontab(month_of_year=1, day_of_month=7, hour=22,
#                             minute=40),
#     },
# }
celery_app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'worker.celery_worker.def_hello',
        'schedule': crontab(month_of_year=1, day_of_month=8, hour=17, minute=13),
    },
}

celery_app.conf.timezone = 'Europe/Moscow'
celery_app.timezone.fromutc(datetime.datetime.now())

# def celery_localtime_util(t):
#     bj_tz = pytz.timezone('Europe/Moscow')
#     bj_dt = bj_tz.localize(t)
#     return bj_dt.astimezone(pytz.UTC)


# celery_localtime_util(datetime.datetime.now())

# london_tz = pytz.timezone('Europe/Moscow')
# london_dt = london_tz.localize(datetime.datetime.now())
# give_this_to_celery = london_dt.astimezone(pytz.UTC)
# enable_utc = False
celery_app.autodiscover_tasks()
