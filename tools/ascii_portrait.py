"""Photo -> neofetch-style ASCII portrait variants.
usage: python ascii_portrait.py PHOTO OUTDIR
Writes OUTDIR/variant_<name>.txt and OUTDIR/variants_sheet.png (all variants rendered side by side)."""
import sys, os, numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont
import cv2
from rembg import remove

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
im.thumbnail((1400, 1400))
cut = remove(im)                       # RGBA, background alpha=0
a = np.array(cut)[:, :, 3]
ys, xs = np.where(a > 40)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
# head-and-shoulders crop: top of hair down to ~1.15x the head height below
h = y1 - y0
y1c = min(y1, y0 + int((x1 - x0) * 1.15))
cut = cut.crop((max(0, x0 - 10), max(0, y0 - 10), min(cut.width, x1 + 10), y1c))
rgba = np.array(cut).astype(np.float32)
alpha = rgba[:, :, 3] / 255.0
gray = cv2.cvtColor(rgba[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(6, 6))
blur = cv2.GaussianBlur(gray, (0, 0), 3)
gray = cv2.addWeighted(gray, 1.6, blur, -0.6, 0)  # unsharp mask: crisper eyes/brows/mouth

RAMPS = {
    "andrew": " .`',:;!|ijlkm%H@g",        # close to Andrew6rant's glyph mix
    "classic": " .:-=+*#%@",
    "dense": " .'`^\",:;Il!i><~+_-?][}{1)(|tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "soft": " .,:;irsXA253hMHGS#9B&@",
}

def to_ascii(cols, ramp, gamma, edge, invert):
    g = clahe.apply(gray)
    if edge:
        e = cv2.Canny(g, 60, 140)
        e = cv2.dilate(e, np.ones((2, 2), np.uint8))
        g = np.clip(g.astype(np.int16) - (e > 0) * 90, 0, 255).astype(np.uint8)
    lum = g.astype(np.float32) / 255.0
    m = alpha > 0.5
    lo, hi = np.percentile(lum[m], 3), np.percentile(lum[m], 97)   # stretch subject only
    lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    # ink = darkness on a dark terminal shows as bright glyphs -> map brightness to density
    ink = lum if invert else 1 - lum
    ink = ink ** gamma
    ink = ink * alpha                          # background -> space
    rows = int(cols * cut.height / cut.width * 0.47)  # 16px monospace on 20px lines (Andrew6rant metrics)
    small = cv2.resize(ink, (cols, rows), interpolation=cv2.INTER_AREA)
    n = len(ramp) - 1
    return ["".join(ramp[int(round(v * n))] for v in r).rstrip() for r in small]

variants = {}
for cols in (40, 46):
    for rname in ("andrew", "dense", "soft"):
        for inv in (True, False):
            key = f"c{cols}_{rname}_{'fordark' if inv else 'forlight'}"
            variants[key] = to_ascii(cols, RAMPS[rname], 1.0, edge=True, invert=inv)
cut.save(os.path.join(out, "cutout.png"))
for k, lines in variants.items():
    open(os.path.join(out, f"variant_{k}.txt"), "w").write("\n".join(lines) + "\n")

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12) if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf") else ImageFont.load_default()
tiles = []
for k, lines in variants.items():
    w, hgt = 8 + 7.3 * 48, 22 + 15 * max(len(lines), 1)
    light = k.endswith("forlight")
    t = Image.new("RGB", (int(w), int(hgt)), (246, 248, 250) if light else (22, 27, 34))
    d = ImageDraw.Draw(t)
    d.text((6, 4), k, fill=(149, 56, 0) if light else (255, 166, 87), font=font)
    for i, l in enumerate(lines):
        d.text((6, 22 + 15 * i), l, fill=(36, 41, 47) if light else (201, 209, 217), font=font)
    tiles.append(t)
W = max(t.width for t in tiles); H = max(t.height for t in tiles)
per = 4
sheet = Image.new("RGB", (W * per, H * ((len(tiles) + per - 1) // per)), (13, 17, 23))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % per) * W, (i // per) * H))
sheet.save(os.path.join(out, "variants_sheet.png"))
print("wrote", len(variants), "variants to", out)
