import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
import mathutils, random
from mathutils import Matrix
random.seed(7)
C = collection("Props")
for c in bpy.data.collections:
    c.hide_viewport = c.name != "Props"
out = []

def obj(name, material, build, tile=1.0, smooth=False):
    bm = bmesh.new(); build(bm); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.normal_update(); world_uv(bm, tile); o = new_obj(name, bm, material, C)
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    out.append(o); return o

def cyl(bm, x, y0, z, r, h, seg=12, r2=None):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h,
                          matrix=Matrix.Translation(B(x, y0 + h / 2, z)))

def parent(name, kids):
    e = bpy.data.objects.new(name, None); C.objects.link(e)
    for k in kids: k.parent = e
    out.append(e); return e

# ---------- Dragon Fountain basin (world position (-1.5,0,17.5) applied in Unity) ----------
R = 6.4
def basin_rim(bm):
    seg = 48
    ring = lambda r: [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    o, i_ = ring(R), ring(R - 0.55)
    def v(p, y): return bm.verts.new(B(p[0], y, p[1]))
    ot = [v(p, 0.55) for p in o]; it = [v(p, 0.55) for p in i_]; ob = [v(p, 0.0) for p in o]; ib = [v(p, 0.1) for p in i_]
    for k in range(seg):
        n = (k + 1) % seg
        bm.faces.new((ot[k], ot[n], it[n], it[k])); bm.faces.new((ob[n], ob[k], ot[k], ot[n])); bm.faces.new((ib[k], ib[n], it[n], it[k]))
    bm.faces.new(list(reversed(ib)))                                    # basin floor
    bm.normal_update()
    for f in bm.faces:                                                  # outward normals by centroid test
        c = f.calc_center_median();
rim = obj("FountainBasin", "RP_Granite", basin_rim, 2.0)
def water(bm):
    bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=R - 0.5, matrix=Matrix.Translation(B(0, 0.38, 0)))
obj("FountainWater", "RP_Water", water, 4.0)
def rock(bm):
    r = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    noise = mathutils.noise
    for v in r['verts']:
        d = v.co.normalized(); s = 1.0 + 0.22 * noise.noise(d * 2.3) + 0.08 * noise.noise(d * 6.1)
        v.co = Vector((d.x * 2.6 * s, d.y * 2.3 * s, max(-0.2, d.z) * 1.9 * s + 0.2))
rk = obj("FountainRock", "RP_FountainRock", rock, 1.5)
for p in rk.data.polygons: p.use_smooth = False
fountain = parent("Dragon Fountain", [o for o in out])

# ---------- street lamp (Raadhuspladsen masts, ~9 m) ----------
k0 = len(out)
def lamp_pole(bm):
    cyl(bm, 0, 0, 0, 0.14, 0.6, 12); cyl(bm, 0, 0.6, 0, 0.09, 8.2, 10, 0.06)
    box(bm, 0.45, 8.65, 0, 1.0, 0.07, 0.07)                             # short arm
obj("LampPole", "RP_DarkMetal", lamp_pole, 1.0, True)
def lamp_head(bm):
    cyl(bm, 0.95, 8.25, 0, 0.32, 0.38, 16, 0.12)
obj("LampHead", "RP_DarkMetal", lamp_head, 1.0, True)
def lamp_glow(bm):
    bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=0.3, matrix=Matrix.Translation(B(0.95, 8.24, 0)) @ Matrix.Rotation(math.pi, 4, 'X'))
obj("LampLens", "RP_LampGlow", lamp_glow)
parent("Street Lamp", out[k0:])

# ---------- bench (granite block + wooden seat + back) ----------
k0 = len(out)
def bench_stone(bm):
    box(bm, -0.85, 0.2, 0, 0.3, 0.4, 0.55); box(bm, 0.85, 0.2, 0, 0.3, 0.4, 0.55)
obj("BenchFeet", "RP_Granite", bench_stone, 1.0)
def bench_wood(bm):
    for i in range(4): box(bm, 0, 0.44, -0.2 + i * 0.13, 2.0, 0.05, 0.11)
    for i in range(2): box(bm, 0, 0.62 + i * 0.16, 0.3, 2.0, 0.11, 0.04)
    box(bm, -0.8, 0.6, 0.3, 0.05, 0.4, 0.05); box(bm, 0.8, 0.6, 0.3, 0.05, 0.4, 0.05)
obj("BenchWood", "RP_Wood", bench_wood, 1.0)
parent("Bench", out[k0:])

# ---------- waste bin (Copenhagen green), steel bollard, bike rack ----------
k0 = len(out)
def bin_(bm):
    cyl(bm, 0, 0, 0, 0.05, 0.9, 8); cyl(bm, 0, 0.35, 0.22, 0.24, 0.7, 16)
obj("Bin", "RP_BinGreen", bin_, 1.0, True); parent("Waste Bin", out[k0:])
k0 = len(out)
def bollard(bm):
    cyl(bm, 0, 0, 0, 0.1, 1.0, 14)
obj("BollardSteel", "RP_Steel", bollard, 1.0, True); parent("Bollard", out[k0:])
k0 = len(out)
def rack(bm):
    for i in range(6):                                                  # wall-loop style: hoops 0.8 m apart
        x = -2.0 + i * 0.8
        box(bm, x, 0.4, -0.35, 0.04, 0.8, 0.04); box(bm, x, 0.4, 0.35, 0.04, 0.8, 0.04); box(bm, x, 0.8, 0, 0.04, 0.04, 0.74)
obj("RackSteel", "RP_Steel", rack, 1.0); parent("Bike Rack", out[k0:])

export(out, "Street Props")
print("props", [o.name for o in out if o.type == 'EMPTY'])
