import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
# Industriens Hus (rebuilt 2013): glass office block, 8 storeys, OSM footprint w25658852. Scene coordinates.
F = features()
C = collection("IndustriensHus")
ring = [tuple(p) for p in F['w25658852']['pts']]
if ring[0] == ring[-1]: ring = ring[:-1]
H, FLOOR = 31.0, 3.8
bm = bmesh.new(); polygon(bm, ring, 0.0, H); world_uv(bm, 4.0)
glass = new_obj("IH_Glass", bm, "RP_CurtainGlass", C)
bm = bmesh.new()                                     # slab edges: thin outset rings every storey
for k in range(1, int(H // FLOOR) + 1):
    y = k * FLOOR
    for i in range(len(ring)):
        p, q = ring[i], ring[(i + 1) % len(ring)]
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 0.5: continue
        yaw = math.degrees(math.atan2(-(q[1] - p[1]), q[0] - p[0]))
        box(bm, (p[0] + q[0]) / 2, y, (p[1] + q[1]) / 2, L + 0.3, 0.35, 0.3, yaw)
world_uv(bm, 2.0)
bands = new_obj("IH_Slabs", bm, "RP_Limestone", C)
export([glass, bands], "Industriens Hus")
print("IH ok", len(ring))
