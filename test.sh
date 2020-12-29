#!/bin/bash

set -x
set -e
docker build \
    --label openindoor/geojson-api \
    -t openindoor/geojson-api .

docker run \
    -v $(pwd)/test/data:/data \
    -v $(pwd)/test/test.sh:/geojson/test \
    -it openindoor/geojson-api \
    /geojson/test