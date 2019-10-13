#!/usr/bin/env bash

#This file is for docker

cd /app

#python3 app.py
#flask run --host 0.0.0.0
celery -A arrow worker -Q sandbox_execution -l info --concurrency=1