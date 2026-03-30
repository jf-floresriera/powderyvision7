"""
generate_icons.py  –  PowderyVision7
Genera todos los iconos PWA + favicon.ico
Ejecutar: python generate_icons.py

Diseno: hoja verde con manchas blancas de mildiu polvoso
Tamanos generados:
  16, 32, 48 px  -> favicon.ico
  72, 96, 128, 144, 152, 180, 192, 256, 384, 512 px  -> PNGs
"""

import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ── Paleta ────────────────────────────────────────────────────────────────
BG_TOP     = ( 27,  94,  32)         # #1B5E20  verde oscuro
BG_BOT     = ( 46, 125,  50)         # #2E7D32  verde medio
LEAF_FILL  = ( 76, 175,  80, 255)    # #4CAF50  hoja verde
LEAF_DARK  = ( 46, 125,  50, 255)    # borde hoja
VEIN_COL   = (255, 255, 255, 160)    # nervios blancos
MILDEW_COL = (245, 242, 232, 218)    # manchas mildiu (blanco-crema)
GOLD       = (255, 193,   7, 255)    # #FFC107  texto PV


# ── Fondo degradado con esquinas redondeadas ──────────────────────────────
def make_background(size: int) -> Image.Image:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    for y in range(size):
        t = y / max(size - 1, 1)
        arr[y, :] = [
            int(BG_TOP[0] + t * (BG_BOT[0] - BG_TOP[0])),
            int(BG_TOP[1] + t * (BG_BOT[1] - BG_TOP[1])),
            int(BG_TOP[2] + t * (BG_BOT[2] - BG_TOP[2])),
            255
        ]
    base = Image.fromarray(arr, "RGBA")
    # Esquinas redondeadas (22 % del lado)
    radius = int(size * 0.22)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=radius, fill=255)
    base.putalpha(mask)
    return base


# ── Geometria de la hoja ──────────────────────────────────────────────────
def leaf_poly(cx, cy, length, width, angle_deg, n=48):
    """Ovalo puntiagudo (hoja) rotado angle_deg grados."""
    ar  = math.radians(angle_deg)
    pts = []
    for i in range(n):
        t  = 2 * math.pi * i / n
        lx = (width  / 2) * math.sin(t) * (1 - 0.12 * (1 - abs(math.cos(t))))
        ly = -(length / 2) * math.cos(t)
        rx = lx * math.cos(ar) - ly * math.sin(ar)
        ry = lx * math.sin(ar) + ly * math.cos(ar)
        pts.append((int(cx + rx), int(cy + ry)))
    return pts


def midrib(cx, cy, length, angle_deg):
    ar = math.radians(angle_deg)
    hl = length * 0.44
    return (cx + hl * math.sin(ar), cy - hl * math.cos(ar)), \
           (cx - hl * math.sin(ar), cy + hl * math.cos(ar))


# ── Dibujar hoja con mildiu ───────────────────────────────────────────────
def draw_leaf_mildew(base: Image.Image, size: int) -> Image.Image:
    s      = size
    cx     = int(s * 0.500)
    cy     = int(s * 0.445)
    llen   = int(s * 0.580)
    lwid   = int(s * 0.320)
    angle  = -12            # inclinacion suave

    # ── Sombra de la hoja ─────────────────────────────────────────────────
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd     = ImageDraw.Draw(shadow)
    sd.polygon(
        leaf_poly(cx + int(s*0.022), cy + int(s*0.022), llen, lwid, angle),
        fill=(0, 0, 0, 70))
    base = Image.alpha_composite(
        base, shadow.filter(ImageFilter.GaussianBlur(int(s * 0.022))))

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld    = ImageDraw.Draw(layer)

    # ── Hoja (relleno verde + borde oscuro) ───────────────────────────────
    pts = leaf_poly(cx, cy, llen, lwid, angle)
    ld.polygon(pts, fill=LEAF_FILL)
    # Borde interior sutil
    ld.polygon(pts, outline=LEAF_DARK, width=max(1, int(s * 0.008)))

    # ── Nervio central ─────────────────────────────────────────────────────
    tip, base_pt = midrib(cx, cy, llen, angle)
    vw = max(2, int(s * 0.022))
    ld.line([tip, base_pt], fill=VEIN_COL, width=vw)

    # ── Nervios laterales (3 pares) ────────────────────────────────────────
    ar  = math.radians(angle)
    for frac, span in [(0.28, 0.28), (0.55, 0.32), (0.75, 0.26)]:
        # punto sobre el nervio central
        # tip es el extremo superior de la hoja
        # recorremos desde tip hacia base_pt en fraccion frac
        bx = tip[0] + frac * (base_pt[0] - tip[0])
        by = tip[1] + frac * (base_pt[1] - tip[1])
        half = llen * span * 0.30
        # direccion perpendicular al nervio
        px_dir =  math.cos(ar)
        py_dir =  math.sin(ar)
        ld.line([(int(bx), int(by)),
                 (int(bx - half * px_dir), int(by - half * py_dir))],
                fill=VEIN_COL, width=max(1, vw - 1))
        ld.line([(int(bx), int(by)),
                 (int(bx + half * px_dir), int(by + half * py_dir))],
                fill=VEIN_COL, width=max(1, vw - 1))

    # ── Manchas de mildiu polvoso ─────────────────────────────────────────
    # Posiciones fijas (seed=42) sobre la mitad superior de la hoja
    rng    = random.Random(42)
    n_spots = 8 if s >= 128 else 5
    for i in range(n_spots):
        # parametro a lo largo del nervio: 0 = tip, 1 = base
        t_nerve  = rng.uniform(0.05, 0.70)
        sx_base  = tip[0] + t_nerve * (base_pt[0] - tip[0])
        sy_base  = tip[1] + t_nerve * (base_pt[1] - tip[1])
        # desplazamiento lateral (dentro de la hoja)
        lat_max  = llen * (0.14 + 0.10 * math.sin(math.pi * t_nerve))
        lateral  = rng.uniform(-lat_max, lat_max)
        sx = sx_base + lateral * math.cos(ar)
        sy = sy_base + lateral * math.sin(ar)
        # tamaño de la mancha
        sr  = int(s * rng.uniform(0.035, 0.065))
        sw  = int(sr * rng.uniform(0.55, 0.85))
        rot = angle + rng.randint(-40, 40)
        pts_m = leaf_poly(int(sx), int(sy), sr * 2, sw * 2, rot, n=20)
        # Sombra interna suave
        ld.polygon(pts_m, fill=(*MILDEW_COL[:3], 80))
        # Mancha principal
        ld.polygon(pts_m, fill=MILDEW_COL)

    base = Image.alpha_composite(base, layer)
    return base


# ── Texto "PV" ────────────────────────────────────────────────────────────
def load_font(size: int) -> ImageFont.FreeTypeFont:
    for fc in ["C:/Windows/Fonts/bahnschrift.ttf",
               "C:/Windows/Fonts/segoeuib.ttf",
               "C:/Windows/Fonts/calibrib.ttf",
               "arialbd.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(fc, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_pv_text(base: Image.Image, size: int) -> Image.Image:
    if size < 72:       # no cabe texto en iconos pequenos
        return base
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld    = ImageDraw.Draw(layer)
    fs    = int(size * 0.175)
    font  = load_font(fs)
    label = "PV"
    bbox  = ld.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = size // 2 - tw // 2 - bbox[0]
    ty = int(size * 0.855) - th // 2 - bbox[1]
    # Sombra
    ld.text((tx + int(size*0.010), ty + int(size*0.010)),
            label, fill=(0, 0, 0, 120), font=font)
    ld.text((tx, ty), label, fill=GOLD, font=font)
    return Image.alpha_composite(base, layer)


# ── Constructor maestro ───────────────────────────────────────────────────
def make_icon(size: int) -> Image.Image:
    base = make_background(size)
    base = draw_leaf_mildew(base, size)
    base = draw_pv_text(base, size)
    return base


# ── Generar todos los tamanos ─────────────────────────────────────────────
SIZES_PNG = [72, 96, 128, 144, 152, 180, 192, 256, 384, 512]
SIZES_ICO = [16, 32, 48]

def run():
    os.makedirs("static", exist_ok=True)

    # Generar master 512 y reducir
    print("Generando master 512x512...")
    master = make_icon(512)

    ico_imgs = []
    for sz in sorted(set(SIZES_ICO + SIZES_PNG)):
        if sz == 512:
            img = master.copy()
        else:
            img = master.resize((sz, sz), Image.LANCZOS)

        if sz in SIZES_PNG:
            path = f"static/icon-{sz}.png"
            img.save(path, "PNG")
            print(f"  OK  {path}")

        if sz in SIZES_ICO:
            ico_imgs.append(img)

    # favicon.ico  (multi-size: 16 + 32 + 48)
    favicon_path = "static/favicon.ico"
    ico_imgs[0].save(
        favicon_path, format="ICO",
        sizes=[(s, s) for s in SIZES_ICO]
    )
    print(f"  OK  {favicon_path}  ({', '.join(str(s) for s in SIZES_ICO)} px)")

    print(f"\nTotal: {len(SIZES_PNG)} PNGs + 1 ICO  ->  static/")
    print("Actualiza index.html con:  <link rel='icon' href='/static/favicon.ico'>")


if __name__ == "__main__":
    run()
