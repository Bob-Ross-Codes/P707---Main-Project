"""Builds the 4000 f.v.t. hut and exports it for Unity (version 2, after the museum photos).

Run:  /Applications/Blender.app/Contents/MacOS/Blender -b --python Tools/Blender/hut_4000.py
Writes Assets/3D Assets/4000 f.t.v/Hut 4000.fbx and its textures in Textures/.
Pass `-- preview` after the script path to also render check images to Captures/.
Blender axes: Z up, the door faces -Y. Units are metres.

Build-up, inside to outside (as in the reconstruction):
pole lattice (uprights, hoops, diagonal braces) -> reed lining ->
rawhide panels round the low wall, held by outside stakes -> whole furred hides over the dome.
Version 1 (bent saplings + plain hides) is kept as hut_4000_v1.py / Hut 4000 v1.fbx.
"""
import bpy, bmesh, math, random, os, sys
import numpy as np
from mathutils import Vector, noise

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Assets", "3D Assets", "4000 f.t.v")
TEX = os.path.join(OUT, "Textures")
STICK = os.path.join(ROOT, "Assets", "3D Assets", "STICK 1",
                     "Military_Trenches_Equipment_Stick_Wood_S_04_xfekfgv_Low_1K_")
PREVIEW = "preview" in sys.argv
random.seed(4001)
np.random.seed(4001)

# ---------------------------------------------------------------- shape
R_X, R_Y, H = 2.05, 1.95, 2.35   # footprint radii and height
WALL_H = 0.95                    # low near-vertical wall, then the dome
TW = 0.32                        # share of the profile parameter t used by the wall
T_TOP = 0.955                    # frame and lining stop here: smoke hole
LEAN = Vector((0.06, 0.04, 0.0))
DOOR_TH = -math.pi / 2           # door faces -Y
DOOR_HALF_M = 0.34               # half the door width, metres
DOOR_H = 1.65
ARC_WALL, ARC_DOME = 2.97, 3.9   # metres of surface per unit of t


def n3(x, y, z):
    return noise.noise(Vector((x, y, z)))


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def base_radius(th):
    ell = R_X * R_Y / math.sqrt((R_Y * math.cos(th)) ** 2 + (R_X * math.sin(th)) ** 2)
    return ell * (1 + 0.05 * n3(math.cos(th) * 1.4, math.sin(th) * 1.4, 7.1))


def prof(t):
    """(radius factor, height) along the profile; t < 0 goes into the ground."""
    if t <= TW:
        z = t / TW * WALL_H
        return 1.0 - 0.04 * max(z, 0) / WALL_H, z
    a = min((t - TW) / (1 - TW), 1.0) * math.pi / 2
    return 0.96 * math.cos(a) ** 0.8, WALL_H + (H - WALL_H) * math.sin(a)


def z_to_t(z):
    if z <= WALL_H:
        return z / WALL_H * TW
    return TW + math.asin(min((z - WALL_H) / (H - WALL_H), 1)) * 2 / math.pi * (1 - TW)


def dome(th, t):
    rf, z = prof(t)
    r = base_radius(th) * rf * (1 + 0.03 * n3(math.cos(th) * 2, math.sin(th) * 2, z))
    if z > WALL_H:
        z *= 1 + 0.04 * n3(math.cos(th) * 0.9, math.sin(th) * 0.9, 3.3)
    return Vector((r * math.cos(th), r * math.sin(th), z)) + LEAN * (max(z, 0) / H) ** 2


def dome_normal(th, t):
    e = 1e-3
    a = dome(th + e, t) - dome(th - e, t)
    b = dome(th, t + e) - dome(th, t - e)
    n = a.cross(b).normalized()
    p = dome(th, t)
    if n.dot(Vector((p.x, p.y, 0)) + Vector((0, 0, 0.3))) < 0:
        n = -n
    return n


def surf(th, t, off):
    return dome(th, t) + dome_normal(th, t) * off


def hrad(th, t):
    p = dome(th, t)
    return max(Vector((p.x, p.y)).length, 0.3)


def door_half_m(z):
    """Half width of the opening at height z: straight sides, rounded top."""
    if z >= DOOR_H:
        return 0.0
    zz = max(0.0, (z - (DOOR_H - 0.3)) / 0.3)
    return DOOR_HALF_M * math.sqrt(1 - zz * zz)


def door_half_ang(t):
    return door_half_m(dome(DOOR_TH, t).z) / hrad(DOOR_TH, t)


def in_door(th, z, margin=0.0):
    return abs(angdiff(th, DOOR_TH)) * hrad(DOOR_TH, z_to_t(z)) < door_half_m(z) + margin


# ---------------------------------------------------------------- mesh helpers
def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def tube(bm, uv, pts, radii, mat=0, sides=6, tile=0.9):
    """Pipe along pts. Bark texture U runs along the length, V around."""
    n = len(pts)
    tans = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    nrm = tans[0].orthogonal().normalized()
    rings, length, u0 = [], 0.0, random.random()
    for i in range(n):
        t = tans[i]
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        if i:
            length += (pts[i] - pts[i - 1]).length
        rings.append([(bm.verts.new(pts[i] + (nrm * math.cos(a) + bi * math.sin(a)) * radii[i]),
                       (u0 + length / tile, k / sides))
                      for k, a in ((k, 2 * math.pi * k / sides) for k in range(sides + 1))])
    for i in range(n - 1):
        for k in range(sides):
            vs = [rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]]
            f = bm.faces.new([v[0] for v in vs])
            f.material_index = mat
            for loop, v in zip(f.loops, vs):
                loop[uv].uv = v[1]
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        vs = ring[:-1][::-1] if flip else ring[:-1]
        f = bm.faces.new([v[0] for v in vs])
        f.material_index = mat
        for loop, v in zip(f.loops, vs):
            loop[uv].uv = (0.5 + 0.03 * math.cos(2 * math.pi * v[1][1]), 0.5 + 0.2 * math.sin(2 * math.pi * v[1][1]))


def wobble_path(a, b, steps, amp, seed):
    """Not-quite-straight pole from a to b."""
    pts = []
    side = (b - a).orthogonal().normalized()
    up = (b - a).cross(side).normalized()
    for i in range(steps + 1):
        t = i / steps
        bow = math.sin(math.pi * t)
        p = a.lerp(b, t) + side * amp * bow * n3(seed, 1.1, 0) * 2 + up * amp * bow * n3(seed, 2.3, 1)
        p += Vector((n3(seed, t * 4, 3), n3(seed, t * 4, 4), n3(seed, t * 4, 5))) * amp * 0.25
        pts.append(p)
    return pts


def lashing(bm, uv, centre, axis, r, mat, turns=4, height=0.06):
    """A few turns of cord wrapped round a pole."""
    axis = axis.normalized()
    x = axis.orthogonal().normalized()
    y = axis.cross(x)
    steps = turns * 8
    pts = [centre + axis * (height * (i / steps - 0.5)) +
           (x * math.cos(2 * math.pi * i / 8) + y * math.sin(2 * math.pi * i / 8)) * (r + 0.006)
           for i in range(steps + 1)]
    tube(bm, uv, pts, [0.006] * len(pts), mat=mat, sides=4, tile=0.3)


# ---------------------------------------------------------------- materials
def material(name, color, img=None, nrm=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, 1)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.85
    if img:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(img, check_existing=True)
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if nrm:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(nrm, check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ---------------------------------------------------------------- textures
def save_png(arr, path):
    h, w, _ = arr.shape
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(arr, 0, 1)
    img = bpy.data.images.new(os.path.basename(path), w, h)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def fbm(size, beta, aniso=1.0):
    """Tileable 1/f^beta noise in [0,1]; aniso > 1 stretches it along x, < 1 along y."""
    w = np.random.randn(size, size)
    fx = np.fft.fftfreq(size)[None, :] * aniso
    fy = np.fft.fftfreq(size)[:, None]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    out = np.real(np.fft.ifft2(np.fft.fft2(w) / f ** beta))
    out -= out.min()
    return out / out.max()


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    n = np.stack([-dx, -dy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def mix(a, b, t):
    return np.array(a) * (1 - t[..., None]) + np.array(b) * t[..., None]


def make_fur_textures():
    """Laid out for the hide UVs: U = angle round the hide (tiles), V = 0 at the spine centre, 1 at the edge."""
    s = 1024
    v = np.linspace(0, 1, s)[:, None] * np.ones((1, s))
    hair = fbm(s, 0.8, aniso=0.15)       # strands running along V, out from the spine
    blotch = fbm(s, 1.5)
    col = mix((0.40, 0.27, 0.16), (0.62, 0.47, 0.31), np.clip(v * 1.1 + (blotch - 0.5) * 0.6, 0, 1))
    belly = np.clip((v - 0.55 + (fbm(s, 1.3) - 0.5) * 0.5) * 3, 0, 1)        # pale flanks
    col = mix(col, (0.80, 0.72, 0.58), belly * 0.7)
    rim = np.clip((v - 0.86 + (fbm(s, 1.2) - 0.5) * 0.12) * 12, 0, 1)        # flesh side shows at the edge
    col = mix(col, (0.86, 0.80, 0.68), rim)
    col *= (0.78 + 0.4 * hair)[..., None]
    save_png(col, os.path.join(TEX, "Hut_Fur_BaseColor.png"))
    save_png(normal_from_height(hair * (1 - rim) + blotch * 0.3, 9.0), os.path.join(TEX, "Hut_Fur_Normal.png"))


def make_rawhide_textures():
    s = 1024
    low, mid = fbm(s, 1.7), fbm(s, 1.1)
    veins = np.abs(fbm(s, 1.3) - 0.5) < 0.012
    col = mix((0.83, 0.64, 0.33), (0.62, 0.43, 0.20), np.clip(low * 1.2 - 0.3 + mid * 0.3, 0, 1))
    stain = np.clip((fbm(s, 1.4) - 0.6) * 4, 0, 1)
    col *= (1 - 0.3 * stain)[..., None]
    col *= (1 - 0.12 * veins)[..., None]
    save_png(col, os.path.join(TEX, "Hut_Rawhide_BaseColor.png"))
    save_png(normal_from_height(mid * 0.6 + fbm(s, 1.0, aniso=3.0) * 0.4, 5.0),
             os.path.join(TEX, "Hut_Rawhide_Normal.png"))


def make_reed_textures():
    """Vertical reed stalks."""
    s = 1024
    w = 8  # px per stalk, ~6 mm
    cols = np.repeat(np.random.rand(s // w), w)[None, :] * np.ones((s, 1))
    edge = (np.arange(s) % w == 0)[None, :] * np.ones((s, 1))
    stalks = np.clip(cols * 0.6 + fbm(s, 1.2, aniso=0.05) * 0.3 + 0.1 - 0.3 * edge, 0, 1)
    low = fbm(s, 1.6)
    col = mix((0.47, 0.35, 0.19), (0.80, 0.67, 0.42), np.clip(stalks * 1.3 - 0.15 + (low - 0.5) * 0.4, 0, 1))
    save_png(col, os.path.join(TEX, "Hut_Reed_BaseColor.png"))
    save_png(normal_from_height(stalks, 14.0), os.path.join(TEX, "Hut_Reed_Normal.png"))


def make_bark_textures():
    """Clean bark strip from the STICK 1 atlas, made to tile both ways."""
    for kind in ("BaseColor", "Normal"):
        img = bpy.data.images.load(STICK + kind + ".jpg")
        w, h = img.size
        px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[..., :3]
        bpy.data.images.remove(img)
        # rows 545..745 / cols 100..820 from the top of the 1024 image (pixels[] is bottom-up)
        crop = px[h - 745:h - 545, 100:820]
        ox, oy = 120, 40
        a = np.linspace(0, 1, ox)[None, :, None]
        tiled = crop[:, :-ox].copy()
        tiled[:, :ox] = crop[:, :ox] * a + crop[:, -ox:] * (1 - a)
        b = np.linspace(0, 1, oy)[:, None, None]
        out = tiled[:-oy].copy()
        out[:oy] = tiled[:oy] * b + tiled[-oy:] * (1 - b)
        save_png(out, os.path.join(TEX, "Hut_Bark_" + kind + ".png"))


# ---------------------------------------------------------------- parts
WOOD, CORD, REED, RAW, FUR, FUR2 = range(6)


def build_lattice(bm, uv):
    # uprights, bent in over the dome; the ones over the door start above it
    n_up = 22
    for i in range(n_up):
        a = DOOR_TH + (i + 0.5) * 2 * math.pi / n_up + random.uniform(-0.07, 0.07)
        t0 = -0.03 if not in_door(a, 0.5, 0.1) else z_to_t(DOOR_H + 0.05)
        ts = np.linspace(t0, T_TOP + 0.01, 28)
        pts = [surf(a + 0.05 * n3(i * 2.3, t * 2, 0), t, -0.03) for t in ts]
        last = pts[-1]
        out = Vector((last.x - LEAN.x, last.y - LEAN.y, 0)).normalized()
        d = (Vector((0, 0, 1)) + out * 0.4).normalized()
        pts += [last + d * random.uniform(0.08, 0.22) * k / 3 for k in (1, 2, 3)]
        r0 = random.uniform(0.024, 0.034)
        tube(bm, uv, pts, [r0 * (1 - 0.5 * k / (len(pts) - 1)) for k in range(len(pts))], WOOD)
    # hoops every ~35 cm, tied off at the door posts below the door top
    for k, z0 in enumerate((0.32, 0.66, 1.0, 1.34, 1.66, 1.95, 2.18)):
        closed = z0 > DOOR_H
        t = z_to_t(z0)
        da = 0 if closed else (DOOR_HALF_M + 0.03) / hrad(DOOR_TH, t)
        steps = 90
        pts = []
        for s in range(steps + 1):
            th = DOOR_TH + da + (2 * math.pi - 2 * da) * s / steps
            z = z0 + 0.06 * n3(k * 4.1, th * 1.5, 0)
            pts.append(surf(th, z_to_t(z), -0.065))
        if closed:
            pts[-1] = pts[0]
        tube(bm, uv, pts, [0.018] * len(pts), WOOD, sides=5)
    # diagonal braces across the wall, crossing each other
    for k in range(18):
        a = DOOR_TH + 0.5 + k * (2 * math.pi - 1.0) / 18 + random.uniform(-0.1, 0.1)
        sweep = random.choice((-1, 1)) * random.uniform(0.5, 0.8)
        if any(in_door(a + sweep * s, 0.4, 0.15) for s in np.linspace(0, 1, 12)):
            continue
        t1 = random.uniform(0.45, 0.75)
        pts = [surf(a + sweep * s, -0.02 + t1 * s, -0.048) for s in np.linspace(0, 1, 16)]
        tube(bm, uv, pts, [0.017] * len(pts), WOOD, sides=5)


def build_door(bm, uv):
    """One bent sapling framing the opening, with thin sticks bundled beside the posts."""
    pts = []
    for s in np.linspace(-1, 1, 41):
        side = -1 if s < 0 else 1
        u = abs(s)
        if u > 0.5:   # posts: from the ground up to where the arch starts
            z = (DOOR_H - 0.3) * (1 - (u - 0.5) / 0.5) - 0.05 * ((u - 0.5) / 0.5)
            x = side * (DOOR_HALF_M + 0.03)
        else:          # rounded top
            ang = u / 0.5 * math.pi / 2
            x = side * (DOOR_HALF_M + 0.03) * math.sin(ang)
            z = DOOR_H - 0.3 + 0.33 * math.cos(ang)
        t = z_to_t(z)
        pts.append(surf(DOOR_TH + x / hrad(DOOR_TH, t), t, 0.07) + Vector((0, 0, 0.004 * n3(s * 5, 1, 1))))
    tube(bm, uv, pts, [0.042] * len(pts), WOOD, sides=7)
    for side in (-1, 1):
        for j in range(4):
            x = side * (DOOR_HALF_M + 0.08 + 0.03 * j)
            top = random.uniform(1.0, 1.55)
            a = surf(DOOR_TH + x / hrad(DOOR_TH, 0.1), -0.01, 0.09 + 0.012 * j)
            b = surf(DOOR_TH + (x + side * random.uniform(-0.04, 0.06)) / hrad(DOOR_TH, z_to_t(top)),
                     z_to_t(top), 0.09 + 0.012 * j)
            p = wobble_path(a, b, 8, 0.015, 60 + j + side * 10)
            tube(bm, uv, p, [0.012] * len(p), WOOD, sides=4)
        for z in (0.35, 1.0):
            t = z_to_t(z)
            c = surf(DOOR_TH + side * (DOOR_HALF_M + 0.07) / hrad(DOOR_TH, t), t, 0.08)
            lashing(bm, uv, c, Vector((0, 0, 1)), 0.06, CORD)


def build_lining(bm, uv):
    """Reed lining between the lattice and the hides; rows end at the door edges."""
    NT, NP = 96, 30
    grid = {}
    for j in range(NP + 1):
        t = -0.03 + (T_TOP + 0.03) * j / NP
        dh = door_half_ang(t)
        for i in range(NT + 1):
            th = DOOR_TH + dh + (2 * math.pi - 2 * dh) * i / NT
            uvc = ((th - DOOR_TH) * hrad(th, t) / 0.8, prof(t)[1] / 0.8)
            if dh == 0 and i == NT:
                grid[i, j] = (grid[0, j][0], uvc)
            else:
                grid[i, j] = (bm.verts.new(surf(th, t, 0.02 + 0.008 * noise.noise(dome(th, t) * 4))), uvc)
    for i in range(NT):
        for j in range(NP):
            q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
            if len({id(v[0]) for v in q}) < 4:
                continue
            f = bm.faces.new([v[0] for v in q])
            f.material_index = REED
            for loop, v in zip(f.loops, q):
                loop[uv].uv = v[1]


def build_wall(bm_panels, uvp, bm_wood, uvw):
    """Stiff rawhide panels round the low wall, held by stakes outside and tied on."""
    R = hrad(DOOR_TH, 0.15)
    a_start = DOOR_TH + (DOOR_HALF_M + 0.02) / R
    a_end = DOOR_TH + 2 * math.pi - (DOOR_HALF_M + 0.02) / R
    edges, a = [a_start], a_start
    while a < a_end - 0.5 / R:
        a += random.uniform(0.85, 1.25) / R
        edges.append(min(a, a_end))
    edges[-1] = a_end
    stakes = []
    for k in range(len(edges) - 1):
        a0 = edges[k] - (0.06 / R if k else 0)
        a1 = edges[k + 1]
        top = random.uniform(0.85, 1.0)
        cut = (random.uniform(0, 0.12), random.uniform(0, 0.12))   # trimmed-off corners
        NU, NV = 12, 9
        vs = {}
        off = 0.045 + 0.007 * (k % 2)
        uo = (random.random(), random.random())
        for i in range(NU + 1):
            for j in range(NV + 1):
                u, v = i / NU, j / NV
                ztop = top + 0.035 * n3(k * 3.3, u * 3, 0) - cut[0] * max(0, 1 - u * 6) - cut[1] * max(0, u * 6 - 5)
                z = -0.05 + (ztop + 0.05) * v
                th = a0 + (a1 - a0) * u
                t = z_to_t(z) if z > 0 else z / WALL_H * TW
                bulge = 0.024 * abs(math.sin(math.pi * u * 2)) * math.sin(math.pi * v) + 0.008 * n3(k, u * 5, v * 3)
                curl = 0.025 * max(0, v - 0.85) ** 2 / 0.0225
                vs[i, j] = (bm_panels.verts.new(surf(th, t, off + bulge + curl)),
                            (uo[0] + (th - a0) * R, uo[1] + z))
        for i in range(NU):
            for j in range(NV):
                q = [vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]]
                f = bm_panels.faces.new([x[0] for x in q])
                f.material_index = RAW
                for loop, x in zip(f.loops, q):
                    loop[uvp].uv = x[1]
        stakes.append((a0 + 0.04 / R, top))
        if random.random() < 0.5:
            stakes.append(((a0 + a1) / 2 + random.uniform(-0.1, 0.1) / R, top))
    stakes.append((a_end - 0.04 / R, top))
    for k, (a, top) in enumerate(stakes):
        if in_door(a, 0.5, 0.12):
            continue
        h = top + random.uniform(0.05, 0.3)
        lean = random.uniform(-0.04, 0.04)
        b = surf(a, -0.03, 0.085)
        e = surf(a + lean, z_to_t(h), 0.085)
        p = wobble_path(b + Vector((0, 0, -0.06)), e, 8, 0.012, 80 + k)
        tube(bm_wood, uvw, p, [random.uniform(0.016, 0.024)] * len(p), WOOD, sides=5)
        for z in (0.3, top - 0.12):
            c = b.lerp(e, (z + 0.06) / (h + 0.06))
            lashing(bm_wood, uvw, c, e - b, 0.02, CORD, turns=3)


def deer_outline(k, al, aspect):
    """Hide silhouette: long oval with four leg flaps, neck and tail; al = 0 points at the head."""
    e = 1 / math.sqrt(math.cos(al) ** 2 + (math.sin(al) / aspect) ** 2)
    for c, amp, w in ((0.65, 0.32, 0.13), (-0.65, 0.3, 0.12), (2.45, 0.34, 0.14), (-2.45, 0.3, 0.15),
                      (0.0, 0.16, 0.2), (math.pi, 0.09, 0.09)):
        e += amp * math.exp(-(angdiff(al, c) / w) ** 2)
    return e * (1 + 0.08 * n3(k * 9.0, math.cos(al) * 2, math.sin(al) * 2)
                + 0.03 * n3(k * 9.0, math.cos(al) * 7, math.sin(al) * 7))


def hide(bm, uv, k, thc, tc, half_len, rot, extra, mat, cap=False):
    """One whole furred hide laid over the dome. cap=True centres it on the crown, around the smoke hole."""
    NR, NA = 10, 36
    aspect = random.uniform(0.68, 0.82)
    uoff = random.random()

    def place(rho, al):
        e = deer_outline(k, al, aspect)
        d = rho * e * half_len
        x, y = d * math.sin(al + rot), d * math.cos(al + rot)
        if cap:
            th, t = math.atan2(x, y) + thc, 1 - math.hypot(x, y) / ARC_DOME
        else:
            t = tc + y / ARC_DOME
            if t < TW:
                t = TW + (t - TW) * ARC_DOME / ARC_WALL
            t = min(max(t, -0.02), 0.985)
            th = thc + x / hrad(thc, t)
        drape = 0.03 * max(0, rho - 0.6) ** 2 / 0.16
        p = surf(th, t, max(extra - drape, 0.058) + 0.006 * n3(k, x * 3, y * 3))
        return p, th

    centre, _ = place(0, 0)
    centre = bm.verts.new(centre)
    ring_v = []
    for r in range(1, NR + 1):
        rho = r / NR
        row = []
        for m in range(NA):
            p, th = place(rho, 2 * math.pi * m / NA)
            row.append((bm.verts.new(p), th))
        ring_v.append(row)

    def uvat(r, m):
        return (uoff + 2 * m / NA, 0.97 * r / NR)

    def keep(vs, ths):
        z = sum(v.co.z for v in vs) / len(vs)
        if cap and min(Vector((v.co.x, v.co.y)).length for v in vs) < 0.24:
            return False   # leave the smoke hole open
        return not in_door(ths[0], z, 0.03)

    for m in range(NA):
        m2 = (m + 1) % NA
        r0 = ring_v[0]
        if keep([centre, r0[m][0], r0[m2][0]], [r0[m][1]]):
            f = bm.faces.new([centre, r0[m][0], r0[m2][0]])
            f.material_index = mat
            for loop, x in zip(f.loops, ((uoff + 2 * m / NA, 0), uvat(1, m), uvat(1, m + 1))):
                loop[uv].uv = x
        for r in range(NR - 1):
            a, b = ring_v[r], ring_v[r + 1]
            vs = [a[m][0], b[m][0], b[m2][0], a[m2][0]]
            if not keep(vs, [a[m][1]]):
                continue
            f = bm.faces.new(vs)
            f.material_index = mat
            for loop, x in zip(f.loops, (uvat(r + 1, m), uvat(r + 2, m), uvat(r + 2, m + 1), uvat(r + 1, m + 1))):
                loop[uv].uv = x


def build_hides(bm, uv):
    k = 0
    # lower ring: lower edges hang over the top of the rawhide wall
    n = 9
    for i in range(n):
        thc = DOOR_TH + (i + 0.5) * 2 * math.pi / n + random.uniform(-0.12, 0.12)
        hide(bm, uv, k, thc, random.uniform(0.47, 0.52), random.uniform(0.75, 0.88), random.uniform(-0.35, 0.35),
             0.068 + 0.005 * (i % 3), FUR2 if i % 3 == 1 else FUR)
        k += 1
    # upper ring, overlapping the lower one like shingles
    n = 7
    for i in range(n):
        thc = DOOR_TH + i * 2 * math.pi / n + random.uniform(-0.15, 0.15)
        hide(bm, uv, k, thc, random.uniform(0.72, 0.78), random.uniform(0.72, 0.85), random.uniform(-0.5, 0.5),
             0.085 + 0.005 * (i % 2), FUR2 if i == 2 else FUR)
        k += 1
    hide(bm, uv, k, random.uniform(0, 6.28), 1.0, 0.8, 0.0, 0.1, FUR, cap=True)


# ---------------------------------------------------------------- interior
# Furnishing after Ertebølle finds: hearth, fur beds on reed bedding, baskets, pointed-base pots,
# bows, a fish leister, pelts on the lattice, firewood. Exported as its own FBX so it can be toggled.
FLOOR = 0.17   # just above the terrain inside the hut (up to 0.156 m above the hut origin at the wall)
I_WOOD, I_CORD, I_REED, I_FUR, I_FUR2, I_STONE, I_EARTH, I_ASH, I_CHAR, I_CLAY, I_FLINT = range(11)


def make_ground_textures():
    s = 512
    for name, a, b, strength in (("Hut_Stone", (0.30, 0.30, 0.29), (0.62, 0.60, 0.56), 4.0),
                                 ("Hut_Earth", (0.24, 0.19, 0.14), (0.50, 0.43, 0.33), 3.0)):
        low, mid, fine = fbm(s, 1.6), fbm(s, 1.0), fbm(s, 0.5)
        col = mix(a, b, np.clip(low * 0.8 + mid * 0.5 - 0.3, 0, 1))
        col *= (0.85 + 0.3 * fine)[..., None]
        save_png(col, os.path.join(TEX, name + "_BaseColor.png"))
        save_png(normal_from_height(mid * 0.5 + fine * 0.5, strength), os.path.join(TEX, name + "_Normal.png"))


def at(deg, r, z=FLOOR):
    a = math.radians(deg)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def wall_limit(p, margin=0.1):
    return base_radius(math.atan2(p.y, p.x)) * 0.97 - margin


def set_uv(faces, uv, mat, scale=2.0):
    for f in faces:
        f.material_index = mat
        for loop in f.loops:
            q = loop.vert.co
            loop[uv].uv = ((q.x + q.y) * scale, q.z * scale + q.x)


def rock(bm, uv, c, size, flat=0.6, mat=I_STONE, bump=0.25):
    seed = random.uniform(0, 100)
    vs = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)["verts"]
    sx, sy, sz = size * random.uniform(0.8, 1.2), size * random.uniform(0.8, 1.2), size * flat
    rot = random.uniform(0, math.pi)
    for v in vs:
        d = v.co.copy()
        k = 1 + bump * noise.noise(d * 1.3 + Vector((seed, 0, 0)))
        x, y = d.x * sx * k, d.y * sy * k
        v.co = c + Vector((x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot), d.z * sz * k))
    set_uv({f for v in vs for f in v.link_faces}, uv, mat)


def lathe(bm, uv, c, prof, mat, axis=Vector((0, 0, 1)), segs=20, wobble=0.04, u_rep=1.0):
    """Revolve [(r, h)] round axis through c. Profile order sets the facing side."""
    up = axis.normalized()
    x = up.orthogonal().normalized()
    y = up.cross(x)
    seed = random.uniform(0, 100)
    rings = []
    for j, (r, h) in enumerate(prof):
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            rr = r * (1 + wobble * n3(seed, math.cos(a), math.sin(a) + j * 0.3))
            ring.append(bm.verts.new(c + up * h + (x * math.cos(a) + y * math.sin(a)) * rr))
        rings.append(ring)
    for j in range(len(prof) - 1):
        for i in range(segs):
            i2 = (i + 1) % segs
            f = bm.faces.new([rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]])
            f.material_index = mat
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (a / segs * u_rep, b / (len(prof) - 1))


def rug(bm, uv, k, c, half_len, rot, mat, mound=None, aspect=0.75):
    """A hide lying on the floor (or on a bedding mound); turns up where it meets the wall."""
    NR, NA = 9, 32
    uoff = random.random()

    def pos(rho, al):
        d = rho * deer_outline(k, al, aspect) * half_len
        p = c + Vector((d * math.sin(al + rot), d * math.cos(al + rot), 0))
        if mound:
            mc, ax, ay, mh = mound
            q = (p.x - mc.x) ** 2 / ax ** 2 + (p.y - mc.y) ** 2 / ay ** 2
            p.z += mh * max(0.0, 1 - q) ** 0.6
        p.z += 0.012 + 0.012 * n3(k, p.x * 3, p.y * 3) + 0.02 * max(0, rho - 0.8) ** 2 / 0.04
        lim = wall_limit(p, 0.12)
        r = Vector((p.x, p.y)).length
        if r > lim:   # fold up against the wall
            p.x, p.y, p.z = p.x * lim / r, p.y * lim / r, p.z + (r - lim)
        return p

    centre = bm.verts.new(pos(0, 0))
    rings = [[bm.verts.new(pos(r / NR, 2 * math.pi * m / NA)) for m in range(NA)] for r in range(1, NR + 1)]
    uvat = lambda r, m: (uoff + 2 * m / NA, 0.97 * r / NR)
    for m in range(NA):
        m2 = (m + 1) % NA
        f = bm.faces.new([centre, rings[0][m], rings[0][m2]])
        f.material_index = mat
        for loop, x in zip(f.loops, ((uoff + 2 * m / NA, 0), uvat(1, m), uvat(1, m + 1))):
            loop[uv].uv = x
        for r in range(NR - 1):
            f = bm.faces.new([rings[r][m], rings[r + 1][m], rings[r + 1][m2], rings[r][m2]])
            f.material_index = mat
            for loop, x in zip(f.loops, (uvat(r + 1, m), uvat(r + 2, m), uvat(r + 2, m + 1), uvat(r + 1, m + 1))):
                loop[uv].uv = x


def pelt(bm, uv, k, deg, z_top, half_len, mat):
    """A small pelt hung by its neck from the lattice, inside."""
    th = math.radians(deg)
    t = z_to_t(z_top - half_len)
    n = dome_normal(th, t)
    upv = (dome(th, t + 0.01) - dome(th, t - 0.01)).normalized()
    side = upv.cross(n).normalized()
    c = surf(th, t, -0.11)
    NU, NV = 10, 14
    vs = {}
    for i in range(NU + 1):
        for j in range(NV + 1):
            u, v = i / NU * 2 - 1, j / NV * 2 - 1
            al = math.atan2(u, v)
            e = deer_outline(k, al, 0.5)
            rr = math.hypot(u, v) / max(e, 0.01) if (u or v) else 0
            p = c + side * u * half_len * 0.5 + upv * v * half_len - n * (0.025 * math.sin(math.pi * (v + 1) / 2) * (1 - rr))
            vs[i, j] = (p, rr <= 1.0, (0.5 + u * 0.25, rr * 0.97))
    made = {}
    for i in range(NU):
        for j in range(NV):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if not all(vs[x][1] for x in q):
                continue
            for x in q:
                if x not in made:
                    made[x] = bm.verts.new(vs[x][0])
            f = bm.faces.new([made[x] for x in q])
            f.material_index = mat
            for loop, x in zip(f.loops, q):
                loop[uv].uv = vs[x][2]


def lean_pole(bm, uv, deg, z_top, length, r, seed, foot_in=0.22):
    """A pole standing on the floor near the wall with its top resting on the lattice."""
    th = math.radians(deg)
    top = surf(th, z_to_t(z_top), -0.1)
    foot = at(deg, Vector((top.x, top.y)).length - foot_in, FLOOR)
    d = (top - foot).normalized()
    end = foot + d * length
    pts = wobble_path(foot, end, 12, 0.01, seed)
    tube(bm, uv, pts, [r] * len(pts), I_WOOD, sides=6)
    return foot, end, d


def build_interior():
    make_ground_textures()
    tx = lambda n: (os.path.join(TEX, n + "_BaseColor.png"), os.path.join(TEX, n + "_Normal.png"))
    get = lambda name, *a: bpy.data.materials.get(name) or material(name, *a)
    mats = [get("Hut_Wood"), get("Hut_Cord"), get("Hut_Reed"), get("Hut_Fur"), get("Hut_Fur_Pale"),
            get("Hut_Stone", (0.45, 0.44, 0.42), *tx("Hut_Stone")),
            get("Hut_Earth", (0.36, 0.3, 0.23), *tx("Hut_Earth")),
            get("Hut_Ash", (0.55, 0.54, 0.52)),
            get("Hut_Charcoal", (0.05, 0.045, 0.04)),
            get("Hut_Clay", (0.30, 0.22, 0.16)),
            get("Hut_Flint", (0.16, 0.15, 0.15))]

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()

    # trampled earth floor, filling the hut to the reed lining
    NA, NR = 64, 8
    ctr = bm.verts.new(Vector((0, 0, FLOOR)))
    rings = []
    for r in range(1, NR + 1):
        row = []
        for m in range(NA):
            th = 2 * math.pi * m / NA
            rr = (hrad(th, z_to_t(FLOOR)) + 0.035) * r / NR   # reaches just under the rawhide panels
            row.append(bm.verts.new(Vector((rr * math.cos(th), rr * math.sin(th), FLOOR + 0.008 * n3(th * 3, r, 0)))))
        rings.append(row)
    rings.append([bm.verts.new(v.co - Vector((0, 0, 0.3))) for v in rings[-1]])   # earth edge dropping into the ground
    for m in range(NA):
        m2 = (m + 1) % NA
        fs = [bm.faces.new([ctr, rings[0][m], rings[0][m2]])]
        fs += [bm.faces.new([rings[r][m], rings[r][m2], rings[r + 1][m2], rings[r + 1][m]][::-1]) for r in range(NR)]
        set_uv(fs, uv, I_EARTH, 0.6)
    for f in bm.faces:   # top/down projection for the floor, side projection for its edge
        f.normal_update()
        side = abs(f.normal.z) < 0.5
        for loop in f.loops:
            q = loop.vert.co
            loop[uv].uv = ((q.x + q.y) * 0.6, q.z * 0.6) if side else (q.x * 0.6, q.y * 0.6)

    # hearth: stone ring, ash, burnt sticks
    hc = Vector((0.05, 0.15, FLOOR))
    for i in range(13):
        a = 2 * math.pi * i / 13 + random.uniform(-0.08, 0.08)
        rr = 0.38 + random.uniform(-0.06, 0.05)
        size = random.uniform(0.065, 0.14)
        rock(bm, uv, hc + Vector((rr * math.cos(a), rr * math.sin(a), size * 0.15)), size)
    lathe(bm, uv, hc, [(0.36, 0.0), (0.25, 0.018), (0.1, 0.028), (0.0, 0.03)], I_ASH, segs=24, wobble=0.1)
    for i in range(6):
        a = random.uniform(0, 2 * math.pi)
        p0 = hc + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), 0.045))
        p1 = hc + Vector((random.uniform(0.25, 0.42) * math.cos(a), random.uniform(0.25, 0.42) * math.sin(a), 0.03))
        pts = wobble_path(p0, p1, 6, 0.01, 90 + i)
        tube(bm, uv, pts, [0.018 * (0.6 + 0.4 * k / 6) for k in range(7)], I_CHAR, sides=5)
    for i in range(8):
        rock(bm, uv, hc + Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0.03)),
             random.uniform(0.015, 0.03), 0.5, I_CHAR, 0.4)

    # beds: reed bedding mounds with a fur on top
    soft = bmesh.new()
    suv = soft.loops.layers.uv.new()
    for k, (deg, r, rot, mat) in enumerate(((45, 1.15, 0.6, I_FUR), (150, 1.15, -0.5, I_FUR2))):
        mc = at(deg, r)
        ax, ay, mh = 0.6, 0.62, 0.12
        vs = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)["verts"]
        for v in vs:   # reed bedding, a bit wider than the furs on it
            d = v.co.copy()
            v.co = mc + Vector((d.x * ax * 1.12, d.y * ay * 1.12, d.z * mh * 0.95)) * (1 + 0.06 * noise.noise(d * 2 + Vector((k * 9, 0, 0))))
        set_uv({f for v in vs for f in v.link_faces}, uv, I_REED, 1.2)
        rug(soft, suv, 40 + k, mc, 0.72, rot + math.radians(deg) - math.pi / 2, mat, (mc, ax, ay, mh))
        rug(soft, suv, 50 + k, mc + Vector((0.1, -0.05, 0)), 0.55, rot + 2.6, I_FUR2 if mat == I_FUR else I_FUR,
            (mc, ax, ay, mh + 0.02))
    rug(soft, suv, 60, at(222, 1.2), 0.62, 0.9, I_FUR)
    for k, (deg, z) in enumerate(((122, 1.75), (188, 1.7))):
        pelt(soft, suv, 70 + k, deg, z, random.uniform(0.38, 0.45), I_FUR if k else I_FUR2)
    # rolled-up fur
    rc = at(192, 1.45, FLOOR + 0.1)
    axis = Vector((math.cos(math.radians(282)), math.sin(math.radians(282)), 0))
    lathe(bm, uv, rc - axis * 0.32, [(0.0, 0.0), (0.09, 0.0), (0.1, 0.02), (0.1, 0.62), (0.09, 0.64), (0.0, 0.64)],
          I_FUR, axis, segs=14, wobble=0.12, u_rep=2)

    # baskets
    for k, (deg, r, sc) in enumerate(((-20, 1.45, 1.0), (-5, 1.5, 0.75), (122, 1.5, 0.9))):
        c = at(deg, r)
        prof = [(0.0, 0.0), (0.17, 0.0), (0.19, 0.1), (0.21, 0.22), (0.22, 0.3), (0.205, 0.31),
                (0.2, 0.22), (0.18, 0.1), (0.16, 0.015), (0.0, 0.015)]
        lathe(bm, uv, c, [(a * sc, b * sc) for a, b in prof], I_REED, segs=24, wobble=0.05, u_rep=3)
        for h in (0.1, 0.2, 0.3):
            rr = (0.19 + 0.1 * (h - 0.1)) * sc + 0.004
            ring = [c + Vector((rr * math.cos(a), rr * math.sin(a), h * sc)) for a in np.linspace(0, 2 * math.pi, 25)]
            tube(bm, uv, ring, [0.008 * sc] * 25, I_CORD, sides=4)

    # pointed-base pots, one pushed into the floor by the hearth, one by the back wall
    pot = [(0.0, 0.0), (0.05, 0.03), (0.11, 0.1), (0.14, 0.2), (0.13, 0.3), (0.12, 0.36), (0.13, 0.4),
           (0.115, 0.405), (0.105, 0.36), (0.115, 0.3), (0.125, 0.2), (0.095, 0.1), (0.0, 0.05)]
    lathe(bm, uv, at(-15, 0.68, FLOOR - 0.06), pot, I_CLAY, Vector((0.08, 0.05, 1)), segs=22, wobble=0.03)
    lathe(bm, uv, at(95, 1.5, FLOOR - 0.05), [(a * 1.2, b * 1.2) for a, b in pot], I_CLAY,
          Vector((-0.05, -0.12, 1)), segs=22, wobble=0.03)
    # wooden bowl and a coil of cord by the hearth
    lathe(bm, uv, at(205, 0.62), [(0.0, 0.0), (0.09, 0.0), (0.14, 0.05), (0.15, 0.08), (0.14, 0.085),
                                    (0.125, 0.05), (0.08, 0.025), (0.0, 0.025)], I_WOOD, segs=20, wobble=0.04)
    cc = at(-40, 0.75, FLOOR + 0.008)
    coil = [cc + Vector(((0.03 + 0.012 * a / (2 * math.pi)) * math.cos(a), (0.03 + 0.012 * a / (2 * math.pi)) * math.sin(a),
                         0.004 * math.sin(a * 3))) for a in np.linspace(0, 2 * math.pi * 6, 180)]
    tube(bm, uv, coil, [0.006] * len(coil), I_CORD, sides=4)

    # stone slab seat
    rock(bm, uv, at(15, 1.35, FLOOR + 0.05), 0.28, 0.22, I_STONE, 0.15)

    # firewood stacked by the door
    fc = at(-58, 1.35)
    tang = Vector((-math.sin(math.radians(-58)), math.cos(math.radians(-58)), 0))
    outw = Vector((math.cos(math.radians(-58)), math.sin(math.radians(-58)), 0))
    for layer in range(3):
        for i in range(4 - layer):
            r = random.uniform(0.035, 0.05)
            c = fc + outw * ((i - (3 - layer) / 2) * 0.1) + Vector((0, 0, r + layer * 0.085))
            L = random.uniform(0.55, 0.85)
            d = (tang + outw * random.uniform(-0.1, 0.1)).normalized()
            pts = wobble_path(c - d * L / 2, c + d * L / 2, 6, 0.01, 100 + layer * 10 + i)
            tube(bm, uv, pts, [r] * len(pts), I_WOOD, sides=7)

    # bows, a three-pronged fish leister and a flint-tipped spear leaning on the back wall
    for k, deg in enumerate((70, 84)):
        foot, end, d = lean_pole(bm, uv, deg, 1.45, 0.02, 0.001, 200 + k)  # just to get the line
        side = d.cross(Vector((0, 0, 1))).normalized()
        L = 1.55
        pts = [foot + d * L * s + side * 0.1 * math.sin(math.pi * s) for s in np.linspace(0, 1, 25)]
        tube(bm, uv, pts, [0.009 + 0.008 * math.sin(math.pi * s) for s in np.linspace(0, 1, 25)], I_WOOD, sides=6)
        tube(bm, uv, [foot + d * 0.02, foot + d * (L - 0.02)], [0.0025, 0.0025], I_CORD, sides=4)
    foot, end, d = lean_pole(bm, uv, 112, 1.6, 2.3, 0.018, 210)
    side = d.cross(Vector((0, 0, 1))).normalized()
    for s in (-1, 0, 1):
        tip = [end - d * 0.05, end + d * 0.12 + side * 0.035 * s, end + d * 0.3 + side * 0.05 * s]
        tube(bm, uv, tip, [0.008, 0.006, 0.003], I_WOOD, sides=4)
    lashing(bm, uv, end - d * 0.02, d, 0.022, I_CORD, turns=4, height=0.06)
    foot, end, d = lean_pole(bm, uv, 58, 1.5, 2.0, 0.017, 211)
    lathe(bm, uv, end - d * 0.02, [(0.0, 0.0), (0.024, 0.03), (0.012, 0.09), (0.0, 0.13)], I_FLINT, d, segs=6, wobble=0.15)
    lashing(bm, uv, end - d * 0.03, d, 0.018, I_CORD, turns=3, height=0.05)

    hard = new_obj("InteriorHard", bm, mats)
    softo = new_obj("InteriorSoft", soft, mats)
    mod = softo.modifiers.new("Solidify", "SOLIDIFY")
    mod.thickness = 0.015
    bpy.context.view_layer.objects.active = softo
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.select_all(action="DESELECT")
    hard.select_set(True)
    softo.select_set(True)
    bpy.context.view_layer.objects.active = hard
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = ob.data.name = "Hut 4000 Interior"
    bpy.ops.object.material_slot_remove_unused()
    return ob


# ---------------------------------------------------------------- build
def build():
    os.makedirs(TEX, exist_ok=True)
    make_bark_textures()
    make_fur_textures()
    make_rawhide_textures()
    make_reed_textures()
    tx = lambda n: (os.path.join(TEX, n + "_BaseColor.png"), os.path.join(TEX, n + "_Normal.png"))
    mats = [material("Hut_Wood", (0.35, 0.27, 0.2), *tx("Hut_Bark")),
            material("Hut_Cord", (0.3, 0.24, 0.17)),
            material("Hut_Reed", (0.7, 0.58, 0.36), *tx("Hut_Reed")),
            material("Hut_Rawhide", (0.8, 0.62, 0.32), *tx("Hut_Rawhide")),
            material("Hut_Fur", (0.5, 0.36, 0.22), *tx("Hut_Fur")),
            material("Hut_Fur_Pale", (0.7, 0.6, 0.48), *tx("Hut_Fur"))]

    parts = []
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    build_lattice(bm, uv)
    build_door(bm, uv)
    bmp = bmesh.new(); uvp = bmp.loops.layers.uv.new()
    build_wall(bmp, uvp, bm, uv)
    parts.append((new_obj("Wood", bm, mats), 0))
    parts.append((new_obj("Rawhide", bmp, mats), 0.006))
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    build_lining(bm, uv)
    parts.append((new_obj("Reed", bm, mats), 0.03))
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    build_hides(bm, uv)
    parts.append((new_obj("Hides", bm, mats), 0.014))

    for ob, th in parts:
        if not th:
            continue
        mod = ob.modifiers.new("Solidify", "SOLIDIFY")
        mod.thickness = th
        mod.offset = -1
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)

    bpy.ops.object.select_all(action="DESELECT")
    for ob, _ in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0][0]
    bpy.ops.object.join()
    hut = bpy.context.active_object
    hut.name = hut.data.name = "Hut 4000"
    bpy.ops.object.material_slot_remove_unused()
    return hut


def export(hut, name="Hut 4000"):
    bpy.ops.object.select_all(action="DESELECT")
    hut.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True,
                             object_types={"MESH"}, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", path_mode="STRIP")
    print(name, "tris:", sum(len(p.vertices) - 2 for p in hut.data.polygons))


def preview(hut):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_shadows = True
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    bpy.ops.mesh.primitive_plane_add(size=14)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    os.makedirs(os.path.join(ROOT, "Captures"), exist_ok=True)
    shots = [("door", Vector((0.8, -6.5, 1.6)), Vector((0, 0, 1.1))),
             ("back", Vector((4.5, 4.5, 2.2)), Vector((0, 0, 1.1))),
             ("side", Vector((-6.0, -2.0, 3.2)), Vector((0, 0, 1.0))),
             ("inside", Vector((0.3, 0.9, 1.0)), Vector((-0.6, -1.6, 1.0))),
             ("inside_back", Vector((0.1, -1.7, 1.35)), Vector((0.0, 0.6, 0.45))),
             ("inside_left", Vector((1.2, -0.9, 1.3)), Vector((-1.0, 0.6, 0.4)))]
    for name, loc, aim in shots:
        cam.location = loc
        cam.rotation_euler = (aim - loc).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 18 if name == "inside" else 40
        sc.render.filepath = os.path.join(ROOT, "Captures", "hut_" + name + ".png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":  # info_hide_4000.py imports the helpers above
    bpy.ops.wm.read_factory_settings(use_empty=True)
    hut = build()
    export(hut)
    interior = build_interior()
    export(interior, "Hut 4000 Interior")
    if PREVIEW:
        preview(hut)
