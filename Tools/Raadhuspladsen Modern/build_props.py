import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
import mathutils, random
from mathutils import Matrix
random.seed(7)
C = collection("Props")
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
R = 6.45                      # outer radius of the basin wall
def lathe(bm, profile, seg=96):
    """Spin a (radius, height) profile around the up axis (Unity y)."""
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        rings.append([bm.verts.new(B(r * math.cos(a), y, r * math.sin(a))) for r, y in profile])
    for k in range(seg):
        r0, r1 = rings[k], rings[(k + 1) % seg]
        for i in range(len(profile) - 1):
            bm.faces.new((r0[i], r1[i], r1[i + 1], r0[i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def basin_rim(bm):
    prof = [(R + 0.08, 0.0), (R + 0.08, 0.06), (R, 0.08), (R, 0.36)]          # plinth step, outer wall
    prof += [(R - 0.25 + 0.25 * math.cos(t), 0.36 + 0.24 * math.sin(t))       # half-round coping
             for t in [i * math.pi / 10 for i in range(11)]]
    prof += [(R - 0.5, 0.30), (R - 0.55, 0.05)]                              # inner wall, slight batter
    lathe(bm, prof)
obj("FountainBasin", "RP_BasinStone", basin_rim, 2.3)
def floor(bm):
    bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=R - 0.52, matrix=Matrix.Translation(B(0, 0.05, 0)))
obj("FountainFloor", "RP_BasinFloor", floor, 2.3)
def water(bm):
    bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=R - 0.52, matrix=Matrix.Translation(B(0, 0.42, 0)))
obj("FountainWater", "RP_FountainWater", water, 4.0)
def nozzles(bm):                                                         # bronze spouts on the coping, one per jet
    for i in range(8):
        a = (i + 0.5) * 2 * math.pi / 8; x, z = (R - 0.25) * math.cos(a), (R - 0.25) * math.sin(a)
        cyl(bm, x, 0.58, z, 0.11, 0.08, 12); cyl(bm, x, 0.66, z, 0.06, 0.12, 10, 0.035)
obj("FountainNozzles", "RP_Bronze", nozzles, 1.0, True)
# the bronze dragon/bull group (Generated/DragonBullGroup.fbx, Meshy) sits on the basin floor in the prefab
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
