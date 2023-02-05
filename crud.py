from models import Client as ModelClient
from fastapi_sqlalchemy import db


def get_client_by_tag(client_tag):
    client = db.session.query(ModelClient).filter(ModelClient.tag == client_tag).all()
    return client


def get_item(model, item_id):
    return db.session.query(ModelClient).get(item_id)


def get_items(model):
    items = db.session.query(model).all()
    return items


def delete_item(model, item_id):
    deleted_item = get_item(model, item_id)
    db.session.delete(get_item(model, item_id))
    db.session.commit()
    return deleted_item
