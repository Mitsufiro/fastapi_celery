RUN alembic revision --autogenerate -m "New Migration"
RUN alembic upgrade head
