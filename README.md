# RIPE-Atlas-sbucket
Spatial Bucketing of RIPE Atlas Probes on Map Projections

This tool selects probes based on spatial distribution on an arbitrary map projection. Some tweaking might be required for non-mercartor like projections.

## Usage
```
usage: sbucket.py [-h] [--data DATA] [--projection PROJECTION]
                  [--maxiter MAXITER] [--country COUNTRY [COUNTRY ...]]
                  [--verbose]
                  count

Spatial bucketing of RIPE Atlas probes.

positional arguments:
  count                 number of probes to be returned

optional arguments:
  -h, --help            show this help message and exit
  --data DATA, -d DATA  dump of probe metadata, if not given data is retrieved
                        from atlas.ripe.net
  --projection PROJECTION, -p PROJECTION
                        projection to use for spatial distribution, has to be
                        supported by pyproj (default: merc)
  --maxiter MAXITER, -m MAXITER
                        maximum number of iterations to be performed (default:
                        100)
  --country COUNTRY [COUNTRY ...], -c COUNTRY [COUNTRY ...]
                        Allowed countries. If not set: world-wide.
  --verbose, -v
```

## Example
```
./sbucket.py meta-20150223.txt 100
[11689, 15655, 52, 1114, 168, 628, 86, 21451, 16100, 24, 13237, 11, 4096, 303, 176, 33, 4920, 683, 1190, 2810, 14449, 449, 239, 6107, 12505, 17601, 1002, 4814, 74, 1118, 78, 243, 212, 1046, 3466, 16632, 21126, 3585, 227, 126, 73, 12811, 77, 2917, 483, 446, 2062, 3, 253, 3168, 2250, 11061, 3053, 329, 1147, 3461, 2001, 524, 1042, 3579, 93, 75, 4089, 20255, 3646, 4985, 12848, 11691, 165, 3924, 516, 11744, 4776, 1016, 4000, 2564, 97, 14446, 1069, 40, 603, 13028, 645, 521, 20092, 332, 18357, 18641, 1154, 12372, 1133, 234, 1149, 4153, 2456, 15297, 13805, 2218, 18437, 4919, 470, 10688, 1165, 1003]
```

Without sbucket selection (world-wide 500 probes): 
![alt text](https://github.com/cod3monk/RIPE-Atlas-sbucket/raw/master/without-sbucket.png "Map without sbucket.")

The distribution is biased, because it prefers areas with a high density of probes. Here you can see the global distribution of probes by country code:
![alt text](https://github.com/cod3monk/RIPE-Atlas-sbucket/raw/master/WW500-probes-per-country.png "Probe Numbers by Country (WW500).")

With sbucket selection (world-wide 500 probes): 
![alt text](https://github.com/cod3monk/RIPE-Atlas-sbucket/raw/master/with-sbucket.png "Map with sbucket.")

After application of the spacial bucket algorithm this distribution has a much longer tail (thus includes more countries) and small countries with high probe density are moved down and large countries are moved up the ladder:
![alt text](https://github.com/cod3monk/RIPE-Atlas-sbucket/raw/master/SB500-probes-per-country.png "Probe Numbers by Country (WW500).")

## Algorithm
It tries to find a grid with roughly square cells where the number of cells by iterating over grid sizes. It stops after a grid was found which yields the number of probes (with a 5% error margin) OR a maximum number of iterations have been performed.

If the number of probes is bellow the targeted count, the cell number is increased (vertically and horizontally) by 50%, otherwise it is reduce by 10%.

Within one cell a random probe is selected.

## Known Problems
 * Selection might yield more or less probes then expected, no guarantees here, but it works well for larger numbers (>20).
 * The grid is set between 85 degrees north and east, this might be a problem with other projections than mercartor
 