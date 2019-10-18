FROM python:3
ENV PYTHONUNBUFFERED 1

RUN apt -y install libz-dev libjpeg-dev libfreetype6-dev python-dev

RUN mkdir /code
WORKDIR /code
COPY setup/requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/