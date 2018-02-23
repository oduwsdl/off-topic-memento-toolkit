FROM python:3.6.4-stretch

WORKDIR /app

ADD . /app

RUN python ./setup.py install