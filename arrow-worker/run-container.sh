#!/bin/bash

docker run -p 127.0.0.1:5000:5000 --env CELERY_BACKEND=redis://:yourpassword@redis:6379 --env CELERY_BROKER=redis://:yourpassword@redis:6379 --network host -it --cap-add=ALL --privileged --rm arrow-celery