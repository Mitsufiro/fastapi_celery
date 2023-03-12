import phonenumbers
from fastapi import Depends, HTTPException, APIRouter
from fastapi_sqlalchemy import db
from phonenumbers import geocoder

from crud import get_items
from fast_app import app, RoleChecker, get_current_user
from models import Client as ModelClient
from schemas.schemas import Client as SchemaClient, Users

ROUTER = APIRouter(
    prefix="/client",
    tags=["client"])


