# geojson-api

geojson-api is an OpenIndoor's API, dedicated to convert OpenStreetMap data from osm-api to OSM compliant geojson files.

## Usage

Example:

format: environment / api / action / country / id

status: https://api-sandbox.openindoor.io/geojson/status/france/FranceParisGareDeLEst

trigger: https://api-sandbox.openindoor.io/geojson/trigger/france/FranceParisGareDeLEst

data: https://api-sandbox.openindoor.io/geojson/data/france/FranceParisGareDeLEst.geojson

## Development

```
docker build \
    --label openindoor/geojson-api \
    -t openindoor/geojson-api .

docker run \
    -v $(pwd)/test/data:/data \
    -v $(pwd)/test/test.sh:/geojson/test \
    -it openindoor/geojson-api \
    /geojson/test
```
