################ OSM TO GEOJSON #####################
FROM debian:testing

RUN apt-get -qq update \
  && DEBIAN_FRONTEND=noninteractive \
  apt-get -y install --no-install-recommends \
    ca-certificates \
  && apt-get clean

RUN echo "deb [trusted=yes] https://apt.fury.io/caddy/ /" \
    | tee -a /etc/apt/sources.list.d/caddy-fury.list
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get -y install \
      --no-install-recommends \
      bash \
      caddy \
      cron \
      curl \
      fcgiwrap \
      file \
      gettext \
      git \
      grep \
      htop \
      jq \
      less \
      net-tools \
      npm nodejs \
      procps \
      python3-geopandas \
      python3-geojson \
      python3-pycurl \
      python3-pip \
      unzip \
      util-linux \
      uuid-runtime \
      vim \
      wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g osmtogeojson

COPY ./requirements.txt /geojson/
RUN pip3 install -v -r /geojson/requirements.txt

COPY ./Caddyfile /etc/caddy/Caddyfile

RUN mkdir -p /geojson

WORKDIR /geojson

ENV API_DOMAIN_NAME api.openindoor.io

CMD ["/geojson/geojson-api.sh"]

COPY ./geojson-api.sh /geojson/geojson-api.sh
COPY ./geojson.py /geojson/geojson
COPY ./action.py /usr/bin/action
RUN chmod +x /geojson/geojson-api.sh
COPY ./tic.sh /usr/bin/tic

EXPOSE 80