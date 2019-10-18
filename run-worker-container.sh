#!/bin/bash

# For dev
docker run --env CELERY_BACKEND=redis://host.docker.internal:6379 --env CELERY_BROKER=redis://host.docker.internal:6379 --network host -it --cap-add=ALL --privileged --rm arrow-celery