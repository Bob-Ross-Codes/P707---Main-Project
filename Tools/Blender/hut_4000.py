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


def export(hut):
    bpy.ops.object.select_all(action="DESELECT")
    hut.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "Hut 4000.fbx"), use_selection=True,
                             object_types={"MESH"}, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", path_mode="STRIP")
    print("HUT tris:", sum(len(p.vertices) - 2 for p in hut.data.polygons))


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
             ("inside", Vector((0.3, 0.9, 1.0)), Vector((-0.6, -1.6, 1.0)))]
    for name, loc, aim in shots:
        cam.location = loc
        cam.rotation_euler = (aim - loc).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 18 if name == "inside" else 40
        sc.render.filepath = os.path.join(ROOT, "Captures", "hut_" + name + ".png")
        bpy.ops.render.render(write_still=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
hut = build()
export(hut)
if PREVIEW:
    preview(hut)
