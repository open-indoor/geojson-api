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
import getopt
import sys

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

def within(geojson_file, bounds_file):
    bounds_gdf = geopandas.read_file(bounds_file)
    geojson_gdf = geopandas.read_file(geojson_file)
    geojson_gdf['openindoor:id'] = bounds_gdf.iloc[0].id
    with open(geojson_file, 'w') as outfile:
        outfile.write(
            geojson_gdf[
                geojson_gdf['geometry'].intersects(
                    bounds_gdf['geometry'][0]
                )
            ].to_json(na='drop')
        )

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
            feature['properties']['feature_id'] = featureId
    with open(geojsonFile, 'w') as outfile:
        json.dump(myGeojson, outfile)
    if (boundsFile != None):
        within(geojsonFile, boundsFile)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "tc:i:", ["test", "country=", "id="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)
    test = False
    place = 'BulgariaHaskovoXackoboGeorgiKirkovStreet'
    country = 'bulgaria'
    for o, a in opts:
        if o in ("-t", "--test"):
            test = True
        elif o in ("-c", "--country"):
            country = a
        elif o in ("-i", "--id"):
            place = a
        else:
            print(o)
            print(a)
            assert False, "unhandled option"
    if test:
        print("test")
        osmFile = '/data/' + country + '/' + place + '.osm'
        geojsonFileTmp = '/data/' + country + '/' + place + '.geojson'
        pipeFile = '/data/' + country + '/' + place + '_bounds.geojson'
        osmToGeojson(place, osmFile, geojsonFileTmp, pipeFile)
        sys.exit()

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


if __name__ == "__main__":
    main()