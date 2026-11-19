# OSM point features -> "type x z yaw" lines for Unity scattering (only what the window can see, with margin).
import json, math, random, sys
random.seed(11)
F = json.load(open(sys.argv[1]))
heads = [(x, z) for x in (-5.0, -1.69, 1.6) for z in (5.0, 8.9)]
def visible(x, z, margin=0.25):
    for hx, hz in heads:
        if z <= 11.6: continue
        xs = hx + (x - hx) * (11.56 - hz) / (z - hz)
        if -4.34 - 5.3 * margin <= xs <= 0.96 + 5.3 * margin: return True
    return False
def kind(t):
    if t.get('natural') == 'tree': return 'tree'
    if t.get('highway') == 'street_lamp': return 'lamp'
    if t.get('amenity') == 'bench': return 'bench'
    if t.get('amenity') == 'waste_basket': return 'bin'
    if t.get('barrier') == 'bollard': return 'bollard'
    if t.get('amenity') == 'bicycle_parking' and t.get('covered') != 'yes': return 'rack'
out = []
for f in F:
    t = f['tags']; k = kind(t)
    if not k or len(f['pts']) != 1 or t.get('layer', '0').startswith('-'): continue
    x, z = f['pts'][0]
    if math.hypot(x + 1.69, z - 8.4) > 300 or not visible(x, z): continue
    if k == 'tree': yaw = random.uniform(0, 360)
    elif k == 'lamp': yaw = 0 if x < 0 else 180
    elif k == 'bench': yaw = -90 if x < 0 else 90
    elif k == 'rack': yaw = 90
    else: yaw = random.uniform(0, 360)
    out.append(f"{k} {x:.2f} {z:.2f} {yaw:.1f}")
open(sys.argv[2], 'w').write("\n".join(out))
from collections import Counter; print(Counter(l.split()[0] for l in out))
