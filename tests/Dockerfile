FROM busybox as get_buildx

RUN wget -O /docker-buildx https://github.com/docker/buildx/releases/download/v0.4.2/buildx-v0.4.2.linux-amd64
RUN chmod a+x /docker-buildx

#-----------------------------------------------------------------------------
FROM python:3.7 as python_dependencies

RUN pip install typeguard pydantic requests tqdm

COPY tests/test-requirements.txt /tmp/
COPY requirements.txt /tmp/
RUN pip install -r /tmp/test-requirements.txt -r /tmp/requirements.txt


#-----------------------------------------------------------------------------
FROM python_dependencies as lint
WORKDIR /python-on-whales
COPY . .
RUN flake8
RUN isort --check
RUN black --check

#-----------------------------------------------------------------------------
FROM python_dependencies as tests_with_binaries
COPY --from=docker:19.03 /usr/local/bin/docker /usr/local/bin/
COPY --from=get_buildx /docker-buildx /root/.docker/cli-plugins/
WORKDIR /python-on-whales
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests


#-----------------------------------------------------------------------------
FROM python_dependencies as tests_without_any_binary
WORKDIR /python-on-whales
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests/python_on_whales/components/test_buildx.py


#-----------------------------------------------------------------------------
FROM python_dependencies as tests_ubuntu_install_without_buildx

RUN apt-get update && \
    apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      gnupg-agent \
      software-properties-common
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
RUN  apt-get update && \
     apt-get install -y docker-ce-cli

WORKDIR /python-on-whales
COPY . .

RUN pip install -e .

CMD pytest -v --durations=10 ./tests/python_on_whales/components/test_buildx.py
