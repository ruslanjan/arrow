#!/usr/bin/env bash

#This file executed inside container

cd /app

#python3 app.py
#flask run --host 0.0.0.0
celery -A arrow worker -Q sandbox_execution -l info --concurrency=1