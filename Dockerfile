FROM python:3.6.4-stretch

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

RUN pip install .
