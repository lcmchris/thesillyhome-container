FROM python:3.10-slim-bullseye

COPY thesillyhome_src /thesillyhome_src


RUN apt-get update && apt-get install -y curl bash
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -

RUN \
    apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    nodejs 

RUN pip3 install -U setuptools && \
    pip3 install -e /thesillyhome_src/thesillyhome/ && \
    pip3 install appdaemon==4.2.1

WORKDIR /thesillyhome_src/frontend
RUN npm install
RUN npm run build

WORKDIR /

ENTRYPOINT [ "bash", "/thesillyhome_src/startup/run.sh" ]
