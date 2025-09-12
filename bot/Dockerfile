FROM python:3.11.4-slim 
 
RUN apt-get update && \ 
  apt-get install -y gcc libpq-dev && \ 
  apt clean && \ 
  rm -rf /var/cache/apt/* 
 
ENV PYTHONDONTWRITEBYTECODE=1 \ 
  PYTHONUNBUFFERED=1 \ 
  PYTHONIOENCODING=utf-8 

COPY /requirements.txt /tmp/requirements.txt 


RUN pip install -U pip && \ 
  pip install -r /tmp/requirements.txt 

COPY ./bot ./src/bot
COPY ./database ./src/database
COPY ./migrations ./src/migrations
COPY ./alembic.ini ./src/


WORKDIR /src

CMD ["python", "-m", "bot"]