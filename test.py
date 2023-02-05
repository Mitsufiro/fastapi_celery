import pytz

from database import db_context
from models import Client as ModelClient
client_tag = 'Second tag'
mob_code = 999
with db_context() as db:
    clients = db.query(ModelClient).all()
    # filtred_clients = list(map(lambda x: x.mob_code == mob_code, clients))
