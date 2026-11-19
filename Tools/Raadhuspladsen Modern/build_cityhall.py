import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
# Copenhagen City Hall (Martin Nyrop, 1905). LOCAL frame, Unity axes: x along the square facade
# (-37.5..37.5), y up, z into the building (front face z=0). Placed in Unity at (0.5,0,93.8) yaw +2.
C = collection("CityHall")
W2 = 37.5          # half facade width
EAVE = 19.6        # main cornice
PAR = 22.3         # parapet top (block-out height)
objs = []

def solid(name, material, build, tile=2.0):
    bm = bmesh.new(); build(bm); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.normal_update(); world_uv(bm, tile); o = new_obj(name, bm, material, C); objs.append(o); return o

def arch_cutter(bm, x, y0, w, h, depth, z0=-0.5):
    """Box + half-cylinder cutter for an arched opening, bottom at y0, total height h."""
    r = w / 2; hb = h - r
    box(bm, x, y0 + hb / 2, z0 + depth / 2, w, hb, depth)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=depth)
    for v in res['verts']:
        lx, ly, lz = v.co.x, v.co.y, v.co.z            # cone axis = Blender Z -> we want Unity z
        v.co = B(x + lx, y0 + hb + ly, z0 + depth / 2 + lz)

# ---------- window layout on the front (x positions per floor) ----------
side_x = [s * (13.5 + 3.0 * i) for s in (-1, 1) for i in range(8)]       # 13.5 .. 34.5 both sides
centre_x = [-8.0, 8.0]
floors = [  # (sill y, height, width, arched)
    (2.2, 3.4, 1.7, True),     # ground floor
    (7.2, 4.0, 1.8, True),     # main floor (Festsal level)
    (12.6, 2.6, 1.5, False),
    (16.9, 1.6, 1.2, False),
]

# ---------- front wall with cut openings ----------
def front_wall(bm):
    box(bm, 0, (EAVE + 1.0) / 2, 0.6, 2 * W2, EAVE + 1.0, 1.2)
cut = bmesh.new()
for (sy, h, w, arched) in floors:
    for x in side_x + centre_x:
        if arched: arch_cutter(cut, x, sy, w, h, 1.0)
        else: box(cut, x, sy + h / 2, 0.0, w, h, 1.0)
wall = solid("FrontWall", "RP_Brick", front_wall)
cutter = new_obj("cutter", cut, "RP_Brick", C)
m = wall.modifiers.new("cut", 'BOOLEAN'); m.object = cutter; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.use_self = True; m.use_hole_tolerant = True
bpy.context.view_layer.objects.active = wall; bpy.ops.object.modifier_apply(modifier="cut")
bpy.data.objects.remove(cutter, do_unlink=True)

# glass + frames inside the openings (0.35 m recess)
def glazing(bm_glass, bm_frame):
    for (sy, h, w, arched) in floors:
        for x in side_x + centre_x:
            box(bm_glass, x, sy + h / 2, 0.38, w, h, 0.04)
            box(bm_frame, x, sy + h * 0.62, 0.34, w, 0.08, 0.06)           # transom
            box(bm_frame, x, sy + h / 2, 0.34, 0.08, h, 0.06)              # mullion
            box(bm_frame, x, sy - 0.08, -0.05, w + 0.3, 0.16, 0.25)        # stone sill (limestone below)
g = bmesh.new(); f = bmesh.new(); glazing(g, f)
o = new_obj("Glass", g, "RP_Glass", C); objs.append(o)
o = new_obj("Frames", f, "RP_Frame", C); objs.append(o)

# ---------- limestone bands, plinth, cornice ----------
def bands(bm):
    for (y, h, d) in [(6.3, 0.45, 0.12), (12.1, 0.3, 0.1), (16.4, 0.3, 0.1), (EAVE - 0.2, 0.5, 0.35)]:
        box(bm, 0, y, -d / 2, 2 * W2 + 0.4, h, d)
solid("Bands", "RP_Limestone", bands)
def plinth(bm):
    box(bm, 0, 0.6, -0.08, 2 * W2 + 0.3, 1.2, 0.16)
solid("Plinth", "RP_Granite", plinth)

# ---------- crenellated parapet (merlons) ----------
def merlons(bm):
    x = -W2 + 0.5
    while x < W2 - 0.4:
        if abs(x) > 11.6: box(bm, x, EAVE + 2.0, 0.35, 1.0, 2.0, 0.7)
        x += 1.8
solid("Merlons", "RP_Brick", merlons)

# ---------- central projecting section ----------
CW = 11.0  # half width
def centre_block(bm):
    box(bm, 0, 13.0, -0.5, 2 * CW, 26.0, 1.0)        # projects 1 m, rises to 26 m
cb_cut = bmesh.new()
arch_cutter(cb_cut, 0, 0.0, 5.0, 7.2, 3.0, -1.5)        # main portal
arch_cutter(cb_cut, -5.2, 0.0, 2.6, 5.0, 3.0, -1.5)
arch_cutter(cb_cut, 5.2, 0.0, 2.6, 5.0, 3.0, -1.5)
arch_cutter(cb_cut, 0, 9.6, 4.6, 8.4, 0.9, -1.4)         # Absalon niche (shallow)
for x in (-8.0, 8.0):
    for (sy, h, w, arched) in floors[1:]:
        if arched: arch_cutter(cb_cut, x, sy, w, h, 2.0, -1.5)
        else: box(cb_cut, x, sy + h / 2, -0.5, w, h, 2.0)
cblk = solid("CentreBlock", "RP_Brick", centre_block)
cobj = new_obj("cutter2", cb_cut, "RP_Brick", C)
m = cblk.modifiers.new("cut", 'BOOLEAN'); m.object = cobj; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.use_self = True; m.use_hole_tolerant = True
bpy.context.view_layer.objects.active = cblk; bpy.ops.object.modifier_apply(modifier="cut")
bpy.data.objects.remove(cobj, do_unlink=True)
# also open the portal through the main wall
cut = bmesh.new(); arch_cutter(cut, 0, 0.0, 5.0, 7.2, 3.0, -1.5)
for xx in (-5.2, 5.2): arch_cutter(cut, xx, 0.0, 2.6, 5.0, 3.0, -1.5)
cobj = new_obj("cutter3", cut, "RP_Brick", C)
m = wall.modifiers.new("cut", 'BOOLEAN'); m.object = cobj; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.use_self = True; m.use_hole_tolerant = True
bpy.context.view_layer.objects.active = wall; bpy.ops.object.modifier_apply(modifier="cut")
bpy.data.objects.remove(cobj, do_unlink=True)

def centre_details(bm):
    box(bm, 0, 0.6, 1.4, 5.0, 1.2, 0.2)                            # dark door back wall placeholder sill
    box(bm, 0, 7.45, -1.75, 9.0, 0.3, 1.5)                          # balcony slab
    for x in [-4.4 + 0.55 * i for i in range(17)]:                  # balustrade posts
        box(bm, x, 8.15, -2.35, 0.18, 1.1, 0.18)
    box(bm, 0, 8.75, -2.35, 9.0, 0.14, 0.3)                         # handrail
    box(bm, -4.4, 8.15, -1.75, 0.2, 1.1, 1.3); box(bm, 4.4, 8.15, -1.75, 0.2, 1.1, 1.3)
    for (y, h) in [(6.6, 0.4), (19.0, 0.5), (25.6, 0.5)]:
        box(bm, 0, y, -1.05, 2 * CW + 0.3, h, 0.25)                 # bands across centre block
    for s in (-1, 1):                                               # corner pilasters
        box(bm, s * (CW - 0.5), 13.0, -1.1, 1.0, 26.0, 0.25)
solid("CentreStone", "RP_Limestone", centre_details)

def centre_merlons(bm):
    x = -CW + 0.6
    while x < CW - 0.5:
        box(bm, x, 26.0 + 0.9, -0.5, 1.1, 1.8, 1.0); x += 2.0
    for s in (-1, 1):                                               # pinnacle turrets at centre corners
        box(bm, s * (CW - 0.5), 27.5, -0.5, 1.4, 3.0, 1.4)
solid("CentreMerlons", "RP_Brick", centre_merlons)

def dark_openings(bm):
    box(bm, 0, 3.6, 1.1, 5.2, 7.2, 0.1)
    for xx in (-5.2, 5.2): box(bm, xx, 2.5, 1.1, 2.8, 5.0, 0.1)
solid("PortalDark", "RP_Glass", dark_openings)

# ---------- gilded Absalon (simplified bishop-warrior figure) ----------
def absalon(bm):
    z = -0.75
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.9, radius2=0.45, depth=2.6,
                          matrix=__import__('mathutils').Matrix.Translation(B(0, 11.6, z)))
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.32,
                              matrix=__import__('mathutils').Matrix.Translation(B(0, 13.25, z)))
    box(bm, 0, 10.1, z, 1.8, 0.5, 1.0)                              # plinth
    box(bm, 0.75, 12.4, z - 0.2, 0.12, 2.6, 0.12)                   # crozier/axe shaft
    box(bm, -0.7, 12.0, z - 0.25, 0.5, 0.9, 0.12)                   # shield arm
for o in [solid("Absalon", "RP_Gold", absalon)]:
    for p in o.data.polygons: p.use_smooth = True

# ---------- copper roofs ----------
def gable_roof(bm, x0, x1, z0, z1, y_eave, y_ridge, along_x=True):
    """Simple pitched roof over rect x0..x1, z0..z1 with ridge running along x (or z)."""
    if along_x:
        zm = (z0 + z1) / 2
        v = [B(x0, y_eave, z0), B(x1, y_eave, z0), B(x1, y_ridge, zm), B(x0, y_ridge, zm), B(x0, y_eave, z1), B(x1, y_eave, z1)]
    else:
        xm = (x0 + x1) / 2
        v = [B(x0, y_eave, z1), B(x0, y_eave, z0), B(xm, y_ridge, z0), B(xm, y_ridge, z1), B(x1, y_eave, z1), B(x1, y_eave, z0)]
    V = [bm.verts.new(p) for p in v]
    bm.faces.new((V[0], V[1], V[2], V[3])); bm.faces.new((V[5], V[4], V[3], V[2]))
    bm.faces.new((V[0], V[3], V[4])); bm.faces.new((V[1], V[5], V[2]))
def roofs(bm):
    gable_roof(bm, -W2, W2, 0.8, 16.0, EAVE + 0.3, 29.0)                   # front wing
    gable_roof(bm, -W2, -22.0, 16.0, 112.0, EAVE + 0.3, 28.0, False)        # left wing
    gable_roof(bm, 22.0, W2, 16.0, 112.0, EAVE + 0.3, 28.0, False)          # right wing
    gable_roof(bm, -W2, W2, 112.0, 128.0, EAVE + 0.3, 28.0)                 # rear wing
    gable_roof(bm, -20.0, 20.0, 16.0, 48.0, 28.0, 33.5)                     # Raadhushallen
solid("Roofs", "RP_Copper", roofs, 3.0)

def body(bm):
    # rest of the building: brick boxes (no detail; mostly hidden behind the front)
    box(bm, 0, EAVE / 2 + 0.2, 8.6, 2 * W2, EAVE + 0.4, 14.8)            # front wing core
    box(bm, -29.75, EAVE / 2, 64.0, 15.5, EAVE, 96.0)
    box(bm, 29.75, EAVE / 2, 64.0, 15.5, EAVE, 96.0)
    box(bm, 0, EAVE / 2, 120.0, 2 * W2, EAVE, 16.0)
    box(bm, 0, 14.0, 32.0, 40.0, 28.0, 32.0)                              # hall walls
    for s in (-1, 1):                                                     # spire turrets beside the hall
        box(bm, s * 27.5, 18.0, 17.0, 2.6, 36.0, 2.6)
solid("Body", "RP_Brick", body)
def turret_spires(bm):
    import mathutils
    for s in (-1, 1):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=1.9, radius2=0.05, depth=9.0,
            matrix=mathutils.Matrix.Translation(B(s * 27.5, 40.5, 17.0)) @ mathutils.Matrix.Rotation(0, 4, 'X'))
    for s in (-1, 1):                                                     # front corner pinnacles
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=1.2, radius2=0.05, depth=4.5,
            matrix=mathutils.Matrix.Translation(B(s * (W2 - 0.8), PAR + 2.3, 0.8)))
        box(bm, s * (W2 - 0.8), PAR - 1.0, 0.8, 1.8, 2.6, 1.8)
solid("Spires", "RP_Copper", turret_spires, 3.0)

# ---------- the tower (105.6 m), centred at local (-35.3, 50.0) ----------
TX, TZ, TS = -35.3, 50.0, 7.0
def tower(bm):
    box(bm, TX, 31.0, TZ, TS, 62.0, TS)                                  # brick shaft to 62 m
    for y in (30.0, 45.0):                                               # brick corbel ledges
        box(bm, TX, y, TZ, TS + 0.4, 0.5, TS + 0.4)
    box(bm, TX, 63.5, TZ, TS + 1.6, 3.0, TS + 1.6)                       # machicolated crown
    for i in range(5):                                                   # merlons round the crown
        for (dx, dz) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            t = -TS / 2 - 0.4 + i * (TS + 0.8) / 4
            if dx: box(bm, TX + dx * (TS / 2 + 0.6), 65.6, TZ + t, 0.5, 1.2, 0.7)
            else: box(bm, TX + t, 65.6, TZ + dz * (TS / 2 + 0.6), 0.7, 1.2, 0.5)
tw = solid("Tower", "RP_Brick", tower)
tcut = bmesh.new()
for (dx, dz) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:                       # tall slit windows
    for y0 in (24.0, 36.0, 47.0):
        for o in (-1.6, 0, 1.6):
            if dx: arch_cutter_x = box(tcut, TX + dx * TS / 2, y0 + 2.5, TZ + o, 1.2, 5.0, 0.7)
            else: box(tcut, TX + o, y0 + 2.5, TZ + dz * TS / 2, 0.7, 5.0, 1.2)
cobj = new_obj("tcut", tcut, "RP_Brick", C)
m = tw.modifiers.new("cut", 'BOOLEAN'); m.object = cobj; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.use_self = True; m.use_hole_tolerant = True
bpy.context.view_layer.objects.active = tw; bpy.ops.object.modifier_apply(modifier="cut")
bpy.data.objects.remove(cobj, do_unlink=True)
def tower_dark(bm):
    for (dx, dz) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        for y0 in (24.0, 36.0, 47.0):
            for o in (-1.6, 0, 1.6):
                if dx: box(bm, TX + dx * (TS / 2 - 0.4), y0 + 2.5, TZ + o, 0.05, 5.0, 0.7)
                else: box(bm, TX + o, y0 + 2.5, TZ + dz * (TS / 2 - 0.4), 0.7, 5.0, 0.05)
solid("TowerDark", "RP_Glass", tower_dark)
def tower_stone(bm):
    for y in (22.0, 34.5, 57.0):
        box(bm, TX, y, TZ, TS + 0.25, 0.4, TS + 0.25)
solid("TowerStone", "RP_Limestone", tower_stone)
def clocks(bm):
    import mathutils
    for (dx, dz) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        c = (TX + dx * (TS / 2 + 0.05), 54.0, TZ + dz * (TS / 2 + 0.05))
        rot = mathutils.Matrix.Rotation(math.radians(90), 4, 'Y') if dx else mathutils.Matrix.Rotation(math.radians(90), 4, 'X')
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=1.9, radius2=1.9, depth=0.12,
                              matrix=mathutils.Matrix.Translation(B(*c)) @ rot)
solid("ClockFaces", "RP_Gold", clocks)
def spire(bm):
    import mathutils
    box(bm, TX, 66.5 + 3.5, TZ, 5.4, 7.0, 5.4)                           # copper lantern stage
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=4.4, radius2=1.6, depth=6.0,
        matrix=mathutils.Matrix.Translation(B(TX, 76.5, TZ)) @ mathutils.Matrix.Rotation(math.radians(45), 4, 'Z'))
    box(bm, TX, 81.0, TZ, 2.6, 3.0, 2.6)                                 # upper lantern
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=1.6, radius2=0.04, depth=21.0,
        matrix=mathutils.Matrix.Translation(B(TX, 82.5 + 10.5, TZ)))
solid("TowerSpire", "RP_Copper", spire, 3.0)
def finial(bm):
    import mathutils
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.35, matrix=mathutils.Matrix.Translation(B(TX, 104.0, TZ)))
    box(bm, TX, 105.0, TZ, 0.08, 1.2, 0.08)
solid("TowerFinial", "RP_Gold", finial)

export(objs, "City Hall")
print("exported", len(objs), "objects;", sum(len(o.data.polygons) for o in objs), "faces")
