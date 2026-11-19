import os
# Run from Blender (Scripting tab or the Blender MCP). Set PROJECT to your checkout if __file__ is unknown.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(PROJECT, "Tools", "Raadhuspladsen Modern", "rp_lib.py")).read())
# Palace Hotel (Anton Rosen, 1910): red-brick block on the west side of the square with a slim corner
# tower. Front follows the OSM footprint w638965060; world (scene) coordinates, no placement needed.
import mathutils
C = collection("PalaceHotel")
rows = [(1.0, 3.2), (5.2, 2.2), (8.6, 2.2), (12.0, 2.2), (15.4, 2.2), (18.6, 1.8)]
objs = []
objs += facade_segment("PalaceA", (-69.2, 60.4), (-73.1, 81.5), C, 22.5, 16.0, rows, ridge=34.0)
objs += facade_segment("PalaceB", (-74.1, 87.1), (-76.8, 102.8), C, 22.5, 14.0, rows, ridge=33.0)
# corner block between the Palace and Frederiksberggade (OSM w1013392339), plastered
crow = [(1.0, 3.0), (4.8, 2.0), (8.0, 2.0), (11.2, 2.0), (14.4, 2.0), (17.4, 1.6)]
objs += facade_segment("CornerFront", (-64.8, 34.3), (-69.2, 58.5), C, 20.0, 12.0, crow, wall="RP_Plaster", spacing=2.9, ridge=27.0)
objs += facade_segment("CornerSouth", (-87.6, 36.8), (-64.8, 32.4), C, 20.0, 10.0, crow, wall="RP_Plaster", spacing=2.9, ridge=26.0)
objs += facade_segment("PalaceSouth", (-77.7, 57.1), (-69.2, 58.5), C, 22.5, 8.0, rows[1:], spacing=3.0, ridge=30.0)

# corner tower between the two fronts, centred where the OSM footprint juts out toward the square
TX, TZ, S = -70.8, 84.9, 5.6
def tower(bm):
    box(bm, TX, 24.0, TZ, S, 48.0, S)
    box(bm, TX, 48.6, TZ, S + 0.6, 1.2, S + 0.6)                          # gallery ledge
    box(bm, TX, 51.5, TZ, S - 1.4, 5.0, S - 1.4)                          # belfry stage
bm = bmesh.new(); tower(bm); world_uv(bm, 2.0); tw = new_obj("PalaceTower", bm, "RP_Brick", C)
cut = bmesh.new()
for y in range(6, 46, 4):                                                 # small window per storey, square-facing sides
    box(cut, TX + S / 2, y + 1.0, TZ, 1.2, 1.6, 0.9)
    box(cut, TX, y + 1.0, TZ - S / 2, 0.9, 1.6, 1.2); box(cut, TX, y + 1.0, TZ + S / 2, 0.9, 1.6, 1.2)
boolean_cut(tw, cut, C); objs.append(tw)
bm = bmesh.new()
for y in range(6, 46, 4):
    box(bm, TX + S / 2 - 0.35, y + 1.0, TZ, 0.04, 1.6, 0.9)
    box(bm, TX, y + 1.0, TZ - S / 2 + 0.35, 0.9, 1.6, 0.04); box(bm, TX, y + 1.0, TZ + S / 2 - 0.35, 0.9, 1.6, 0.04)
objs.append(new_obj("PalaceTowerGlass", bm, "RP_Glass", C))
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=2.6, radius2=0.05, depth=11.0,
                      matrix=mathutils.Matrix.Translation(B(TX, 54.0 + 5.5, TZ)))
box(bm, TX, 65.6, TZ, 0.08, 1.6, 0.08)
world_uv(bm, 3.0); objs.append(new_obj("PalaceSpire", bm, "RP_Copper", C))
bm = bmesh.new()
for (dx, dz) in [(1, 0), (0, -1), (0, 1)]:                                # clock faces
    c = (TX + dx * (S / 2 - 0.65), 51.5, TZ + dz * (S / 2 - 0.65))
    rot = mathutils.Matrix.Rotation(math.radians(90), 4, 'Y') if dx else mathutils.Matrix.Rotation(math.radians(90), 4, 'X')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=1.3, radius2=1.3, depth=0.1, matrix=mathutils.Matrix.Translation(B(*c)) @ rot)
objs.append(new_obj("PalaceClock", bm, "RP_Gold", C))

export(objs, "Palace Hotel")
print("palace", len(objs), "objects", sum(len(o.data.polygons) for o in objs), "faces")
