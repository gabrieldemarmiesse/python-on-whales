FROM busybox as get_buildx

RUN wget -O /docker-buildx https://github.com/docker/buildx/releases/download/v0.4.2/buildx-v0.4.2.linux-amd64
RUN chmod a+x /docker-buildx

#-----------------------------------------------------------------------------
FROM python:3.7 as all_dependencies_except_cli

RUN pip install typeguard pydantic requests tqdm

COPY tests/test-requirements.txt /tmp/
COPY requirements.txt /tmp/
RUN pip install -r /tmp/test-requirements.txt -r /tmp/requirements.txt

COPY --from=get_buildx /docker-buildx /root/.docker/cli-plugins/

#-----------------------------------------------------------------------------
FROM all_dependencies_except_cli as tests_with_cli
COPY --from=docker:19.03 /usr/local/bin/docker /usr/local/bin/
WORKDIR /python-on-whales
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests


#-----------------------------------------------------------------------------
FROM all_dependencies_except_cli as tests_without_cli
WORKDIR /python-on-whales
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests
