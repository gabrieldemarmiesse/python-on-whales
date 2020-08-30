FROM busybox as get_docker

WORKDIR /
RUN wget https://download.docker.com/linux/static/stable/x86_64/docker-19.03.9.tgz -O /docker.tgz
RUN tar zxvf /docker.tgz


FROM python:3.7

COPY --from=get_docker /docker/docker /usr/bin/docker
RUN docker --help

RUN pip install typeguard

COPY tests/test-requirements.txt /tmp/

RUN pip install -r /tmp/test-requirements.txt

WORKDIR /docker-cli-wrapper
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests
