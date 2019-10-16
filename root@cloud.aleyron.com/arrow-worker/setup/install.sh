#!/bin/sh

cd /app
pip3 install -r requirements.txt
mkdir --mod=222 /app/polygon/temp
chmod 222 /app/polygon/temp
chmod -R 666 /app/polygon/payload/usercode
chmod 667 /app/polygon/payload/usercode
