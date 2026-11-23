"""Builds the 4000 f.v.t. hut (bent saplings + hides) and exports it for Unity.

Run:  /Applications/Blender.app/Contents/MacOS/Blender -b --python Tools/Blender/hut_4000_v1.py
Frozen backup of version 1. Writes Assets/3D Assets/4000 f.t.v/Hut 4000 v1.fbx and its textures in Textures/.
Pass `-- preview` after the script path to also render check images to Captures/.
Blender axes: Z up, the door faces -Y. Units are metres.
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
random.seed(4000)
np.random.seed(4000)

# ---------------------------------------------------------------- shape
R_X, R_Y, H = 2.12, 2.04, 2.30            # footprint radii and height of the frame
LEAN = Vector((0.08, 0.05, 0.0))          # the crown sits a little off-centre
PHI_TOP = math.radians(84)                # skin stops here: leaves the smoke hole
DOOR_TH = -math.pi / 2                    # door faces -Y
DOOR_HALF = 0.30                          # half-angle of the door at the ground
DOOR_H = 1.55


def n3(x, y, z):
    return noise.noise(Vector((x, y, z)))


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def base_radius(th):
    ell = R_X * R_Y / math.sqrt((R_Y * math.cos(th)) ** 2 + (R_X * math.sin(th)) ** 2)
    return ell * (1 + 0.07 * n3(math.cos(th) * 1.4, math.sin(th) * 1.4, 7.1))


def dome(th, phi):
    r = base_radius(th) * max(math.cos(phi), 0.0) ** 0.85
    z = H * math.sin(phi) * (1 + 0.05 * n3(math.cos(th) * 0.9, math.sin(th) * 0.9, 3.3))
    return Vector((r * math.cos(th), r * math.sin(th), z)) + LEAN * (max(z, 0) / H) ** 2


def dome_normal(th, phi):
    e = 1e-3
    a = dome(th + e, phi) - dome(th - e, phi)
    b = dome(th, phi + e) - dome(th, phi - e)
    n = a.cross(b).normalized()
    p = dome(th, phi)
    if n.dot(Vector((p.x, p.y, 0)) + Vector((0, 0, 0.3))) < 0:
        n = -n
    return n


# ---------------------------------------------------------------- ribs
# Saplings planted round the edge, uneven spacing, none inside the doorway.
ribs = []
N_RIB = 15
for i in range(N_RIB):
    a = DOOR_TH + (i + 0.5) * 2 * math.pi / N_RIB + random.uniform(-0.12, 0.12)
    if abs(angdiff(a, DOOR_TH)) > DOOR_HALF + 0.18:
        ribs.append({"a": a, "seed": i * 3.7, "wob": 0.07, "r": random.uniform(0.026, 0.042)})
for s in (-1, 1):  # door posts: straighter and thicker
    ribs.append({"a": DOOR_TH + s * DOOR_HALF * 1.08, "seed": 50 + s, "wob": 0.0, "r": 0.05})


def rib_theta(rib, phi):
    return rib["a"] + rib["wob"] * n3(rib["seed"], phi * 1.6, 0.5)


def sag_factor(th, phi):
    """0 on a rib, 1 half-way between two ribs."""
    angs = sorted(rib_theta(r, phi) % (2 * math.pi) for r in ribs)
    t = th % (2 * math.pi)
    for k in range(len(angs)):
        a0 = angs[k]
        a1 = angs[(k + 1) % len(angs)] + (2 * math.pi if k == len(angs) - 1 else 0)
        tt = t if t >= a0 else t + 2 * math.pi
        if a0 <= tt <= a1:
            return max(0.0, math.sin(math.pi * (tt - a0) / (a1 - a0))) ** 1.3
    return 0.0


def door_half(z):
    if z >= DOOR_H:
        return 0.0
    return DOOR_HALF * (1 - (max(z, 0) / DOOR_H) ** 2.5) ** 0.5


def in_door(th, z, margin=0.0):
    return abs(angdiff(th, DOOR_TH)) < door_half(z) + margin


def skin(th, phi, extra=0.0):
    p = dome(th, phi)
    n = dome_normal(th, phi)
    sag = 0.10 * sag_factor(th, phi) * max(math.cos(phi), 0) ** 0.6
    wr = 0.016 * noise.noise(p * 3.7) + 0.03 * noise.noise(p * 0.9 + Vector((5, 0, 0)))
    hem = 0.06 * max(0.0, 1 - phi / 0.14)  # hem flares out where it meets the ground
    return p + n * (0.048 - sag + wr + hem + extra)


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


def tube(bm, uv, pts, radii, mat=0, sides=8, tile=0.9):
    """Pipe along pts. Bark texture U runs along the length, V around."""
    n = len(pts)
    tans = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    nrm = tans[0].orthogonal().normalized()
    rings, length, u0 = [], 0.0, random.random()
    for i in range(n):
        t = tans[i]
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        if i:
            length += (pts[i] - pts[i - 1]).length
        ring = []
        for k in range(sides + 1):
            ang = 2 * math.pi * k / sides
            ring.append((bm.verts.new(pts[i] + (nrm * math.cos(ang) + bi * math.sin(ang)) * radii[i]),
                         (u0 + length / tile, k / sides)))
        rings.append(ring)
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


def lashing(bm, uv, centre, axis, r, turns=5, height=0.08, mat=2):
    """A few turns of cord wrapped round a pole."""
    axis = axis.normalized()
    x = axis.orthogonal().normalized()
    y = axis.cross(x)
    steps = turns * 10
    pts = [centre + axis * (height * (i / steps - 0.5)) +
           (x * math.cos(2 * math.pi * i / 10) + y * math.sin(2 * math.pi * i / 10)) * (r + 0.008)
           for i in range(steps + 1)]
    tube(bm, uv, pts, [0.007] * len(pts), mat=mat, sides=5, tile=0.3)


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
def save_png(arr, path, alpha=None):
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
    """Tileable 1/f^beta noise in [0,1]; aniso > 1 stretches it along x."""
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


def make_hide_textures():
    s = 1024
    low = fbm(s, 1.6)
    mid = fbm(s, 1.1)
    hair = fbm(s, 0.9, aniso=6.0)        # short fibre streaks
    stain = np.clip((fbm(s, 1.4) - 0.62) * 4, 0, 1)
    light = np.array([0.62, 0.49, 0.36])
    dark = np.array([0.33, 0.23, 0.15])
    t = np.clip(low * 0.8 + mid * 0.4 - 0.25, 0, 1)[..., None]
    col = light * (1 - t) + dark * t
    col *= (0.85 + 0.3 * hair)[..., None]
    col *= (1 - 0.35 * stain)[..., None]
    save_png(col, os.path.join(TEX, "Hut_Hide_BaseColor.png"))
    wrinkle = np.abs(fbm(s, 1.2, aniso=0.5) - 0.5) * 2
    height = wrinkle * 0.7 + hair * 0.3
    save_png(normal_from_height(height, 6.0), os.path.join(TEX, "Hut_Hide_Normal.png"))


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


# ---------------------------------------------------------------- build
def build():
    os.makedirs(TEX, exist_ok=True)
    make_hide_textures()
    make_bark_textures()
    wood = material("Hut_Wood", (0.35, 0.27, 0.2), os.path.join(TEX, "Hut_Bark_BaseColor.png"),
                    os.path.join(TEX, "Hut_Bark_Normal.png"))
    hide = material("Hut_Hide", (0.55, 0.43, 0.31), os.path.join(TEX, "Hut_Hide_BaseColor.png"),
                    os.path.join(TEX, "Hut_Hide_Normal.png"))
    hide2 = material("Hut_Hide_Dark", (0.4, 0.3, 0.22), os.path.join(TEX, "Hut_Hide_BaseColor.png"),
                     os.path.join(TEX, "Hut_Hide_Normal.png"))
    cord = material("Hut_Cord", (0.3, 0.24, 0.17))
    mats = [wood, hide, hide2, cord]
    WOOD, HIDE, HIDE2, CORD = range(4)

    # --- frame
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    tips = []
    for rib in ribs:
        pts, phis = [], np.linspace(-0.05, PHI_TOP + 0.03, 34)
        for phi in phis:
            pts.append(dome(rib_theta(rib, phi), phi))
        # tip pokes up and out through the smoke hole
        last = pts[-1]
        out = Vector((last.x - LEAN.x, last.y - LEAN.y, 0)).normalized()
        L = random.uniform(0.25, 0.6)
        d = (Vector((0, 0, 1)) + out * random.uniform(0.2, 0.6)).normalized()
        for k in range(1, 6):
            pts.append(last + d * L * k / 5 + out * 0.02 * k * k / 25)
        tips.append(last + d * 0.12)
        n = len(pts)
        radii = [rib["r"] * (1 - 0.55 * i / (n - 1)) for i in range(n)]
        tube(bm, uv, pts, radii, WOOD)

    # door lintel, lashed to both posts
    zL = DOOR_H + 0.04
    phiL = math.asin(min(zL / H, 1))
    posts = [r for r in ribs if r["wob"] == 0.0]
    pa = dome(rib_theta(posts[0], phiL), phiL) + dome_normal(rib_theta(posts[0], phiL), phiL) * 0.06
    pb = dome(rib_theta(posts[1], phiL), phiL) + dome_normal(rib_theta(posts[1], phiL), phiL) * 0.06
    span = (pb - pa).normalized()
    a_end = pa - span * 0.18 + Vector((0, 0, -0.03))
    b_end = pb + span * 0.22 + Vector((0, 0, 0.04))
    lint = wobble_path(a_end, b_end, 10, 0.02, 11)
    tube(bm, uv, lint, [0.04] * len(lint), WOOD)
    for p in (pa, pb):
        lashing(bm, uv, p - dome_normal(DOOR_TH, phiL) * 0.04, Vector((0, 0, 1)), 0.05, mat=CORD)

    # weight poles leaning on the cover
    for k in range(6):
        th = DOOR_TH + random.uniform(0.9, 2 * math.pi - 0.9)
        phi_c = random.uniform(0.75, 1.15)
        top = dome(th, phi_c) + dome_normal(th, phi_c) * 0.11
        th_f = th + random.uniform(-0.25, 0.25)
        foot = dome(th_f, 0) * random.uniform(1.12, 1.3) + Vector((0, 0, -0.06))
        over = top + (top - foot).normalized() * random.uniform(0.15, 0.5)
        pts = wobble_path(foot, over, 12, 0.04, 20 + k)
        tube(bm, uv, pts, [random.uniform(0.03, 0.045) * (1 - 0.35 * i / 12) for i in range(13)], WOOD)

    # cords round the cover, tied off at the door posts
    for z0, seed in ((0.8, 1), (1.5, 2)):
        pts = []
        th0 = DOOR_TH + DOOR_HALF * 1.08
        steps = 140
        for i in range(steps + 1):
            th = th0 + (2 * math.pi - 2 * DOOR_HALF * 1.08) * i / steps
            z = z0 + 0.06 * n3(seed, th, 0) + 0.04 * math.sin(th * 3 + seed)
            phi = math.asin(min(z / H, 0.99))
            pts.append(skin(th, phi, 0.05))
        tube(bm, uv, pts, [0.016] * len(pts), CORD, sides=6, tile=0.4)
    # bundle the tips together at the smoke hole
    c = sum(tips, Vector()) / len(tips)
    ring = [c + (t - c) * 1.08 for t in sorted(tips, key=lambda t: math.atan2(t.y - c.y, t.x - c.x))]
    ring.append(ring[0])
    tube(bm, uv, ring, [0.013] * len(ring), CORD, sides=5, tile=0.4)
    frame = new_obj("Frame", bm, mats)

    # --- main hide cover
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    NT, NP = 96, 26
    grid = {}
    for j in range(NP + 1):
        for i in range(NT + 1):
            th = DOOR_TH + 2 * math.pi * i / NT
            p0 = -0.04 + 0.035 * n3(th, 9, 1)
            p1 = PHI_TOP + 0.03 * n3(th * 2, 4, 2)
            phi = p0 + (p1 - p0) * j / NP
            dh = door_half(dome(DOOR_TH, phi).z)
            th = DOOR_TH + dh + (2 * math.pi - 2 * dh) * i / NT  # squeeze the row round the opening
            uvc = ((th - DOOR_TH) * 2.1 / 1.3, j * 3.4 / NP / 1.3)
            if dh == 0 and i == NT:
                grid[i, j] = (grid[0, j][0], uvc)  # closed ring above the door, own UV for the seam
            else:
                grid[i, j] = (bm.verts.new(skin(th, phi)), uvc)
    for i in range(NT):
        for j in range(NP):
            q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
            if len({id(v[0]) for v in q}) < 4:
                continue
            f = bm.faces.new([v[0] for v in q])
            f.material_index = HIDE
            for loop, v in zip(f.loops, q):
                loop[uv].uv = v[1]
    cover = new_obj("Cover", bm, mats)

    # --- overlapping hide panels with ragged edges
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    made_n = 0
    for k in range(60):
        if made_n == 26:
            break
        thc = DOOR_TH + random.uniform(0.3, 2 * math.pi - 0.3)
        phic = random.uniform(0.1, 1.15)
        w = random.uniform(0.7, 1.3) / max(base_radius(thc) * math.cos(phic), 0.6)
        h = random.uniform(0.45, 0.85) / (H * 1.2)
        if abs(angdiff(thc, DOOR_TH)) < DOOR_HALF + w / 2 + 0.1 and phic - h / 2 < 0.8:
            continue  # would hang over the doorway
        made_n += 1
        extra = random.uniform(0.008, 0.03)
        mat = HIDE2 if k % 3 == 0 else HIDE
        tilt = random.uniform(-0.5, 0.5)
        NR, NA = 7, 22
        uoff = (random.random() * 3, random.random() * 3)
        centre = bm.verts.new(skin(thc, phic, extra))
        rings = []
        for r in range(1, NR + 1):
            row = []
            for m in range(NA):
                al = 2 * math.pi * m / NA
                outline = 1 + 0.2 * n3(k * 7.0, math.cos(al) * 1.2, math.sin(al) * 1.2) \
                    + 0.07 * n3(k * 7.0, math.cos(al) * 4, math.sin(al) * 4)
                rho = r / NR * outline
                u, v = rho * math.cos(al + tilt), rho * math.sin(al + tilt)
                curl = 0.04 * max(0, r / NR - 0.6) ** 2
                row.append((bm.verts.new(skin(thc + u * w / 2, max(phic + v * h / 2, -0.03), extra + curl)),
                            (uoff[0] + u * 0.4, uoff[1] + v * 0.3)))
            rings.append(row)
        cuv = (uoff[0], uoff[1])
        for m in range(NA):
            m2 = (m + 1) % NA
            f = bm.faces.new([centre, rings[0][m][0], rings[0][m2][0]])
            f.material_index = mat
            for loop, x in zip(f.loops, (cuv, rings[0][m][1], rings[0][m2][1])):
                loop[uv].uv = x
            for r in range(NR - 1):
                q = [rings[r][m], rings[r + 1][m], rings[r + 1][m2], rings[r][m2]]
                f = bm.faces.new([x[0] for x in q])
                f.material_index = mat
                for loop, x in zip(f.loops, q):
                    loop[uv].uv = x[1]
    panels = new_obj("Panels", bm, mats)

    # --- door flap: a hide hung from the lintel, covering part of the opening
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    out_d = Vector((math.cos(DOOR_TH), math.sin(DOOR_TH), 0))
    NU, NV = 12, 14
    fv = {}
    for a in range(NU + 1):
        for b in range(NV + 1):
            s, t = a / NU, b / NV
            top = lint[1].lerp(lint[-2], 0.04 + 0.5 * s) + out_d * 0.03
            zb = 0.12 + 0.12 * n3(s * 4, 8, 0) + 0.25 * s
            p = top + Vector((0, 0, -(top.z - zb) * t))
            p += out_d * (0.035 * math.sin(s * math.pi * 5) * t + 0.08 * t)
            fv[a, b] = (bm.verts.new(p), (s * 0.7, 1 - t * 0.9))
    for a in range(NU):
        for b in range(NV):
            q = [fv[a, b], fv[a, b + 1], fv[a + 1, b + 1], fv[a + 1, b]]
            f = bm.faces.new([x[0] for x in q])
            f.material_index = HIDE2
            for loop, x in zip(f.loops, q):
                loop[uv].uv = x[1]
    flap = new_obj("Flap", bm, mats)

    # thickness so hides are not paper-thin from inside the doorway
    for ob, th in ((cover, 0.012), (panels, 0.008), (flap, 0.01)):
        mod = ob.modifiers.new("Solidify", "SOLIDIFY")
        mod.thickness = th
        mod.offset = -1
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)

    bpy.ops.object.select_all(action="DESELECT")
    for ob in (frame, cover, panels, flap):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = frame
    bpy.ops.object.join()
    hut = bpy.context.active_object
    hut.name = hut.data.name = "Hut 4000"
    bpy.ops.object.material_slot_remove_unused()
    return hut


def export(hut):
    bpy.ops.object.select_all(action="DESELECT")
    hut.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "Hut 4000 v1.fbx"), use_selection=True,
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
    for name, ang, el in (("door", -90, 12), ("back", 70, 18), ("side", 200, 30)):
        a = math.radians(ang)
        cam.location = Vector((math.cos(a), math.sin(a), 0)) * 7.5 + Vector((0, 0, 1 + el / 10))
        d = Vector((0, 0, 1.1)) - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(ROOT, "Captures", "hut_" + name + ".png")
        bpy.ops.render.render(write_still=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
hut = build()
export(hut)
if PREVIEW:
    preview(hut)
