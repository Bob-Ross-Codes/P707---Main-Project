"""Builds the 4000 f.v.t. info hides for Unity: a rawhide laced into a pole frame, with an info page painted on.

Run:  /Applications/Blender.app/Contents/MacOS/Blender -b --python Tools/Blender/info_hide_4000.py
Writes Assets/3D Assets/4000 f.t.v/Info Hide 4000 <TV|MID|TH>.fbx and Textures/InfoHide_<key>_BaseColor/_Normal.png.
The copy lives in PAGES below and is set in Georgia, sized to read on the 1080p screen; the photos are cropped out of
the old web-page cards in Assets/2D Assets/Textinfo. Edit PAGES and re-run to change the wording.
Blender axes: Z up, the painted side faces -Y. Units are metres; the origin is on the ground between the poles.
Each moving part hangs under a pivot empty (Pole_L, Pole_R, Bar_Top, Bar_Bottom, Hide) with its *_Mesh child at
identity, so one Unity clip (Assets/Animations/Info Hide Build.anim) builds all three frames.
"""
import bpy, bmesh, math, os, random, sys, tempfile
import numpy as np
from mathutils import Vector

sys.dont_write_bytecode = True   # no __pycache__ next to the scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hut_4000 import ROOT, OUT, TEX, n3, angdiff, tube, wobble_path, lashing, new_obj, material, save_png

CARDS = os.path.join(ROOT, "Assets", "2D Assets", "Textinfo")
PAGES = {
    "TV": dict(card="4000_TV2.png", photo_w=1.0, title="Den salte kystmarsk",
               body="I de små vige på Sjællands østkyst fandtes sivskove, mens der på de udsatte kyster ud mod "
                    "Øresund var åben strand med græsser og urter, der kunne tåle både salt og fugt. Planterne nød "
                    "godt af de tilførte næringsstoffer, som blev ført med saltvandet ind over strandengene og "
                    "aflejredes, når det blæste. På det lidt tørrere land var der krat og træbevoksning. Her voksede "
                    "blandt andet egetræer. Egetræer og hassel kan tåle en vis saltpåvirkning og kan derfor, i "
                    "modsætning til de fleste andre træer, rykke længere frem mod stranden.",
               caption="Kysten mellem Sjælland og Amager var præget af små afskærmede vige og med åbne "
                       "strand-arealer. Foto: CoastalSandpiper, Pixabay."),
    "MID": dict(card="4000_Mid2.png", photo_w=0.8, title="Spor af mennesker",
                body="I området omkring Rådhuspladsen er der ikke fundet egentlige spor af hytter eller lignende, "
                     "og kun ét sted er der fundet et intakt lag med spor fra stenalderen i form af flintaffald. "
                     "Andre steder i området lå affaldet fra stenalderen blandet rundt i yngre lag. Det er sikkert "
                     "sket, fordi man allerede i middelalderen eller senere hen har gravet, og dermed forstyrret "
                     "sporene fra stenalderen. Sporene fra stenalderen viser, at der har været mennesker, som har "
                     "boet i området i en periode, eller har passeret forbi. Derfor viser vi i modellen en simpel "
                     "boplads, som den kunne have set ud. På denne tid har der ikke været egentlige landsbyer med "
                     "mange hytter men snarere ensomt liggende hytter.",
                caption="Billede fra indersiden af en rekonstrueret stenalderhytte fra Sagnlandet Lejre, hvor der "
                        "er fiskeredskaber, skind og ildsted inde i hytten. Hytten er bygget som en rekonstruktion "
                        "af en af Nivå-hytterne fra Nordsjælland."),
    "TH": dict(card="4000_TH2.png", photo_w=0.9, title="Stenalderhavets højde",
               body="Efter afslutningen på sidste istid var havniveauet anderledes end i dag. Da de store iskapper "
                    "smeltede, steg det globale havniveau. I Danmark blev landmasserne ikke længere presset ned af "
                    "vægten af iskapperne, og landmasserne begyndte derfor langsomt at hæve sig. Der opstod et "
                    "”kapløb” mellem havniveaustigningen og landhævningen, og i stenalderen var der i den nordlige "
                    "del af Danmark et ø-hav: Stenalderhavet. I København var havniveauet ca. 3,2 m højere end i "
                    "dag, og en stor del af det nuværende København ligger i områder, der dengang var havdækket.",
               caption="Illustration der med en rød streg viser stenalderkystlinjen i København."),
}
# Blender text sizes; Georgia's x-height is 0.35 of the size, so the body's 2.8 cm x-height is about 8.5 px on the
# 1080p screen for a visitor 1.5 m from it
TITLE, BODY, CAPTION = 0.12, 0.08, 0.068
TEXT_W, COL_GAP, GAP = 1.4, 0.12, 0.06          # body column (about 50 characters a line), gaps between blocks
INK = {"title": ((0.42, 0.13, 0.06), 0.9), "body": ((0.06, 0.05, 0.04), 0.94),   # red ochre and charcoal
       "caption": ((0.12, 0.10, 0.08), 0.85)}
FONT_DIRS = ["/System/Library/Fonts/Supplemental", "/Library/Fonts", "C:/Windows/Fonts"]
FONTS = {"regular": ("Georgia.ttf", "georgia.ttf"), "bold": ("Georgia Bold.ttf", "georgiab.ttf"),
         "italic": ("Georgia Italic.ttf", "georgiai.ttf")}
PPM = 640                       # texture pixels per metre; the 1024 px rawhide tile then spans 1.6 m
SE = 6.0                        # superellipse power of the stretched hide: higher is squarer
POLE_R, BAR_R = 0.05, 0.04
BAR_Y = -(POLE_R + BAR_R)       # the bars are lashed to the front of the poles
GROUND_IN = 0.3                 # pole feet below the ground
BOTTOM_BAR = 0.1                # height of the lower bar


def outline(al, k):
    """Normalised hide edge radius at angle al (0 = +X, pi/2 = up): squarish stretched body, leg flaps, neck, tail."""
    e = (abs(math.cos(al)) ** SE + abs(math.sin(al)) ** SE) ** (-1 / SE)
    for c, amp, w in ((math.pi / 4, 0.16, 0.10), (3 * math.pi / 4, 0.16, 0.10),
                      (-math.pi / 4, 0.14, 0.11), (-3 * math.pi / 4, 0.14, 0.11),
                      (math.pi / 2, 0.07, 0.22), (-math.pi / 2, 0.05, 0.07)):
        e += amp * math.exp(-(angdiff(al, c) / w) ** 2)
    return e * (1 + 0.015 * n3(k * 7.0, math.cos(al) * 3, math.sin(al) * 3))


def pixels(img, channels=3):
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[..., :channels]   # rows run bottom to top, as in UV space


def tiled(name, h, w):
    img = bpy.data.images.load(os.path.join(TEX, name), check_existing=False)
    src = pixels(img)
    bpy.data.images.remove(img)
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
    img = bpy.data.images.load(path, check_existing=False)
    a = pixels(img)
    bpy.data.images.remove(img)
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


def font(style):
    for d in FONT_DIRS:
        for name in FONTS[style]:
            if os.path.exists(os.path.join(d, name)):
                return bpy.data.fonts.load(os.path.join(d, name), check_existing=True)
    raise FileNotFoundError("Georgia %s not found in %s" % (style, FONT_DIRS))


def text(body, style, size, width, x, top, color):
    """A wrapped text block with its top edge at y = top; returns its height."""
    cu = bpy.data.curves.new("text", "FONT")
    cu.body, cu.font, cu.size, cu.space_line = body, font(style), size, 1.12
    cu.text_boxes[0].width = width
    ob = bpy.data.objects.new("text", cu)
    ob.color = color
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.update()
    ys = [c[1] for c in ob.bound_box]
    ob.location = (x, top - max(ys), 0)
    return max(ys) - min(ys)


def render_page(page):
    """Sets the page (title across, body left, photo and caption right) and renders its ink at PPM.
    Returns the page size in metres, one ink mask per style (title, body, caption; rows bottom to top) and the
    photo with its bottom-left corner in page pixels."""
    photo = card_photo(os.path.join(CARDS, page["card"]))
    pw = page["photo_w"]
    ph = pw * photo.shape[0] / photo.shape[1]
    xc = TEXT_W + COL_GAP
    th = text(page["title"], "bold", TITLE, xc + pw, 0, 0, (1, 0, 0, 1))      # colour = mask channel
    top = -(th + GAP)
    bh = text(page["body"], "regular", BODY, TEXT_W, 0, top, (0, 1, 0, 1))
    caph = text(page["caption"], "italic", CAPTION, pw, xc, top - ph - GAP / 2, (0, 0, 1, 1))
    cw, ch = xc + pw, th + GAP + max(bh, ph + GAP / 2 + caph)

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "FLAT", "OBJECT"
    sh.show_cavity = sh.show_shadows = sh.show_object_outline = False
    sc.display.render_aa = "32"
    sc.render.film_transparent = True
    sc.render.dither_intensity = 0
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = round(cw * PPM), round(ch * PPM)
    sc.render.resolution_percentage = 100
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type, cam.data.ortho_scale = "ORTHO", max(cw, ch)
    cam.location = (cw / 2, -ch / 2, 5)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(tempfile.mkdtemp(), "page.png")
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(sc.render.filepath)
    rgba = pixels(img, 4)
    masks = rgba[..., :3] * rgba[..., 3:]
    ph_px, pw_px = round(ph * PPM), round(pw * PPM)
    return cw, ch, masks, (round(xc * PPM), round((ch - th - GAP) * PPM) - ph_px, resize(photo, pw_px, ph_px))


def pivot(name, loc):
    em = bpy.data.objects.new(name, None)
    em.location = loc
    bpy.context.collection.objects.link(em)
    return em


def part(name, loc, mats, fill):
    """Pivot empty at loc with a <name>_Mesh child at identity; fill(bm, uv, loc) builds the mesh in world space."""
    em = pivot(name, loc)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    fill(bm, uv)
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=-loc)
    ob = new_obj(name + "_Mesh", bm, mats)
    ob.parent = em
    return ob


def build(key, cw, ch, masks, photo, seed, mats):
    wood, cord, hide_mat = mats
    random.seed(seed)
    k = seed * 0.37
    a, b = cw / 2 + 0.16, ch / 2 + 0.17       # body semi-axes; the page corners stay inside the rounded corners
    NA, NR = 120, 20
    edge = [outline(2 * math.pi * j / NA, k) for j in range(NA)]
    ex = [edge[j] * math.cos(2 * math.pi * j / NA) * a for j in range(NA)]
    ez = [edge[j] * math.sin(2 * math.pi * j / NA) * b for j in range(NA)]
    xmin, xmax, zmin, zmax = min(ex), max(ex), min(ez), max(ez)
    zc = BOTTOM_BAR + 0.06 - zmin             # hide centre height above the ground
    z_top_bar = zc + zmax + 0.08
    px = max(-xmin, xmax) + 0.10              # poles at x = -px and +px
    pole_top = z_top_bar + 0.25

    # texture: rawhide tiled 1:1, scraped lighter and smoother behind the page, then photo and ink painted on
    W, H = int(round((xmax - xmin) * PPM / 8)) * 8, int(round((zmax - zmin) * PPM / 8)) * 8
    base = tiled("Hut_Rawhide_BaseColor.png", H, W)
    h_px, w_px = masks.shape[:2]
    x0, y0 = round((-cw / 2 - xmin) * PPM), round((-ch / 2 - zmin) * PPM)
    assert x0 >= 0 and y0 >= 0 and x0 + w_px <= W and y0 + h_px <= H, (key, x0, y0, masks.shape, W, H)
    yy, xx = np.mgrid[0:H, 0:W]
    f = 40
    s = (np.clip(np.minimum(xx - x0 + f, x0 + w_px + f - xx) / f, 0, 1) *
         np.clip(np.minimum(yy - y0 + f, y0 + h_px + f - yy) / f, 0, 1))
    s = (s * s * (3 - 2 * s))[..., None]
    m = s * 0.6
    base = base * (1 - m) + base.mean((0, 1)) * 1.1 * m
    page = base[y0:y0 + h_px, x0:x0 + w_px]   # a view: painting it paints base
    px0, py0, img = photo
    under = page[py0:py0 + img.shape[0], px0:px0 + img.shape[1]]
    under[:] = img * (0.8 + 0.2 * under / under.mean((0, 1)))   # a little leather grain shows through the photo
    for i, style in enumerate(("title", "body", "caption")):
        color, opacity = INK[style]
        ink = masks[..., i:i + 1] * opacity
        page[:] = page * (1 - ink) + np.array(color) * ink
    save_png(base, os.path.join(TEX, "InfoHide_%s_BaseColor.png" % key))
    nrm = tiled("Hut_Rawhide_Normal.png", H, W)
    nrm = nrm * (1 - s * 0.85) + np.array((0.5, 0.5, 1.0)) * s * 0.85   # calmer bumps behind the writing
    save_png(resize(nrm, W // 2, H // 2), os.path.join(TEX, "InfoHide_%s_Normal.png" % key))

    def pole(side):
        def fill(bm, uv):
            foot = Vector((side * px, 0.0, -GROUND_IN))
            top = Vector((side * px + 0.03 * n3(seed, side, 1), 0.01, pole_top))
            pts = wobble_path(foot, top, 14, 0.012, seed + side)
            tube(bm, uv, pts, [POLE_R * (1 - 0.2 * i / (len(pts) - 1)) for i in range(len(pts))], 0, sides=8)
        return fill

    def bar(z):
        def fill(bm, uv):
            pts = wobble_path(Vector((-px - 0.16, BAR_Y, z)), Vector((px + 0.16, BAR_Y, z + 0.02)), 10, 0.01, seed + z)
            tube(bm, uv, pts, [BAR_R * (1 - 0.15 * i / (len(pts) - 1)) for i in range(len(pts))], 0, sides=8)
            for s in (-1, 1):                  # cross lashing where the bar meets each pole
                for ax in (Vector((1, 0, 1)), Vector((1, 0, -1))):
                    lashing(bm, uv, Vector((s * px, BAR_Y / 2, z)), ax, POLE_R + 0.035, 1, turns=3, height=0.05)
        return fill

    def hide(bm, uv):
        vid, uvs = {}, {}
        def vert(i, j):
            j %= NA
            key_ = (0, 0) if i == 0 else (i, j)
            if key_ not in vid:
                al, rr = 2 * math.pi * j / NA, i / NR
                x, z = rr * edge[j] * math.cos(al) * a, rr * edge[j] * math.sin(al) * b
                y = -0.03 * (1 - rr * rr) - 0.004 * n3(x * 2.5, z * 2.5, k)   # slight belly toward the viewer
                vid[key_] = bm.verts.new((x, y, zc + z))
                uvs[key_] = ((x - xmin) / (xmax - xmin), (z - zmin) / (zmax - zmin))
            return vid[key_], uvs[key_]
        faces = []
        for i in range(NR):
            for j in range(NA):
                q = [vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)]   # winding faces -Y
                if i == 0:
                    q = q[:3]
                f = bm.faces.new([v for v, _ in q])
                f.material_index = 0
                for loop, (_, t) in zip(f.loops, q):
                    loop[uv].uv = t
                faces.append(f)
        bmesh.ops.solidify(bm, geom=faces, thickness=0.006)
        # lacing: cords from holes near the edge to the nearest pole or bar
        n = max(16, int(2.2 * (a + b) * 2 / 0.22))
        for m_ in range(n):
            al = 2 * math.pi * (m_ + 0.5) / n
            e = outline(al, k) * 0.93
            x, z = e * math.cos(al) * a, zc + e * math.sin(al) * b
            hole = Vector((x, -0.008, z))
            gaps = {"L": x + px, "R": px - x, "T": z_top_bar - z, "B": z - BOTTOM_BAR}
            side = min(gaps, key=gaps.get)
            tgt = {"L": Vector((-px, 0, z + 0.02)), "R": Vector((px, 0, z + 0.02)),
                   "T": Vector((x * 1.02, BAR_Y, z_top_bar)), "B": Vector((x * 1.02, BAR_Y, BOTTOM_BAR))}[side]
            mid = (hole + tgt) / 2 + Vector((0, -0.01, -0.012))
            tube(bm, uv, [hole, mid, tgt], [0.005] * 3, 1, sides=4, tile=0.3)

    part("Pole_L", Vector((-px, 0, 0)), [wood], pole(-1))
    part("Pole_R", Vector((px, 0, 0)), [wood], pole(1))
    part("Bar_Top", Vector((0, BAR_Y, z_top_bar)), [wood, cord], bar(z_top_bar))
    part("Bar_Bottom", Vector((0, BAR_Y, BOTTOM_BAR)), [wood, cord], bar(BOTTOM_BAR))
    part("Hide", Vector((0, 0, zc + zmax)), [hide_mat, cord], hide)
    print("%s: page %.2f x %.2f m, hide %.2f x %.2f m, poles at +-%.2f m, %.2f m tall, texture %dx%d"
          % (key, cw, ch, xmax - xmin, zmax - zmin, px, pole_top, W, H))


def export(name):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True,
                             object_types={"EMPTY", "MESH"}, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", path_mode="STRIP", bake_anim=False)
    print(name, "tris:", sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                             for o in bpy.data.objects if o.type == "MESH"))


if __name__ == "__main__":
    for n, (key, page) in enumerate(PAGES.items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        cw, ch, masks, photo = render_page(page)
        bpy.ops.wm.read_factory_settings(use_empty=True)   # fresh file per hide, so material names stay exact
        mats = [material("Hut_Wood", (0.35, 0.27, 0.2)), material("Hut_Cord", (0.3, 0.24, 0.17)),
                material("InfoHide_" + key, (0.8, 0.62, 0.32))]
        build(key, cw, ch, masks, photo, 4000 + n, mats)
        export("Info Hide 4000 " + key)
