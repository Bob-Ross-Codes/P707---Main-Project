# Converts OSM JSON to scene-space features (metres, Unity x/z) for the Raadhuspladsen Modern scene.
import json, math, sys
src, dst = sys.argv[1], sys.argv[2]
LAT0, LON0 = 55.67558, 12.57051          # Raadhustaarnet (OSM way 1011067074 centre)
T = (-32.69, 145.19)                      # tower spire in scene (block-out top vertex)
th = math.radians(50.27)                  # block-out root yaw; model east=-X, north=-Z
E = (-math.cos(th), math.sin(th)); N = (-math.sin(th), -math.cos(th))
KX = math.cos(math.radians(LAT0)) * 111320.0; KY = 110574.0
def sc(lat, lon):
    e = (lon - LON0) * KX; n = (lat - LAT0) * KY
    return [round(T[0] + e*E[0] + n*N[0], 2), round(T[1] + e*E[1] + n*N[1], 2)]
VIEW = (-1.69, 8.4); R = 320
def near(p): return math.hypot(p[0]-VIEW[0], p[1]-VIEW[1]) < R
KEEP = ('building','highway','amenity','natural','barrier','railway','man_made','tourism','landuse','leisure','area:highway','public_transport','historic','footway','kerb')
out = []
for e in json.load(open(src))['elements']:
    t = e.get('tags', {})
    if not any(k in t for k in KEEP): continue
    if e['type'] == 'node': pts = [sc(e['lat'], e['lon'])]
    elif e['type'] == 'way' and 'geometry' in e: pts = [sc(g['lat'], g['lon']) for g in e['geometry'] if g]
    elif e['type'] == 'relation':
        pts = [sc(g['lat'], g['lon']) for m in e.get('members', []) if m.get('role') == 'outer' for g in m.get('geometry', []) if g]
    else: continue
    if not pts or not any(near(p) for p in pts): continue
    out.append({'id': e['type'][0] + str(e['id']), 'tags': t, 'pts': pts})
json.dump(out, open(dst, 'w'), ensure_ascii=False)
print(len(out), 'features')
