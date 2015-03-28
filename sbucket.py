#!/usr/bin/env python
'''
Spatial Bucketing of RIPE Atlas Probes on Map Projections

Author: Julian Hammer <julian.hammer@u-sys.org>
License: AGPLv3
'''
from __future__ import print_function
from __future__ import division

import sys
import json
import argparse
import random

import pyproj


def getProbes(probes, online=True, country_codes=None):
    selected_probes = []
    for p in probes:
        # Filtering probes
        if online and p['status'] != 1:
            continue
        if country_codes and p['country_code'] not in country_codes:
            continue
        
        selected_probes.append({
            'id': p['id'],
            'longitude': p['longitude'],
            'latitude': p['latitude']})
    
    return selected_probes


def main():
    parser = argparse.ArgumentParser(description='Spatial bucketing of RIPE Atlas probes.')
    parser.add_argument('probedata', type=file, help='dump of probe metadata')
    parser.add_argument('--projection', '-p', default='merc', help='projection to use for spatial '
        'distribution, has to be supported by pyproj (default: merc)')
    parser.add_argument('count', type=int, help='number of probes to be returned')
    parser.add_argument('--maxiter', '-m', type=int, default=100, help='maximum number of '
        'iterations to be performed (default: 100)')
    parser.add_argument('--country', '-c', nargs='+', help='Allowed countries. If not set: '
        'world-wide.')
    parser.add_argument('--verbose', '-v', action='count', default=0)
        
    args = parser.parse_args()
    
    probes = []
    for line in args.probedata.readlines():
        probes.append(json.loads(line))
    probes = getProbes(probes, country_codes=args.country)
    
    p_latlong = pyproj.Proj(proj='latlong')
    p_dst = pyproj.Proj(proj=args.projection)
    
    for p in probes:
        try:
            # Project to targeted map projection
            p['proj'] = \
                pyproj.transform(p_latlong, p_dst, float(p['longitude']), float(p['latitude']))
        except:
            # ignore probes with bad long/lat information
            pass
    
    min_dst = pyproj.transform(p_latlong, p_dst, -180, -85.)
    max_dst = pyproj.transform(p_latlong, p_dst, 180, 85.)
    
    target_count = int(sys.argv[2])
    cell_counts = (10, 20)
    cells = {}
    
    # 10% acceptable deviation
    max_iter = args.maxiter
    while abs(len(cells)-target_count) > 0.05*target_count and not max_iter <= 0:
        if len(cells) < target_count:
            cell_counts = cell_counts[0]*1.5, cell_counts[1]*1.5
        else:
            cell_counts = cell_counts[0]*0.9, cell_counts[1]*0.9
    
        cells = {}
        
        div = ((max_dst[0]-min_dst[0])/cell_counts[0],
               (max_dst[1]-min_dst[1])/cell_counts[1])
        
        cells = {}
        for p in probes:
            if not 'proj' in p:
                continue
            
            key = (int(p['proj'][0]/div[0]), int(p['proj'][1]/div[1]))
            if key not in cells:
                cells[key] = [p['id']]
            else:
                cells[key].append(p['id'])
        
        max_iter -= 1
    
    if args.verbose >= 1:
        print("selected probes:",)
    
    print([random.choice(c) for c in cells.values()])
    
    if args.verbose >= 1:
        print('count:', len(cells))
    
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
                "value": ",".join([str(random.choice(c)) for c in cells.values()]),
                "type": "probes",
                "requested": len(cells)}],
            "is_oneoff": True})+"'", "https://atlas.ripe.net/api/v1/measurement/?key=INSERT_KEY_HERE")

if __name__ == '__main__':
    main()