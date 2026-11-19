import os
# Run in Blender (uses its numpy). Writes procedural textures used by the Raadhuspladsen Modern materials.
PROJECT = globals().get("PROJECT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
import bpy, numpy as np
OUT = os.path.join(PROJECT, "Assets", "3D Assets", "Raadhuspladsen Modern", "Textures")
rng = np.random.default_rng(4)

def noise(n, octaves=5, base=8):
    """Tileable value noise in [0,1] (sum of upsampled random grids)."""
    acc = np.zeros((n, n), np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        g = base * 2 ** o
        r = rng.random((g, g)).astype(np.float32)
        idx = np.arange(n) * g / n; i0 = np.floor(idx).astype(int); f = idx - i0; i1 = (i0 + 1) % g
        f = f * f * (3 - 2 * f)
        a = r[i0][:, i0] * (1 - f)[None, :] + r[i0][:, i1] * f[None, :]
        b = r[i1][:, i0] * (1 - f)[None, :] + r[i1][:, i1] * f[None, :]
        acc += amp * (a * (1 - f)[:, None] + b * f[:, None]); tot += amp; amp *= 0.5
    return acc / tot

def save(name, rgb, alpha=None, colorspace='sRGB'):
    n = rgb.shape[0]
    a = np.ones((n, n, 1), np.float32) if alpha is None else alpha[..., None]
    px = np.concatenate([np.clip(rgb, 0, 1), a], axis=2)[::-1]       # Blender images are bottom-up
    im = bpy.data.images.new(name, n, n, alpha=True); im.colorspace_settings.name = colorspace
    im.pixels = px.ravel(); im.filepath_raw = os.path.join(OUT, name + ".png"); im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im)

def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength; dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nrm = np.stack([-dx, dy, np.ones_like(h)], 2); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    return nrm * 0.5 + 0.5

# 1. Verdigris copper, standing seams every 0.5 m (texture = 3 m, matching the roofs' UV tile)
N = 2048
x = np.arange(N) / N * 3.0
seam = np.exp(-((np.mod(x, 0.5) - 0.25) ** 2) / (2 * 0.012 ** 2))       # ridge in the middle of each 0.5 m pan
n1, n2 = noise(N, 6, 4), noise(N, 5, 16)
streak = noise(N, 4, 2)[:, :1] * 0 + np.repeat(noise(N, 5, 32)[:1, :], N, 0)  # vertical rain streaks
base = np.array([0.36, 0.60, 0.52])
dark = np.array([0.20, 0.30, 0.26])
t = np.clip(0.55 * n1 + 0.25 * streak + 0.2 * n2, 0, 1)[..., None]
alb = base * (1 - t * 0.55) + dark * (t * 0.35)
alb = alb * (0.92 + 0.12 * seam[None, :, None])
save("copper_verdigris_diff", alb)
h = seam[None, :].repeat(N, 0) * 1.0 + n2 * 0.05
save("copper_verdigris_nor_gl", normal_from_height(h, 6.0), colorspace='Non-Color')

# 2. Window glass with white muntins: tile = 1.2 m x 1.2 m, panes 0.4 x 0.3 m
N = 1024
u = np.arange(N) / N * 1.2
mx = np.minimum(np.mod(u, 0.4), 0.4 - np.mod(u, 0.4)) < 0.022
my = np.minimum(np.mod(u, 0.3), 0.3 - np.mod(u, 0.3)) < 0.022
frame = (mx[None, :] | my[:, None])
pane = noise(N, 3, 6)
sky = np.linspace(0.55, 0.15, N)[:, None]                              # brighter (sky) reflection toward the top
glass = np.stack([0.10 + 0.20 * sky * pane, 0.13 + 0.24 * sky * pane, 0.16 + 0.30 * sky * pane], 2) + 0 * pane[..., None]
alb = np.where(frame[..., None], np.array([0.86, 0.85, 0.80]), glass)
smooth = np.where(frame, 0.35, 0.95).astype(np.float32)
save("window_panes_diff", alb, alpha=smooth)

# 3. Facade bay for the backdrop: 3.0 m wide x 3.2 m tall, window 1.3 x 1.9 m, light plaster to be tinted
N = 1024
X = (np.arange(N) / N * 3.0)[None, :].repeat(N, 0); Y = (np.arange(N) / N * 3.2)[::-1, None].repeat(N, 1)   # Y up
wall = 0.80 + 0.10 * noise(N, 5, 4) - 0.08 * np.clip((1.0 - Y) * 0.4, 0, 1)
win = (np.abs(X - 1.5) < 0.65) & (Y > 0.85) & (Y < 2.75)
frm = win & ((np.abs(np.abs(X - 1.5) - 0.65) < 0.06) | (np.abs(Y - 0.85) < 0.06) | (np.abs(Y - 2.75) < 0.06) | (np.abs(X - 1.5) < 0.03) | (np.abs(Y - 2.15) < 0.03))
sill = (np.abs(X - 1.5) < 0.75) & (Y > 0.74) & (Y < 0.85)
lintel_shadow = (np.abs(X - 1.5) < 0.65) & (Y > 2.55) & (Y < 2.75) & ~frm
glass = 0.12 + 0.18 * (Y - 0.85) / 1.9 * noise(N, 3, 3)
alb = np.repeat(wall[..., None], 3, 2)
alb = np.where(win[..., None], np.stack([glass, glass * 1.08, glass * 1.2], 2), alb)
alb = np.where(lintel_shadow[..., None], alb * 0.6, alb)
alb = np.where(frm[..., None], 0.88, alb)
alb = np.where(sill[..., None], 0.7, alb)
save("facade_bay_diff", alb)
hgt = np.where(win & ~frm, -1.0, 0.0) + np.where(sill, 0.4, 0.0) + 0.03 * noise(N, 4, 16)
save("facade_bay_nor_gl", normal_from_height(hgt.astype(np.float32), 3.0), colorspace='Non-Color')
print("textures written to", OUT)
