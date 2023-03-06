FROM python:3.10-slim


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1

WORKDIR /fastapi_celery

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY ./traefik.prod.toml ./etc/traefik/traefik.toml
COPY . .

EXPOSE 8000
EXPOSE 5555
EXPOSE 5433
EXPOSE 4360
EXPOSE 5672
EXPOSE 25672
EXPOSE 15672


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]