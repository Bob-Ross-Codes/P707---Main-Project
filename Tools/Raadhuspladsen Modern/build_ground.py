import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
F = features()
C = collection("Ground")
P = lambda i: [tuple(p) for p in F[i]['pts']]

# 1. Sidewalk base (Copenhagen grey flags) under everything
bm = bmesh.new(); polygon(bm, [(-350, -250), (350, -250), (350, 450), (-350, 450)], -0.03); world_uv(bm, 3.0)
sidewalk = new_obj("Sidewalk", bm, "RP_Sidewalk", C)

# 2. The square (granite) + the cobbled service street in front of Palace Hotel
bm = bmesh.new(); polygon(bm, P('r11318365'), 0.0)
ribbon(bm, P('w143856048'), 7.0, 0.0)
world_uv(bm, 2.0)
square = new_obj("Square", bm, "RP_Granite", C)

# 3. Roads (asphalt). widths: lanes * ~3 m
roads = {
  'w281562358': 12, 'w1426573200': 12, 'w210984643': 9, 'w680691471': 9, 'w27212548': 9, 'w751162445': 9,
  'w679140317': 12, 'w1694113': 9, 'w679140316': 9, 'w680691472': 9, 'w679140314': 12, 'w44105318': 9,
  'w237108790': 9, 'w497220028': 12, 'w678991587': 12, 'w678991582': 6.5, 'w112185988': 3.5, 'w463663727': 3.5,
  'w1232670547': 7, 'w161641203': 7, 'w1232670548': 7, 'w827602422': 7, 'w827602424': 7, 'w149756673': 7,
  'w1700503': 5, 'w314750683': 6,
}
bm = bmesh.new()
for i, w in roads.items(): ribbon(bm, P(i), w, 0.01)
world_uv(bm, 3.0)
asphalt = new_obj("Roads", bm, "RP_Asphalt", C)

# 4. Cycle tracks (asphalt, Copenhagen style raised a little above the road)
cyc = {'w827602415': 2.8, 'w827602430': 4.8, 'w678991577': 2.8, 'w1426573201': 2.8, 'w678991586': 2.8,
       'w827602431': 2.8, 'w1366539119': 2.8, 'w44091154': 2.8, 'w679140308': 3.5, 'w229215459': 2.9,
       'w659328721': 3.0}
bm = bmesh.new()
for i, w in cyc.items(): ribbon(bm, P(i), w, 0.03)
world_uv(bm, 3.0)
cycle = new_obj("CycleTracks", bm, "RP_Asphalt", C)

# 5. Raised traffic islands
bm = bmesh.new()
for i in ('w1378873019', 'w1378873020', 'w679140315'): polygon(bm, P(i), 0.0, 0.13)
world_uv(bm, 3.0)
islands = new_obj("Islands", bm, "RP_Sidewalk", C)

# 6. City Hall forecourt terrace (walls are 1 m high in OSM; steps run z 74 -> 78)
H = 0.95
left = list(reversed(P('w746759132')))   # (-33,87) ... (-7,79)
right = list(reversed(P('w746759133')))  # (9,78) ... (34,85)
ring = [(-38.0, 95.0), (-38.0, 87.6)] + left[:-1] + [(-7.5, 78.0)] + [(8.5, 78.0)] + right[1:] + [(37.0, 85.2), (37.0, 93.6)]
bm = bmesh.new(); polygon(bm, ring, 0.0, H)
# steps: 8 risers from z=74 to z=78, x -7.5 .. 8.5
n = 8
for k in range(n):
    z0 = 74.0 + k * 0.5
    box(bm, 0.5, (k + 1) * H / n / 2, z0 + (78.0 - z0) / 2, 16.0, (k + 1) * H / n, 78.0 - z0)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
bm.normal_update(); world_uv(bm, 2.0)
terrace = new_obj("Forecourt", bm, "RP_Granite", C)

export([sidewalk, square, asphalt, cycle, islands, terrace], "Ground")
print("ground exported", [o.name for o in C.objects])
