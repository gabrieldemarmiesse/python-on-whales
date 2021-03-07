# doesn't work anymore, should fix.

FROM python:3.7 as make-sources

COPY requirements.txt /
RUN pip install keras-autodoc -r /requirements.txt

WORKDIR /python-on-whales
COPY . .
RUN pip install -e .

RUN cd docs && python autogen.py


FROM scratch

COPY --from=make-sources /python-on-whales/docs/generated_sources /
