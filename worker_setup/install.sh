#!/bin/sh

cd /app
python3.7 -m pip install -r worker_setup/requirements.txt
mkdir --mod=222 /app/polygon/temp
chmod 222 /app/polygon/temp
chmod -R 666 /app/polygon/payload/usercode
chmod 667 /app/polygon/payload/usercode
