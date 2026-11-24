"""Builds the in-world info props for every era, three looks (A, B, C) each, and exports them for Unity.

Run:  /Applications/Blender.app/Contents/MacOS/Blender -b --python Tools/Blender/info_props.py
Writes Assets/3D Assets/Info Props/Info Prop <era> <A|B|C>.fbx with their surface textures, and crops the photos out
of the old web-page cards into Assets/2D Assets/Textinfo/Photos/<era>_<TV|MID|TH>.png.
Nothing is baked into the writing surface: each prop carries a "Page" empty (PAGE_W x PAGE_H, facing -Y) where the
Unity InfoPage component lays out live text and the photo.
Blender axes: Z up, the writing side faces -Y, metres, origin on the ground at the prop's centre.
Every moving part hangs under a pivot empty with its <name>_Mesh child at identity; the Unity clips animate the meshes.
"""
import bpy, bmesh, math, os, random, sys
import numpy as np
from mathutils import Vector, Matrix

sys.dont_write_bytecode = True   # no __pycache__ next to the scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hut_4000 import (ROOT, TEX as HUT_TEX, n3, angdiff, tube, wobble_path, lashing, new_obj, material, save_png,
                      fbm, normal_from_height, mix)

OUT = os.path.join(ROOT, "Assets", "3D Assets", "Info Props")
TEX = os.path.join(OUT, "Textures")
CARDS = os.path.join(ROOT, "Assets", "2D Assets", "Textinfo")
PHOTOS = os.path.join(CARDS, "Photos")
CARD_FILES = {"4000": {"TV": "4000_TV2.png", "MID": "4000_Mid2.png", "TH": "4000_TH2.png"},
              "1130": {k: "1130_%s2.png" % k for k in ("TV", "MID", "TH")},
              "1620": {k: "1620_%s2.png" % k for k in ("TV", "MID", "TH")}}
PAGE_W, PAGE_H = 2.45, 1.8      # the live page: title across, 1.4 m body column, photo and caption beside it
ZC = 0.55 + PAGE_H / 2          # page centre height: its lowest line sits 0.55 m up, clear of long grass
PPM = 640                       # texture pixels per metre
SE = 6.0                        # superellipse power of a stretched hide
LOBES = ((math.pi / 4, 0.16, 0.10), (3 * math.pi / 4, 0.16, 0.10), (-math.pi / 4, 0.14, 0.11),
         (-3 * math.pi / 4, 0.14, 0.11), (math.pi / 2, 0.07, 0.22), (-math.pi / 2, 0.05, 0.07))   # legs, neck, tail


# ---------------------------------------------------------------- images
def pixels(img, channels=3):
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[..., :channels]   # rows run bottom to top, as in UV space


def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    a = pixels(img)
    bpy.data.images.remove(img)
    return a


def tile(src, h, w):
    return np.tile(src, (-(-h // src.shape[0]), -(-w // src.shape[1]), 1))[:h, :w].copy()


def resize(arr, w, h):
    img = bpy.data.images.new("resize", arr.shape[1], arr.shape[0])
    rgba = np.ones(arr.shape[:2] + (4,), np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba.ravel())
    img.scale(w, h)
    out = pixels(img)
    bpy.data.images.remove(img)
    return out


def card_photo(path):
    """The photo or map of a web-page card, cropped out of the page, with the page's zoom button painted over."""
    a = load(path)
    page = np.median(a[:, -6:].reshape(-1, 3), axis=0)   # the right margin is bare page on every card
    off = np.abs(a - page).max(-1) > 0.035
    rows = np.flatnonzero(off.mean(1) > 0.5)               # text rows never cover half the width; photo rows do
    r = max(np.split(rows, np.flatnonzero(np.diff(rows) > 1) + 1), key=len)
    cols = np.flatnonzero(off[r[0]:r[-1] + 1].mean(0) > 0.5)
    p = a[r[0] + 1:r[-1], cols[0] + 1:cols[-1]].copy()
    s, f = 50, 8      # zoom button in the bottom-left corner: clone the patch beside it, feathered at the inner edges
    yy, xx = np.mgrid[0:s, 0:s]
    m = (np.clip((s - xx) / f, 0, 1) * np.clip((s - yy) / f, 0, 1))[..., None]
    p[:s, :s] = p[:s, :s] * (1 - m) + p[:s, s:2 * s] * m
    return p


# ---------------------------------------------------------------- surface textures (1024 px tileable sets)
_SETS = {}


def tex_set(kind):
    """(colour, normal) tiles for a surface kind."""
    if kind in _SETS:
        return _SETS[kind]
    s = 1024
    if kind == "rawhide":
        out = (load(os.path.join(HUT_TEX, "Hut_Rawhide_BaseColor.png")),
               load(os.path.join(HUT_TEX, "Hut_Rawhide_Normal.png")))
    else:
        low, mid, hi = fbm(s, 1.8), fbm(s, 1.2), fbm(s, 0.4)
        if kind == "parchment":
            col = mix((0.86, 0.77, 0.58), (0.70, 0.58, 0.38), np.clip(low * 1.3 - 0.3, 0, 1))
            col *= (1 - 0.15 * np.clip((fbm(s, 1.5) - 0.62) * 5, 0, 1))[..., None]
            h, k = mid * 0.3 + hi * 0.1, 1.5
        elif kind == "paper":
            col = mix((0.94, 0.90, 0.79), (0.84, 0.78, 0.63), np.clip(low * 1.2 - 0.35, 0, 1))
            col *= (1 - 0.18 * np.clip((fbm(s, 0.9) - 0.78) * 8, 0, 1))[..., None]          # foxing spots
            h, k = hi * 0.2, 1.0
        elif kind in ("granite", "fieldstone"):
            dark, light = ((0.40, 0.37, 0.36), (0.66, 0.60, 0.57)) if kind == "granite" else \
                          ((0.38, 0.34, 0.29), (0.58, 0.52, 0.44))
            col = mix(dark, light, np.clip(mid * 1.2 - 0.1, 0, 1))
            col *= np.where(hi > 0.72, 0.5, np.where(hi < 0.25, 1.1, 1.0))[..., None]        # speckle
            h, k = mid * 0.6 + hi * 0.4, 4.0
        elif kind in ("oak", "timber"):
            grain = fbm(s, 1.0, aniso=10.0)                                                 # grain runs along u
            col = mix((0.36, 0.25, 0.15), (0.55, 0.40, 0.25), grain)
            h, k = grain, 2.0
            if kind == "oak":                                                               # plank seams
                seam = (np.arange(s) % 256 < 4)[:, None]
                col = np.where(seam[..., None], col * 0.45, col)
                h = h - seam * 0.6
        elif kind == "painted":
            col = mix((0.84, 0.78, 0.63), (0.78, 0.71, 0.55), low) * (0.95 + 0.05 * fbm(s, 1.0, aniso=10.0))[..., None]
            h, k = fbm(s, 1.0, aniso=10.0) * 0.3, 0.8
        out = (col, normal_from_height(h, k))
    _SETS[kind] = out
    return out


def write_surface(name, kind, bbox, lighten=True, paint=None):
    """Texture for a writing surface whose UVs span bbox (xmin, xmax, zmin, zmax, relative to the page centre).
    lighten: scrape the area behind the page lighter and smoother. paint(base, xs, zs): extra decoration."""
    xmin, xmax, zmin, zmax = bbox
    W, H = int(round((xmax - xmin) * PPM / 8)) * 8, int(round((zmax - zmin) * PPM / 8)) * 8
    col, nrm = tex_set(kind)
    base, nn = tile(col, H, W), tile(nrm, H, W)
    if lighten:
        x0, y0 = (-PAGE_W / 2 - xmin) * PPM, (-PAGE_H / 2 - zmin) * PPM
        yy, xx = np.mgrid[0:H, 0:W]
        f = 40
        s = (np.clip(np.minimum(xx - x0 + f, x0 + PAGE_W * PPM + f - xx) / f, 0, 1) *
             np.clip(np.minimum(yy - y0 + f, y0 + PAGE_H * PPM + f - yy) / f, 0, 1))
        s = (s * s * (3 - 2 * s))[..., None]
        base = base * (1 - s * 0.6) + base.mean((0, 1)) * 1.1 * s * 0.6
        nn = nn * (1 - s * 0.85) + np.array((0.5, 0.5, 1.0)) * s * 0.85
    if paint:
        xs = xmin + (np.arange(W) + 0.5) / PPM
        zs = zmin + (np.arange(H) + 0.5) / PPM
        paint(base, xs, zs)
    save_png(base, os.path.join(TEX, name + "_BaseColor.png"))
    save_png(resize(nn, W // 2, H // 2), os.path.join(TEX, name + "_Normal.png"))


# ---------------------------------------------------------------- geometry helpers
def superellipse(al, p):
    return (abs(math.cos(al)) ** p + abs(math.sin(al)) ** p) ** (-1 / p)


def hide_edge(a, b, k, lobes=True, p=SE):
    def f(al):
        e = superellipse(al, p)
        if lobes:
            for c, amp, w in LOBES:
                e += amp * math.exp(-(angdiff(al, c) / w) ** 2)
        e *= 1 + 0.015 * n3(k * 7.0, math.cos(al) * 3, math.sin(al) * 3)
        return e * math.cos(al) * a, e * math.sin(al) * b
    return f


def stone_edge(a, b_top, b_bot, p_top, p_bot, k, rough):
    def f(al):
        c, s = math.cos(al), math.sin(al)
        p, b = (p_top, b_top) if s > 0 else (p_bot, b_bot)
        e = superellipse(al, p) * (1 + rough * n3(k * 5, c * 2, s * 2) + rough * 0.5 * n3(k * 5, c * 7, s * 7))
        return e * c * a, e * s * b
    return f


def extent(edge, n=360):
    pts = [edge(2 * math.pi * j / n) for j in range(n)]
    return min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)


def sheet(bm, uv, edge, zc, bbox, y0=0.0, belly=0.0, rough=0.0, k=0.0, mat=0, NA=120, NR=20):
    """Radial sheet in the XZ plane facing -Y, centred at (0, y0, zc); UVs map bbox to 0-1. Returns its faces."""
    xmin, xmax, zmin, zmax = bbox
    pts = [edge(2 * math.pi * j / NA) for j in range(NA)]
    vid, uvs = {}, {}

    def vert(i, j):
        j %= NA
        key = (0, 0) if i == 0 else (i, j)
        if key not in vid:
            rr = i / NR
            x, z = pts[j][0] * rr, pts[j][1] * rr
            y = y0 - belly * (1 - rr * rr) - rough * n3(x * 2.5, z * 2.5, k)
            vid[key] = bm.verts.new((x, y, zc + z))
            uvs[key] = ((x - xmin) / (xmax - xmin), (z - zmin) / (zmax - zmin))
        return vid[key], uvs[key]
    faces = []
    for i in range(NR):
        for j in range(NA):
            q = [vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)]   # winding faces -Y
            if i == 0:
                q = q[:3]
            f = bm.faces.new([v for v, _ in q])
            f.material_index = mat
            for loop, (_, t) in zip(f.loops, q):
                loop[uv].uv = t
            faces.append(f)
    return faces


BOX_FACES = (((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)), ((1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)),
             ((-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)), ((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)),
             ((-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)))
BOX_AXES = ("xz", "xz", "yz", "yz", "xy", "xy")   # front, back, -x, +x, bottom, top


def box(bm, uv, c, size, mat, tile_m=1.0, long="x", front=None, rot=None):
    """Box at c. UVs are box-projected, the texture's u along the long axis, one repeat per tile_m metres.
    front=(mat, (xmin, xmax, zmin, zmax)) gives the -Y face its own material and maps that rect to 0-1.
    rot=(angle, axis) turns the box about c. Returns its verts."""
    h = [s / 2 for s in size]
    verts = []
    for fi, (quad, ax) in enumerate(zip(BOX_FACES, BOX_AXES)):
        vs = [bm.verts.new((c[0] + q[0] * h[0], c[1] + q[1] * h[1], c[2] + q[2] * h[2])) for q in quad]
        f = bm.faces.new(vs)
        verts += vs
        for loop, v in zip(f.loops, vs):
            co = {"x": v.co.x, "y": v.co.y, "z": v.co.z}
            if fi == 0 and front:
                r = front[1]
                loop[uv].uv = ((v.co.x - r[0]) / (r[1] - r[0]), (v.co.z - r[2]) / (r[3] - r[2]))
            elif long in ax:
                other = ax[1] if ax[0] == long else ax[0]
                loop[uv].uv = (co[long] / tile_m, co[other] / tile_m)
            else:
                loop[uv].uv = (co[ax[0]] / tile_m, co[ax[1]] / tile_m)
        f.material_index = front[0] if (fi == 0 and front) else mat
    if rot:
        bmesh.ops.rotate(bm, verts=verts, cent=c, matrix=Matrix.Rotation(rot[0], 3, rot[1]))
    return verts


def pivot(name, loc):
    em = bpy.data.objects.new(name, None)
    em.location = loc
    bpy.context.collection.objects.link(em)
    return em


def part(name, loc, mats, fill):
    """Pivot empty at loc with a <name>_Mesh child at identity; fill(bm, uv) builds the mesh in world space."""
    em = pivot(name, loc)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    fill(bm, uv)
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=-loc)
    ob = new_obj(name + "_Mesh", bm, mats)
    ob.parent = em
    return ob


def page(mesh_ob, loc, at):
    """The Page empty: where InfoPage lays out text and photo, centred on the page, facing -Y."""
    em = pivot("Page", Vector(at) - loc)
    em.parent = mesh_ob


def solid(bm, faces, thickness):
    """Solidify a sheet backwards (+Y)."""
    before = set(bm.verts)
    bmesh.ops.solidify(bm, geom=faces, thickness=thickness)
    new = [v for v in bm.verts if v not in before]
    if new and sum(v.co.y for v in new) / len(new) < sum(v.co.y for v in before) / len(before):
        for v in new:                                            # it went forward: mirror the new shell behind
            v.co.y += 2 * thickness
    return new


def lacing(bm, uv, edge, zc, y, targets, n, mat):
    """Cords from holes just inside the edge to the nearest frame member; targets(x, z) -> (point, gap) list."""
    for m in range(n):
        al = 2 * math.pi * (m + 0.5) / n
        x, z = edge(al)
        x, z = x * 0.93, zc + z * 0.93
        hole = Vector((x, y - 0.008, z))
        tgt = min(targets(x, z), key=lambda t: t[1])[0]
        mid = (hole + tgt) / 2 + Vector((0, -0.01, -0.012))
        tube(bm, uv, [hole, mid, tgt], [0.005] * 3, mat, sides=4, tile=0.3)


# ---------------------------------------------------------------- the props
def mats(*names):
    return {n: bpy.data.materials.get(n) or material(n, (0.5, 0.45, 0.4)) for n in names}


def frame_sheet(name, seed, kind, square):
    """4000 A (round poles, rawhide with legs) / 1130 C (squared timbers, parchment): a sheet laced into a frame.
    Parts Pole_L, Pole_R, Bar_Top, Bar_Bottom, Hide - the same as the original 4000 hide clip."""
    random.seed(seed)
    k = seed * 0.37
    M = mats("InfoTimber" if square else "Hut_Wood", "Hut_Cord", name)
    wood, cord, surf = M["InfoTimber" if square else "Hut_Wood"], M["Hut_Cord"], M[name]
    a, b = PAGE_W / 2 + 0.16, PAGE_H / 2 + 0.17
    edge = hide_edge(a, b, k, lobes=not square, p=SE if not square else 8.0)
    bb = extent(edge)
    write_surface(name, kind, bb)
    xmin, xmax, zmin, zmax = bb
    zc = ZC
    z_bot, z_top = zc + zmin - 0.08, zc + zmax + 0.08
    px = max(-xmin, xmax) + 0.10
    top = z_top + 0.25
    r = 0.06 if square else 0.05
    bar_y = -(2 * r + 0.01) if square else -0.09

    def pole(side):
        def fill(bm, uv):
            if square:
                box(bm, uv, (side * px, 0, (top - 0.3) / 2), (2 * r, 2 * r, top + 0.3), 0, long="z")
            else:
                pts = wobble_path(Vector((side * px, 0, -0.3)), Vector((side * px + 0.03 * n3(seed, side, 1), 0.01, top)),
                                  14, 0.012, seed + side)
                tube(bm, uv, pts, [r * (1 - 0.2 * i / (len(pts) - 1)) for i in range(len(pts))], 0, sides=8)
        return fill

    def bar(z):
        def fill(bm, uv):
            if square:
                box(bm, uv, (0, bar_y, z), (2 * px + 0.32, 0.1, 0.1), 0, long="x")
            else:
                pts = wobble_path(Vector((-px - 0.16, bar_y, z)), Vector((px + 0.16, bar_y, z + 0.02)), 10, 0.01, seed + z)
                tube(bm, uv, pts, [0.04 * (1 - 0.15 * i / (len(pts) - 1)) for i in range(len(pts))], 0, sides=8)
            for s in (-1, 1):
                for ax in (Vector((1, 0, 1)), Vector((1, 0, -1))):
                    lashing(bm, uv, Vector((s * px, bar_y / 2, z)), ax, r + 0.035, 1, turns=3, height=0.05)
        return fill

    def hide(bm, uv):
        solid(bm, sheet(bm, uv, edge, zc, bb, belly=0.006, rough=0.003, k=k), 0.006)
        lacing(bm, uv, edge, zc, 0.0,
               lambda x, z: [(Vector((-px, 0, z + 0.02)), x + px), (Vector((px, 0, z + 0.02)), px - x),
                             (Vector((x * 1.02, bar_y, z_top)), z_top - z), (Vector((x * 1.02, bar_y, z_bot)), z - z_bot)],
               max(16, int(2.2 * (a + b) * 2 / 0.22)), 1)

    part("Pole_L", Vector((-px, 0, 0)), [wood], pole(-1))
    part("Pole_R", Vector((px, 0, 0)), [wood], pole(1))
    part("Bar_Top", Vector((0, bar_y, z_top)), [wood, cord], bar(z_top))
    part("Bar_Bottom", Vector((0, bar_y, z_bot)), [wood, cord], bar(z_bot))
    loc = Vector((0, 0, zc + zmax))
    page(part("Hide", loc, [surf, cord], hide), loc, (0, -0.012, zc))


def drying_rack(name, seed):
    """4000 B: a hide hanging from the crossbar of a leaning rack. Parts Rack (tips up), Hide (unrolls)."""
    random.seed(seed)
    k = seed * 0.37
    M = mats("Hut_Wood", "Hut_Cord", name)
    a, b = PAGE_W / 2 + 0.16, PAGE_H / 2 + 0.17
    edge = hide_edge(a, b, k)
    bb = extent(edge)
    write_surface(name, "rawhide", bb)
    xmin, xmax, zmin, zmax = bb
    zc = ZC
    z_bar = zc + zmax + 0.06
    px = max(-xmin, xmax) + 0.14
    y_bar, y_hide = 0.15, 0.10

    def rack(bm, uv):
        for s in (-1, 1):
            for foot, head in (((-0.3, -0.2), (0.22, z_bar + 0.3)), ((0.95, -0.2), (0.08, z_bar + 0.3))):
                pts = wobble_path(Vector((s * px, foot[0], foot[1])), Vector((s * px, head[0], head[1])), 12, 0.012,
                                  seed + s + foot[0])
                tube(bm, uv, pts, [0.05 * (1 - 0.2 * i / (len(pts) - 1)) for i in range(len(pts))], 0, sides=8)
            lashing(bm, uv, Vector((s * px, y_bar, z_bar)), Vector((1, 0, 0)), 0.09, 1, turns=4, height=0.08)
        pts = wobble_path(Vector((-px - 0.25, y_bar, z_bar)), Vector((px + 0.25, y_bar, z_bar + 0.02)), 10, 0.01, seed)
        tube(bm, uv, pts, [0.045] * len(pts), 0, sides=8)

    def hide(bm, uv):
        solid(bm, sheet(bm, uv, edge, zc, bb, y0=y_hide, belly=0.006, rough=0.003, k=k), 0.006)
        z_low = zc + zmin + 0.06                                   # weight stick along the bottom edge
        tube(bm, uv, wobble_path(Vector((-a * 0.85, y_hide - 0.03, z_low)), Vector((a * 0.85, y_hide - 0.03, z_low)),
                                 8, 0.01, seed + 3), [0.03] * 9, 2, sides=6)
        for i in range(9):                                         # tied up to the crossbar
            x = -a * 0.8 + i * a * 0.2
            _, ze = edge(math.atan2(1, x / a))
            hole = Vector((x, y_hide - 0.008, zc + ze * 0.93))
            tube(bm, uv, [hole, Vector((x, y_bar - 0.05, z_bar + 0.04)), Vector((x, y_bar + 0.05, z_bar))],
                 [0.005] * 3, 1, sides=4, tile=0.3)

    part("Rack", Vector((0, 0.95, 0)), [M["Hut_Wood"], M["Hut_Cord"]], rack)
    loc = Vector((0, y_hide, z_bar))
    page(part("Hide", loc, [M[name], M["Hut_Cord"], M["Hut_Wood"]], hide), loc, (0, y_hide - 0.012, zc))


def slab(name, seed, kind, a, b_top, b_bot, p_top, p_bot, thick, rough, band=False):
    """4000 C (painted field stone) / 1130 A (runestone): a stone pushing up out of the ground. Part Slab."""
    k = seed * 0.37
    M = mats(name)
    edge = stone_edge(a, b_top, b_bot, p_top, p_bot, k, rough)
    bb = extent(edge)

    def runes(base, xs, zs):
        """A red-painted band just inside the stone's edge, broken into rune-like strokes."""
        X, Z = np.meshgrid(xs, zs)
        top = Z > 0
        p = np.where(top, p_top, p_bot)
        bz = np.where(top, b_top, b_bot)
        r = (np.abs(X / a) ** p + np.abs(Z / bz) ** p) ** (1 / p)
        th = np.arctan2(Z / bz, X / a)
        inband = (r > 0.865) & (r < 0.925) & (Z > -PAGE_H / 2 - 0.1)
        edge_line = inband & ((r < 0.872) | (r > 0.918))
        stroke = inband & (np.mod(th * 70 / math.pi, 1.0) < 0.22) & (np.mod(th * 7 / math.pi, 1.0) > 0.08)
        base[inband] = base[inband] * 0.35 + np.array((0.55, 0.13, 0.07)) * 0.65
        base[edge_line | stroke] = base[edge_line | stroke] * 0.3 + np.array((0.08, 0.05, 0.04)) * 0.7

    write_surface(name, kind, bb, paint=runes if band else None)

    def fill(bm, uv):
        faces = sheet(bm, uv, edge, ZC, bb, rough=0.004, k=k, NA=144, NR=24)
        for v in solid(bm, faces, thick):                         # round the back
            u = (v.co.x / a) ** 2 + ((v.co.z - ZC) / max(b_top, b_bot)) ** 2
            v.co.y += thick * 0.6 * max(0.0, 1 - u)
    loc = Vector((0, 0, 0))
    page(part("Slab", loc, [M[name]], fill), loc, (0, -0.015, ZC))


def board_on_posts(name, seed, notice):
    """1130 B (carved oak board) / 1620 A (notice board with a roof and a nailed proclamation).
    Parts Post_L, Post_R (hammered in), Board (drops on) and, for the notice, Paper (unrolls)."""
    random.seed(seed)
    k = seed * 0.37
    M = mats("InfoTimber", "InfoIron", name)
    bw, bh, bt = PAGE_W + 0.5, PAGE_H + 0.45, 0.07
    front = (-bw / 2, bw / 2, -bh / 2, bh / 2)
    if notice:
        paper_edge = hide_edge(PAGE_W / 2 + 0.09, PAGE_H / 2 + 0.1, k, lobes=False, p=30.0)
        pbb = extent(paper_edge)
        write_surface(name, "paper", pbb, lighten=False)
    else:
        write_surface(name, "oak", front)
    zc = ZC
    top = zc + bh / 2 + (0.45 if notice else 0.25)
    xp = bw / 2 - 0.3

    def post(side):
        def fill(bm, uv):
            box(bm, uv, (side * xp, bt / 2 + 0.08, (top - 1.0) / 2), (0.16, 0.16, top + 1.0), 0, long="z")
        return fill

    def board(bm, uv):
        box(bm, uv, (0, 0, zc), (bw, bt, bh), 0, front=None if notice else (2, (front[0], front[1], zc + front[2], zc + front[3])))
        if notice:                                                 # sloping roof plank over the board
            box(bm, uv, (0, -0.12, zc + bh / 2 + 0.14), (bw + 0.3, 0.55, 0.035), 0, rot=(math.radians(22), "X"))
        else:                                                      # carved edging: a raised border with bosses
            y = -bt / 2 - 0.015
            for c, s in (((0, y, zc + bh / 2 - 0.05), (bw, 0.03, 0.1)), ((0, y, zc - bh / 2 + 0.05), (bw, 0.03, 0.1)),
                         ((-bw / 2 + 0.05, y, zc), (0.1, 0.03, bh - 0.2)), ((bw / 2 - 0.05, y, zc), (0.1, 0.03, bh - 0.2))):
                box(bm, uv, c, s, 0, long="x" if s[0] > s[2] else "z")
            n = int(bw / 0.25)
            for i in range(n + 1):
                for z in (zc + bh / 2 - 0.05, zc - bh / 2 + 0.05):
                    box(bm, uv, (-bw / 2 + 0.05 + i * (bw - 0.1) / n, y - 0.025, z), (0.05, 0.02, 0.05), 0)

    part("Post_L", Vector((-xp, 0, 0)), [M["InfoTimber"]], post(-1))
    part("Post_R", Vector((xp, 0, 0)), [M["InfoTimber"]], post(1))
    loc = Vector((0, 0, zc))
    board_ob = part("Board", loc, [M["InfoTimber"], M["InfoIron"], M[name]], board)
    if not notice:
        page(board_ob, loc, (0, -bt / 2 - 0.004, zc))
        return
    y0 = -bt / 2 - 0.004

    def paper(bm, uv):
        solid(bm, sheet(bm, uv, paper_edge, zc, pbb, y0=y0, rough=0.004, k=k), 0.002)
        for x, z in ((pbb[0] + 0.06, pbb[3] - 0.06), (pbb[1] - 0.06, pbb[3] - 0.06), (0, pbb[3] - 0.05),
                     (pbb[0] + 0.06, pbb[2] + 0.06), (pbb[1] - 0.06, pbb[2] + 0.06)):
            tube(bm, uv, [Vector((x, y0 - 0.012, zc + z)), Vector((x, y0 + 0.03, zc + z))], [0.012, 0.006], 1, sides=8)
    loc = Vector((0, y0, zc + pbb[3]))
    page(part("Paper", loc, [M[name], M["InfoIron"]], paper), loc, (0, y0 - 0.008, zc))


def hanging_sign(name, seed):
    """1620 B: a painted signboard hanging from an iron-braced gallows. Parts Gallows (drops in), Sign (swings in)."""
    M = mats("InfoTimber", "InfoIron", name)
    sw, sh, st = PAGE_W + 0.36, PAGE_H + 0.36, 0.05
    front = (-sw / 2, sw / 2, -sh / 2, sh / 2)

    def border(base, xs, zs):
        X, Z = np.meshgrid(xs, zs)
        inner = (np.abs(X) < PAGE_W / 2 + 0.06) & (np.abs(Z) < PAGE_H / 2 + 0.06)
        line = (np.abs(X) < PAGE_W / 2 + 0.085) & (np.abs(Z) < PAGE_H / 2 + 0.085) & ~inner
        base[~inner] = np.array((0.36, 0.08, 0.06))                # oxblood frame
        base[line] = np.array((0.72, 0.56, 0.22))                  # ochre-gold pinstripe
    write_surface(name, "painted", front, lighten=False, paint=border)
    zc = ZC
    z_arm = zc + sh / 2 + 0.32
    x_post = -(sw / 2 + 0.45)

    def gallows(bm, uv):
        box(bm, uv, (x_post, 0, (z_arm + 0.25 - 1.0) / 2), (0.2, 0.2, z_arm + 1.25), 0, long="z")
        x_end = sw / 2 + 0.25
        box(bm, uv, ((x_post + x_end) / 2, 0, z_arm), (x_end - x_post, 0.14, 0.14), 0, long="x")
        tube(bm, uv, [Vector((x_post + 0.1, 0, z_arm - 0.8)), Vector((x_post + 0.5, 0, z_arm - 0.35)),
                      Vector((x_post + 0.9, 0, z_arm - 0.07))], [0.02] * 3, 1, sides=6)

    def sign(bm, uv):
        box(bm, uv, (0, 0, zc), (sw, st, sh), 0, front=(2, (front[0], front[1], zc + front[2], zc + front[3])))
        for s in (-1, 1):
            x = s * (sw / 2 - 0.25)
            tube(bm, uv, [Vector((x, 0, zc + sh / 2)), Vector((x, 0, z_arm - 0.08))], [0.012] * 2, 1, sides=6)
            lashing(bm, uv, Vector((x, 0, z_arm)), Vector((1, 0, 0)), 0.08, 1, turns=1, height=0.01)
    part("Gallows", Vector((0, 0, 0)), [M["InfoTimber"], M["InfoIron"]], gallows)
    loc = Vector((0, 0, z_arm))
    page(part("Sign", loc, [M["InfoTimber"], M["InfoIron"], M[name]], sign), loc, (0, -st / 2 - 0.004, zc))


def scroll_stand(name, seed):
    """1620 C: a sealed scroll hanging from a turned wooden stand. Parts Stand (drops in), Scroll (unrolls)."""
    k = seed * 0.37
    M = mats("InfoTimber", "InfoWax", name)
    pw, ph = PAGE_W + 0.24, PAGE_H + 0.34
    edge = hide_edge(pw / 2, ph / 2, k, lobes=False, p=30.0)
    bb = extent(edge)
    write_surface(name, "parchment", bb, lighten=False)
    zc = ZC
    z_rod = zc + bb[3] + 0.07
    xs = pw / 2 + 0.22

    def stand(bm, uv):
        for s in (-1, 1):
            zs = [-0.02, 0.1, 0.3, 0.38, z_rod - 0.25, z_rod - 0.17, z_rod + 0.12, z_rod + 0.2, z_rod + 0.24]
            rs = [0.07, 0.06, 0.045, 0.06, 0.045, 0.06, 0.05, 0.065, 0.02]
            tube(bm, uv, [Vector((s * xs, 0, z)) for z in zs], rs, 0, sides=12)
            box(bm, uv, (s * xs, 0, 0.04), (0.12, 0.7, 0.08), 0, long="y")
        tube(bm, uv, [Vector((-xs, 0, z_rod)), Vector((xs, 0, z_rod))], [0.03, 0.03], 0, sides=10)
        tube(bm, uv, [Vector((-pw / 2 - 0.07, -0.04, z_rod - 0.06)), Vector((pw / 2 + 0.07, -0.04, z_rod - 0.06))],
             [0.045, 0.045], 0, sides=12)

    def scroll(bm, uv):
        solid(bm, sheet(bm, uv, edge, zc, bb, y0=-0.06, rough=0.004, k=k), 0.002)
        zb = zc + bb[2] - 0.03
        tube(bm, uv, [Vector((-pw / 2 - 0.06, -0.06, zb)), Vector((pw / 2 + 0.06, -0.06, zb))], [0.04, 0.04], 1, sides=12)
        zs = zc + bb[2] + 0.1                                      # the seal on its ribbon
        tube(bm, uv, [Vector((0, -0.064, zs)), Vector((0, -0.085, zs))], [0.065, 0.06], 2, sides=16)
        for dx in (-0.03, 0.03):
            box(bm, uv, (dx, -0.066, zs - 0.12), (0.035, 0.004, 0.22), 2, rot=(dx * 4, "Y"))
    part("Stand", Vector((0, 0, 0)), [M["InfoTimber"]], stand)
    loc = Vector((0, -0.06, z_rod - 0.1))
    page(part("Scroll", loc, [M[name], M["InfoTimber"], M["InfoWax"]], scroll), loc, (0, -0.072, zc))


PROPS = [("4000 A", lambda n: frame_sheet(n, 4000, "rawhide", square=False)),
         ("4000 B", lambda n: drying_rack(n, 4001)),
         ("4000 C", lambda n: slab(n, 4002, "fieldstone", PAGE_W / 2 + 0.35, PAGE_H / 2 + 0.3, ZC + 0.25, 4.0, 6.0,
                                   0.35, 0.025)),
         ("1130 A", lambda n: slab(n, 1130, "granite", PAGE_W / 2 + 0.45, PAGE_H / 2 + 0.55, ZC + 0.3, 2.8, 6.0,
                                   0.45, 0.02, band=True)),
         ("1130 B", lambda n: board_on_posts(n, 1131, notice=False)),
         ("1130 C", lambda n: frame_sheet(n, 1132, "parchment", square=True)),
         ("1620 A", lambda n: board_on_posts(n, 1620, notice=True)),
         ("1620 B", lambda n: hanging_sign(n, 1621)),
         ("1620 C", lambda n: scroll_stand(n, 1622))]


def export(name):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True,
                             object_types={"EMPTY", "MESH"}, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", path_mode="STRIP", bake_anim=False)
    print(name, "tris:", sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                             for o in bpy.data.objects if o.type == "MESH"))


if __name__ == "__main__":
    np.random.seed(707)
    random.seed(707)
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(PHOTOS, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for era, cards in CARD_FILES.items():
        for key, file in cards.items():
            save_png(card_photo(os.path.join(CARDS, file)), os.path.join(PHOTOS, "%s_%s.png" % (era, key)))
    col, nrm = tex_set("timber")                                   # shared tiling timber for posts and boards
    save_png(col, os.path.join(TEX, "InfoTimber_BaseColor.png"))
    save_png(nrm, os.path.join(TEX, "InfoTimber_Normal.png"))
    only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []   # e.g. -- "1130 A" to rebuild one
    for name, build in PROPS:
        if only and name not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)          # fresh file per prop, so material names stay exact
        build("InfoProp_" + name.replace(" ", "_"))
        export("Info Prop " + name)
