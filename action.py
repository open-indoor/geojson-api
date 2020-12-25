#!/usr/bin/python3

import os
import uuid
import pycurl
import codecs
import re
import json
import geopandas
import io
from shapely.geometry import shape
import geojson

myUuid = str(uuid.uuid4())

def getChecksum(country, place):
    buffer = io.BytesIO()
    url = 'http://osm-api/osm/' + country + '/' + place + '.cksum'
    print('downloading: ' + url)
    crl = pycurl.Curl()
    crl.setopt(crl.URL, url)
    crl.setopt(crl.WRITEDATA, buffer)
    crl.perform()
    if (crl.getinfo(pycurl.HTTP_CODE) >= 400):
        return None
    crl.close()
    body = buffer.getvalue()
    print('downloaded: ' + url)
    result = body.decode('utf-8').rstrip('\n')
    return result

def getOsm(country, place, myUuid):
    osmFileTmp = '/tmp/osm/' + country + '/' + place + '_' + myUuid + '.osm'
    os.makedirs(os.path.dirname(osmFileTmp), exist_ok=True)
    with open(osmFileTmp, 'wb') as file:
        url = 'http://osm-api/osm/' + country + '/' + place + '.osm'
        # print('downloading: ' + url)
        crl = pycurl.Curl()
        crl.setopt(crl.URL, url)
        crl.setopt(crl.WRITEDATA, file)
        crl.perform()
        if (crl.getinfo(pycurl.HTTP_CODE) >= 400):
            return None
        crl.close()
        print('downloaded: ' + url + ' to ' + osmFileTmp)
    osmFile = '/tmp/osm/' + country + '/' + place + '_' + str(getChecksum(country, place)) + '.osm'
    os.makedirs(os.path.dirname(osmFile), exist_ok=True)
    print('osmFileTmp: ' + osmFileTmp)
    os.rename(osmFileTmp, osmFile)
    print('osmFile: ' + osmFile)
    return osmFile

def intersects_02(geojsonFile, boundsFile):
    geojsonGpd = geopandas.read_file(geojsonFile)
    print('geojson to clip: ' + geojsonFile)
    print(geojsonGpd)
    boundsGpd = geopandas.read_file(boundsFile)
    # boundsGpd = boundsGpd.buffer(100)
    print('boundingFile: ' + boundsFile)
    print(boundsGpd)
    # geojsonFilteredGpd = geopandas.clip(geojsonGpd, boundsGpd, keep_geom_type=True)
    # geojsonFilteredGpd = geopandas.overlay(geojsonGpd, boundsGpd, how='intersection')
    geojsonFilteredGpd = geopandas.overlay(boundsGpd, geojsonGpd, how='intersection')
    geojsonFilteredGpd.to_file(geojsonGpd, driver='GeoJSON')

def intersects_01(geojsonFile, boundsFile):
    print('File to clean up:' + geojsonFile + ' with ' + boundsFile)
    with open(geojsonFile) as json_file:
        placeJson = json.load(json_file)
    with open(boundsFile) as json_file:
        boundsGeojson = json.load(json_file)
    if len(boundsGeojson['features']) == 0:
        print('no bounds detected')
        return
    boundsJson = boundsGeojson['features'][0]['geometry']
    boundsShp = shape(boundsJson)
    cleanPlace = {
            "type": "FeatureCollection",
        "generator": "JOSM",
        "features":  []
    }
    for feature in placeJson['features']:
        # print('feature to add:' + json.dumps(feature))
        gj = geojson.Feature(feature)
        gj.errors()
        # print('feature validated')

        featureShp = shape(feature['geometry'])
        try:
            if boundsShp.intersects(featureShp):
                cleanPlace['features'].append(feature)
        except Exception:
            pass  # or you could use 'continue'
    print('Going to write clean file')
    with open(geojsonFile, 'w') as outfile:
        json.dump(cleanPlace, outfile)
    

def osmToGeojson(placeId, osmFile, geojsonFile, boundsFile = None):
    cmd = ('osmtogeojson -m ' + osmFile + ' > ' + geojsonFile)
    print('start cmd: ' + cmd)
    os.system(cmd)
    print('cmd done.')
    print('alter geojson: ' + geojsonFile)
    with open(geojsonFile) as json_file:
        myGeojson = json.load(json_file)
        # filter on id field
        # myGeojson['features'] = dict(filter(lambda feature: 'id' in feature, myGeojson['features'].items()))

        myGeojson['features'] = [feature for feature in myGeojson['features'] if 'id' in feature]

        regMulti = re.compile(r'^(-?\d+\.?\d*).*;(-?\d+\.?\d*)$')
        regMinus = re.compile(r'^(-?\d+\.?\d*)-(-?\d+\.?\d*)$')
        for feature in myGeojson['features']:
            # del feature['id']
#            if ((not 'id' in feature) or (not feature['id'])):
            if (('properties' in feature) and ('level' in feature['properties'])):
                level = feature['properties']['level']
                level = level.replace('--', '-')
                level = level.replace(':', ';')
                level = regMulti.sub(r'\1;\2', level)
                level = regMinus.sub(r'\1;\2', level)
                if (regMulti.match(level)):
                    num1 = float(regMulti.sub(r'\1', level))
                    num2 = float(regMulti.sub(r'\2', level))
                    if (num1 > num2):
                        level = regMulti.sub(r'\2;\1', level)
                feature['properties']['level'] = level
            # feature['place'] = placeId
            featureId = (uuid.uuid4().int % (2**32))
            feature['id'] = featureId
            if (not 'properties' in feature):
                feature['properties'] = {}
            feature['properties']['openindoor:id'] = placeId
            feature['properties']['feature_id'] = featureId
    with open(geojsonFile, 'w') as outfile:
        json.dump(myGeojson, outfile)
    if (boundsFile != None):
        intersects_01(geojsonFile, boundsFile)
        # intersects_02(geojsonFile, boundsFile)
        # geojsonGpd = geopandas.read_file(geojsonFile)
        # print('geojson to clip: ' + geojsonFile)
        # print(geojsonGpd)
        # boundsGpd = geopandas.read_file(boundsFile)
        # boundsGpd = boundsGpd.buffer(100)
        # print('boundingFile: ' + boundsFile)
        # print(boundsGpd)
        # geojsonFilteredGpd = geopandas.clip(geojsonGpd, boundsGpd, keep_geom_type=True)
        # geojsonFilteredGpd.to_file(geojsonGpd, driver='GeoJSON')



    # shapely.geometry.Polygon

    # print(json.dumps(geojson))
    # geojsonIo = io.StringIO(json.dumps(geojson))
    # print('geopandasize...')
    # place = geopandas.read_file(geojsonIo)
    # print('geopandasizes !')
    # file = open(placeFile)
    # bounds = geopandas.read_file(file)
    # selection = geopandas.clip(place, bounds, True)
    # print(selection.to_json(na='drop'))
    # print(place.to_json(na='drop'))

pipeDir = '/tmp/geojsonPipe'
os.makedirs(pipeDir, exist_ok=True)
for country in os.listdir(pipeDir):
    print('country: ' + country)
    for boundsFile in os.listdir('/tmp/geojsonPipe/' + country):
        pipeFile = '/tmp/geojsonPipe/' + country + '/' + boundsFile
        print('boundsFile: ' + boundsFile)
        if not boundsFile.endswith("_bounds.geojson"):
            continue
        # Get bounds
        place = re.sub('_bounds\.geojson$', '', boundsFile)
        print('place: ' + place)
        cksum = getChecksum(country, place)
        if cksum == None:
            continue
        print('cksum: ' + cksum)
        geojsonFile = '/tmp/geojson/' + country + '/' + place + '_' + cksum + '.geojson'
        if os.path.isfile(geojsonFile):
            os.remove(pipeFile)
            continue
        # Create geojson
        osmFile = getOsm(country, place, myUuid)
        if osmFile == None:
            continue

        print('osmFile: ' + str(osmFile))
        geojsonFileTmp = '/tmp/geojson/' + country + '/' + place + '_' + myUuid + '.geojson'
        print('geojsonFileTmp: ' + geojsonFileTmp)
        # mkdir basename geojsonFile
        os.makedirs(os.path.dirname(geojsonFile), exist_ok=True)
        osmToGeojson(place, osmFile, geojsonFileTmp, pipeFile)
        os.remove(pipeFile)
        os.rename(geojsonFileTmp, geojsonFile)
        print('geojsonFile: ' + geojsonFile)
        dst = '/tmp/geojson/' + country + '/' + place + '.geojson'
        dst2 = '/tmp/geojson/' + country + '/' + place
        if os.path.exists(dst):
            os.remove(dst)
        if os.path.exists(dst2):
            os.remove(dst2)
        os.symlink(geojsonFile, dst) 
        os.symlink(geojsonFile, dst2)
        print('dst: ' + dst)
        print('dst2: ' + dst2)
