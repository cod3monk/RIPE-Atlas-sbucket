#!/usr/bin/env python3
'''
Spatial Bucketing of RIPE Atlas Probes on Map Projections

Author: Julian Hammer <julian.hammer@u-sys.org>
License: AGPLv3
'''
import sys
import json
import argparse
import random
import urllib.request

import pyproj


def getProbes(probes, online=True, country_codes=None):
    selected_probes = []
    for p in probes:
        # Filtering probes
        if online and p['status']['id'] != 1:
            continue
        if country_codes and p['country_code'] not in country_codes:
            continue
        if not p['geometry'] or not p['geometry']['coordinates']:
            continue

        # Coordinates are in GeoJSON format: longitude, latitude.
        selected_probes.append({
            'id': p['id'],
            'longitude': p['geometry']['coordinates'][0],
            'latitude': p['geometry']['coordinates'][1]})

    return selected_probes


def bucketing(probes, target_count, projection='merc', max_iter=100):
    # Convert 3D to 2D coordinates using given map projection.
    # This is not the recommended way to transform coordinates with pyproj,
    # but works for our simple use case where we don't care about datum shifts.
    p_dst = pyproj.Proj(proj=projection)

    for p in probes:
        try:
            p['proj'] = p_dst(float(p['longitude']), float(p['latitude']))
        except:
            # ignore probes with bad long/lat information
            pass

    min_dst = p_dst(-180, -85.)
    max_dst = p_dst(180, 85.)

    # Initial cell counts
    bucket_counts = (10, 20)  # vertical and horizontal
    buckets = {}

    # 5% acceptable deviation
    while abs(len(buckets)-target_count) > 0.05*target_count and not max_iter <= 0:
        if len(buckets) < target_count:
            bucket_counts = bucket_counts[0]*1.5, bucket_counts[1]*1.5
        else:
            bucket_counts = bucket_counts[0]*0.9, bucket_counts[1]*0.9

        div = ((max_dst[0]-min_dst[0])/bucket_counts[0],
               (max_dst[1]-min_dst[1])/bucket_counts[1])

        buckets = {}
        for p in probes:
            if not 'proj' in p:
                continue

            key = (int(p['proj'][0]/div[0]), int(p['proj'][1]/div[1]))
            if key not in buckets:
                buckets[key] = [p['id']]
            else:
                buckets[key].append(p['id'])

        max_iter -= 1

    return buckets


def random_selection(buckets):
    for b in buckets.values():
        yield random.choice(b)


def main():
    parser = argparse.ArgumentParser(description='Spatial bucketing of RIPE Atlas probes.')
    parser.add_argument('--data', '-d', type=argparse.FileType('r'), required=False, help='dump of probe metadata '
        '(from https://atlas.ripe.net/api/v2/probes/?format=json&status=1&fields='
        'id,status,country_code,geometry) ,if not given data is retrieved from atlas.ripe.net')
    parser.add_argument('--projection', '-p', default='merc', help='projection to use for spatial '
        'distribution, has to be supported by pyproj (default: merc)')
    parser.add_argument('count', type=int, help='number of probes to be returned')
    parser.add_argument('--maxiter', '-m', type=int, default=100, help='maximum number of '
        'iterations to be performed (default: 100)')
    parser.add_argument('--country', '-c', action='append', help='Allowed countries. If not set: '
        'world-wide.')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    args = parser.parse_args()

    probes = []
    if args.data:
        f = args.data
        probes = json.load(f)['results']
    else:
        # Load json from RIPE API and follow next urls
        next_url = ('https://atlas.ripe.net/api/v2/probes/?format=json&status=1&'
                    'fields=id,status,country_code,geometry&page_size=500')
        while next_url:
            if args.verbose >= 2:
                print("loading {}".format(next_url))
            f = urllib.request.urlopen(next_url)
            result = json.load(f)
            probes += result['results']
            next_url = result['next']
        # DEBUG: Save downloaded probes list for later runs.  Maybe should be command-line option.
        #with open("probes.json", "w") as outfile:
        #    outfile.write('{"results": [\n' + ',\n'.join([json.dumps(p) for p in probes]) + "\n]}")
    if args.verbose >= 1:
        print("received {} raw entries.".format(len(probes)))
    probes = getProbes(probes, country_codes=args.country)
    if args.verbose >= 1:
        print("received {} probes.".format(len(probes)))

    buckets = bucketing(probes, args.count, projection=args.projection, max_iter=args.maxiter)
    probes = list(random_selection(buckets))

    if args.verbose >= 1:
        print("selected {} probes:".format(len(probes)))

    print(probes)

    if args.verbose >= 1:
        print('count:', len(probes))

    if args.verbose >= 2:
        print()
        print('example measurement creation:')
        print('curl --dump-header - -H "Content-Type: application/json" -H "Accept: application/json" -X POST -d', "'"+json.dumps({
            "definitions": [{
                "target": "fablab.fau.de",
                "af": 4,
                "packets": 3,
                "size": 48,
                "description": "Ping measurement to fablab.fau.de",
                "interval": 240,
                "resolve_on_probe": False,
                "type": "ping"}],
            "probes": [{
                "value": ",".join(map(str, probes)),
                "type": "probes",
                "requested": len(probes)}],
            "is_oneoff": True})+"'", "https://atlas.ripe.net/api/v1/measurement/?key=INSERT_KEY_HERE")


if __name__ == '__main__':
    main()
