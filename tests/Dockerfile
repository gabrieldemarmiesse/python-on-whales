FROM busybox as get_docker

WORKDIR /
RUN wget https://download.docker.com/linux/static/stable/x86_64/docker-19.03.9.tgz -O /docker.tgz
RUN tar zxvf /docker.tgz

#-----------------------------------------------------------------------------
FROM busybox as get_buildx

RUN wget -O /docker-buildx https://github.com/docker/buildx/releases/download/v0.4.2/buildx-v0.4.2.linux-amd64
RUN chmod a+x /docker-buildx

#-----------------------------------------------------------------------------
FROM python:3.7

RUN pip install typeguard pydantic requests tqdm

COPY tests/test-requirements.txt /tmp/
RUN pip install -r /tmp/test-requirements.txt

COPY --from=get_docker /docker/docker /usr/bin/docker
RUN docker --help
COPY --from=get_buildx /docker-buildx /root/.docker/cli-plugins/
RUN docker buildx build --help

WORKDIR /docker-cli-wrapper
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests
