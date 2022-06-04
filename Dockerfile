FROM alpine:3.16

RUN \
    apk add --no-cache --virtual .build-dependencies \
    build-base \
    libffi-dev \
    && apk add --no-cache \
    py3-pip \
    python3-dev \
    py3-numpy \
    py3-pandas \
    py3-scikit-learn \
    mariadb-connector-c-dev \
    && pip3 install thesillyhome==0.2.4 \
    && pip3 install appdaemon==4.2.1 \
    && apk del .build-dependencies

RUN \
    apk add --update nodejs npm

COPY appdaemon /appdaemon
COPY startup /startup
COPY frontend /frontend
COPY thesillyhome /thesillyhome

WORKDIR /frontend
RUN npm install
RUN npm run build

WORKDIR /

ENTRYPOINT [ "echo", 'helloworld' ]
# ENTRYPOINT [ "sh", '/startup/run' ]
