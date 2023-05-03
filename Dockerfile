FROM python:3.9-slim-bullseye AS compile-image

RUN apt-get update && apt-get install -y curl bash && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    nodejs \
    gfortran \
    nano

ARG PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple

COPY thesillyhome_src /thesillyhome_src

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install --upgrade pip && \
    pip3 install setuptools==62.4.0 && \
    pip3 install -e /thesillyhome_src/thesillyhome/ && \
    pip3 install appdaemon==4.2.1 

WORKDIR /thesillyhome_src/frontend
RUN npm install && npm run build

FROM python:3.9-slim-bullseye AS build-image

RUN apt-get update && apt-get install -y curl bash && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y libpq-dev nodejs cron

COPY --from=compile-image /opt/venv /opt/venv
COPY --from=compile-image /thesillyhome_src /thesillyhome_src


ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /

ENTRYPOINT [ "bash", "/thesillyhome_src/startup/run.sh" ]

