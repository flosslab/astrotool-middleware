FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04 AS base
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/data
RUN apt update \
    && apt -y dist-upgrade \
    && rm -R /var/lib/apt/*
RUN groupadd -g 1000 user \
    && useradd --home-dir=/data --gid=1000 --no-create-home --shell=/bin/bash --uid=1000 user \
    && mkdir /data \
    && chown 1000:1000 /data

FROM base AS base-build
RUN apt update \
    && apt -y dist-upgrade \
    && apt -y install build-essential automake autoconf libtool pkg-config cmake \
    && rm -R /var/lib/apt/*

FROM base-build AS python-build
RUN apt update \
    && apt -y install libssl1.1 libexpat1 libreadline8 libncurses6 libncursesw6 libbz2-1.0 libsqlite3-0 zlib1g libffi7 liblzma5 libuuid1 \
        libssl-dev libexpat1-dev libreadline-dev libncurses-dev libbz2-dev libsqlite3-dev zlib1g-dev libffi-dev liblzma-dev uuid-dev \
        wget xz-utils \
    && rm -R /var/lib/apt/*
RUN mkdir /build \
    && cd /build \
    && wget "https://www.python.org/ftp/python/3.12.11/Python-3.12.11.tar.xz" \
    && tar xf Python-3.12.11.tar.xz \
    && cd Python-3.12.11 \
    && ./configure \
      --prefix=/opt/python-3.12.11 \
      --enable-optimizations \
      --enable-ipv6 \
      --with-system-expat \
      --with-openssl=/usr \
      --with-ensurepip=install \
    && make -j$(nproc) \
    && make install

FROM base AS venv
COPY --from=python-build /opt/python-3.12.11 /opt/python-3.12.11
RUN apt update \
    && apt -y dist-upgrade \
    && apt -y install build-essential automake autoconf libtool pkg-config cmake \
    && rm -R /var/lib/apt/*
RUN mkdir /project
COPY pyproject.toml /project/pyproject.toml
COPY poetry.lock /project/poetry.lock
RUN /opt/python-3.12.11/bin/python3 -m venv /venv \
    && . /venv/bin/activate \
    && python3 -m pip install --upgrade pip setuptools wheel poetry \
    && poetry install --project=/project --no-root

FROM base AS ready
COPY --from=venv /venv /venv

FROM ready AS dev
COPY pyproject.toml /project/pyproject.toml
COPY poetry.lock /project/poetry.lock
ENV MAKEFLAGS=-j6
#WORKDIR /project
#RUN . /venv/bin/activate \
#    && python3 -m pip install poetry \
#    && poetry install --no-root

FROM dev AS test
COPY src /project/src
COPY test /project/test
WORKDIR /project/test
ENTRYPOINT ["/venv/bin/python3", "-m", "pytest"]

FROM dev AS build
COPY . /project
WORKDIR /project
RUN . /venv/bin/activate \
    && poetry build


FROM venv AS prod
COPY --from=build /project/dist/*.whl /
COPY docker/entrypoint.sh /entrypoint.sh
RUN . /venv/bin/activate \
    && python3 -m pip install /*.whl
EXPOSE 8008
WORKDIR /data
VOLUME /data
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]





























FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    libxrender1 \
    libgl1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://pyenv.run | bash

ENV PATH="/root/.pyenv/bin:$PATH"
ENV PYENV_ROOT="/root/.pyenv"

RUN eval "$(pyenv init -)" && \
    pyenv install 3.12.7 && \
    pyenv global 3.12.7

RUN eval "$(pyenv init -)" && \
    python -m venv /root/venv && \
    /root/venv/bin/pip install --upgrade pip

ENV PATH="/root/venv/bin:$PATH"
ENV VIRTUAL_ENV="/root/venv"

WORKDIR /middleware

COPY . /middleware

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "middleware.py", "--host", "0.0.0.0", "--port", "1234"]
