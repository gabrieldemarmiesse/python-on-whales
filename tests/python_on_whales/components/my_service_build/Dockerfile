FROM python:3.8-slim

RUN pip install redis

RUN apt-get update && apt-get install -y iputils-ping
CMD python -u -c "print(1); import time; time.sleep(99999)"
