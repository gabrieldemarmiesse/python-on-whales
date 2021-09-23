FROM python:3.7-slim

RUN pip install redis

RUN apt-get update && apt-get install -y iputils-ping
CMD python -c "print(1); import time; time.sleep(99999)"
