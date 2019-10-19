FROM python:3.7
ENV PYTHONUNBUFFERED 1

RUN apt -y update
RUN apt -y upgrade
RUN apt -y install libz-dev libjpeg-dev libfreetype6-dev python-dev

RUN mkdir /code
WORKDIR /code
#COPY ./setup/requirements.txt /code/
COPY . /code/
RUN python3.7 -m pip install -r requirements.txt
