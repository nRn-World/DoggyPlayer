"""Render the Doggy Player 9:16 launch video (frames piped straight into ffmpeg)."""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H, FPS = 1080, 1920, 30
FF = os.path.abspath(os.path.join("node_modules", "ffmpeg-static", "ffmpeg.exe"))
TMP = ".brag-tmp"
OUTDIR = "brag-output"
os.makedirs(OUTDIR, exist_ok=True)

INK = (247, 243, 238)
DIM = (166, 158, 148)
AMBER = (236, 164, 92)
AMBER_HI = (255, 202, 142)
BG_DARK = (14, 13, 15)

F_BLACK = "C:/Windows/Fonts/seguibl.ttf"
F_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
F_SEMI = "C:/Windows/Fonts/seguisb.ttf"
F_COND = "C:/Windows/Fonts/bahnschrift.ttf"

with open(os.path.join(TMP, "timing.json"), encoding="utf-8") as f:
    TT = json.load(f)
SCENES = TT["scenes"]
TOTAL = TT["total"]
TOTAL_F = int(round(TOTAL * FPS))


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def lerp(a, b, t):
    return a + (b - a) * t


_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


_tcache = {}


def text_img(text, fpath, size, color, ls=0):
    key = (text, fpath, size, color, ls)
    if key in _tcache:
        return _tcache[key]
    f = font(fpath, size)
    box_h = int(size * 1.46)
    if ls:
        widths = [f.getlength(c) for c in text]
        total = sum(widths) + ls * max(0, len(text) - 1)
        img = Image.new("RGBA", (int(math.ceil(total)) + 8, box_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = 4.0
        for c, w in zip(text, widths):
            d.text((x, 0), c, font=f, fill=color)
            x += w + ls
    else:
        img = Image.new("RGBA", (int(math.ceil(f.getlength(text))) + 8, box_h), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((4, 0), text, font=f, fill=color)
    _tcache[key] = img
    return img


def paste(frame, img, xy, alpha=1.0):
    if alpha <= 0.004:
        return
    x, y = int(round(xy[0])), int(round(xy[1]))
    if alpha >= 0.996:
        frame.alpha_composite(img, (x, y))
        return
    tmp = img.copy()
    tmp.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(tmp, (x, y))


def fit_size(lines, fpath, max_w, cap):
    size = cap
    while size > 40:
        f = font(fpath, size)
        if max(f.getlength(l) for l in lines) <= max_w:
            return size
        size -= 2
    return 40


def block(frame, lines, fpath, size, color, cx, top, lh, t, t0, stagger=0.11, dur=0.55,
          rise=46, alpha=1.0, ls=0, align="center"):
    """Draw headline lines with a per-line slide + fade. cx is the block centre."""
    for i, line in enumerate(lines):
        p = ease_out((t - t0 - i * stagger) / dur)
        if p <= 0:
            continue
        img = text_img(line, fpath, size, color, ls)
        x = cx - (img.width - 8) / 2 if align == "center" else cx
        y = top + i * lh + rise * (1 - p)
        paste(frame, img, (x - 4, y), alpha * p)
    return top + len(lines) * lh


# ---------------- background ----------------
def build_background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = (yy / H) ** 1.25
    top = np.array([8, 8, 10], dtype=np.float32)
    bot = np.array([26, 19, 15], dtype=np.float32)
    base = top[None, None, :] + (bot - top)[None, None, :] * v[..., None]

    dx = (xx - W * 0.5) / (W * 0.82)
    dy = (yy - H * 0.40) / (H * 0.55)
    r = np.sqrt(dx * dx + dy * dy)
    glow = np.clip(1 - r, 0, 1) ** 2.4
    base += glow[..., None] * np.array([232, 150, 78], dtype=np.float32) * 0.22

    # faint dotted grid
    grid = ((xx.astype(np.int32) % 60) < 1) & ((yy.astype(np.int32) % 60) < 1)
    base += grid[..., None].astype(np.float32) * np.array([26, 22, 19], dtype=np.float32)

    # vignette
    vx = (xx - W * 0.5) / (W * 0.62)
    vy = (yy - H * 0.5) / (H * 0.62)
    vig = np.clip(1 - np.sqrt(vx * vx + vy * vy), 0, 1) ** 0.55
    base *= (0.52 + 0.48 * vig)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


BG = build_background()


def glow_blob(radius, color):
    s = int(radius * 2)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2.6
    arr = np.zeros((s, s, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr)


BLOB_A = glow_blob(560, (255, 150, 70))
BLOB_B = glow_blob(430, (255, 190, 120))


# ---------------- brand watermark ----------------
def build_brand():
    logo = Image.open("Logo Bilder/logoW-cropped-no-bg1024x1024.png").convert("RGBA")
    logo = logo.crop(logo.split()[3].getbbox())
    lw = 46
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    txt = text_img("DOGGY PLAYER", F_COND, 30, (247, 243, 238, 205), 7)
    total = logo.width + 14 + (txt.width - 8)
    img = Image.new("RGBA", (total, max(logo.height, txt.height)), (0, 0, 0, 0))
    img.alpha_composite(logo, (0, (img.height - logo.height) // 2))
    img.alpha_composite(txt, (logo.width + 14 - 4, (img.height - txt.height) // 2))
    return img


BRAND = build_brand()


# ---------------- cards ----------------
_card_cache = {}


def rounded_mask(w, h, r):
    key = ("mask", w, h, r)
    if key not in _card_cache:
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
        _card_cache[key] = m
    return _card_cache[key]


def drop_shadow(w, h, r, blur=34, alpha=150):
    key = ("shadow", w, h, r, blur, alpha)
    if key in _card_cache:
        return _card_cache[key]
    pad = blur * 2
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad + 12, pad + w, pad + h + 12], radius=r, fill=(0, 0, 0, alpha))
    img = img.filter(ImageFilter.GaussianBlur(blur))
    _card_cache[key] = img
    return img


class Shot:
    def __init__(self, path, box_w, box_h, hi=2.0):
        img = Image.open(path).convert("RGB")
        self.aspect = img.width / img.height
        self.box = (box_w, box_h)
        scale = max(box_w * hi / img.width, box_h * hi / img.height)
        self.hi = img.resize((max(box_w, int(img.width * scale)), max(box_h, int(img.height * scale))), Image.LANCZOS)

    def window(self, zoom, anchor, drift=(0.0, 0.0)):
        iw, ih = self.hi.size
        ww = max(8, min(iw, int(round(iw / zoom))))
        hh = max(8, min(ih, int(round(ih / zoom))))
        cx = anchor[0] * iw + drift[0] * iw * 0.5
        cy = anchor[1] * ih + drift[1] * ih * 0.5
        x0 = int(clamp(cx - ww / 2, 0, iw - ww))
        y0 = int(clamp(cy - hh / 2, 0, ih - hh))
        return (x0, y0, x0 + ww, y0 + hh)

    def render(self, p, mode="pan", anchor=(0.5, 0.5), z0=1.0, z1=1.06, angle=0.0, bright=1.0):
        if mode == "zoom":
            pz = ease_io(p)
            zoom = lerp(1.02, z1, pz)
            drift = (lerp(-0.05, 0.05, pz), 0)
        elif mode == "hold":
            zoom = z1
            drift = (0, 0)
        else:
            zoom = lerp(z0, z1, p)
            drift = (lerp(-0.035, 0.035, p), lerp(0.012, -0.012, p))
        crop = self.hi.crop(self.window(zoom, anchor, drift))
        img = crop.resize(self.box, Image.LANCZOS)
        if angle:
            img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(0, 0, 0))
        if bright != 1.0:
            img = ImageEnhance.Brightness(img).enhance(bright)
        img = img.convert("RGBA")
        img.putalpha(rounded_mask(*self.box, 26))
        return img


def card_size(src_aspect, box_w=940, max_h=580, min_h=380):
    h = int(clamp(box_w / src_aspect, min_h, max_h))
    return box_w, h


# ---------------- per-scene data ----------------
LOOK = {
    "hook": dict(layout="hero"),
    "seek": dict(
        layout="standard", kicker="01  \u2014  SEEKING",
        head=["SEEK", "ANYWHERE."],
        chips=["MKV  ·  MP4  ·  AVI  ·  TS", "ONE KEY PRESS = ONE SEEK"],
        shots=[dict(img="Screenshot/Sc1.png", mode="pan", anchor=(0.66, 0.5), z0=1.04, z1=1.12),
               dict(img="Screenshot/Live.png", mode="pan", anchor=(0.5, 0.45), z0=1.10, z1=1.0)],
        switch=0.5,
    ),
    "zoom": dict(
        layout="standard", kicker="02  \u2014  ZOOM",
        head=["ZOOM INTO", "THE FRAME."],
        chips=["SCROLL TO ZOOM", "SHIFT + DRAG A BOX"],
        shots=[dict(img="Screenshot/Live.png", mode="zoom", anchor=(0.42, 0.42), z1=2.7)],
    ),
    "fix": dict(
        layout="standard", kicker="03  \u2014  REPAIR",
        head=["SIDEWAYS?", "TOO DARK?"],
        chips=["ROTATE", "BRIGHTNESS 50\u2013150%", "LOCKED PER FILE"],
        shots=[dict(img="Screenshot/Live.png", mode="rotate", anchor=(0.5, 0.45))],
    ),
    "subs": dict(
        layout="standard", kicker="04  \u2014  EVERYTHING ELSE",
        head=["SUBTITLES.", "PLAYLISTS.", "EQUALIZER."],
        chips=["SRT  ·  VTT  ·  ASS", "EQ \u00b112 dB"],
        shots=[dict(img="Screenshot/Sc1.png", mode="pan", anchor=(0.62, 0.5), z0=1.0, z1=1.10)],
    ),
    "iptv": dict(
        layout="standard", kicker="05  \u2014  LIVE TV",
        head=["LIVE TV,", "BUILT IN."],
        chips=["XTREAM CODES", "M3U", "EPG"],
        shots=[dict(img="Screenshot/IPTV.png", mode="pan", anchor=(0.5, 0.5), z0=1.0, z1=1.08),
               dict(img="Screenshot/Movie.png", mode="pan", anchor=(0.4, 0.42), z0=1.10, z1=1.0)],
        switch=0.62,
    ),
    "private": dict(layout="statement"),
    "cta": dict(layout="cta"),
}

_sources = {}


def shot_for(spec, index, box):
    key = (spec["img"], index, box)
    if key not in _sources:
        _sources[key] = Shot(spec["img"], *box)
    return _sources[key]


LOGO = Image.open("Logo Bilder/logoW-cropped-no-bg1024x1024.png").convert("RGBA")
LOGO = LOGO.crop(LOGO.split()[3].getbbox())
_logos = {}


def logo_at(width):
    if width not in _logos:
        _logos[width] = LOGO.resize((width, int(LOGO.height * width / LOGO.width)), Image.LANCZOS)
    return _logos[width]


def chip(text, fsize=30, color=INK, alpha=255, border=(255, 255, 255, 46), bg=(255, 255, 255, 12)):
    txt = text_img(text, F_COND, fsize, color + (alpha,) if len(color) == 3 else color, 3)
    tw, th = txt.width - 8, fsize + 26
    pad = 24
    img = Image.new("RGBA", (tw + pad * 2, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, th - 1], radius=th // 2, fill=bg, outline=border, width=2)
    img.alpha_composite(txt, (pad - 4, (th - txt.height) // 2))
    return img


def chip_row(texts, cy, t, t0, alpha=1.0):
    imgs = [chip(x) for x in texts]
    gap = 14
    total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    if total > 980:
        imgs = [chip(x, 26) for x in texts]
        total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    x = (W - total) / 2
    for i, im in enumerate(imgs):
        p = ease_out((t - t0 - i * 0.09) / 0.45)
        if p > 0:
            paste(FRAME, im, (x, cy + 16 * (1 - p)), alpha * p)
        x += im.width + gap


FRAME = None


def caption_words(scene):
    words = scene["words"]
    groups, cur, cur_w = [], [], 0.0
    f = font(F_BOLD, 54)
    space = 15
    prev_end = None
    for w in words:
        gap = (w["start"] - prev_end) if prev_end is not None else 0.0
        if cur and (cur_w + space + f.getlength(w["w"]) > 880 or len(cur) >= 6
                    or (gap > 0.36 and len(cur) >= 3)):
            groups.append(cur)
            cur, cur_w = [], 0.0
        cur_w += (space if cur else 0) + f.getlength(w["w"])
        cur.append(w)
        prev_end = w["end"]
    if cur:
        groups.append(cur)
    return groups


def draw_caption(scene, t):
    groups = _cap_cache.get(scene["key"])
    if groups is None:
        groups = caption_words(scene)
        _cap_cache[scene["key"]] = groups
    for g in groups:
        gs, ge = g[0]["start"] - 0.08, g[-1]["end"] + 0.28
        if not (gs <= t <= ge):
            continue
        f = font(F_BOLD, 54)
        space = 15
        widths = [f.getlength(w["w"]) for w in g]
        total = sum(widths) + space * (len(g) - 1)
        x = (W - total) / 2
        appear = ease_out((t - gs) / 0.18)
        for w, ww in zip(g, widths):
            active = w["start"] - 0.02 <= t <= w["end"] + 0.10
            col = AMBER_HI if active else (223, 216, 208)
            img = text_img(w["w"], F_BOLD, 54, col)
            paste(FRAME, img, (x - 4, CAPTION_Y + 12 * (1 - appear)), appear)
            x += ww + space
        return


_cap_cache = {}


def draw_chrome(t):
    paste(FRAME, BRAND, ((W - BRAND.width) / 2, 92), 0.9 * ease_out(t / 0.6))
    p = clamp(t / TOTAL)
    bar_y = 1852
    d = ImageDraw.Draw(FRAME)
    d.rounded_rectangle([80, bar_y, W - 80, bar_y + 5], radius=3, fill=(255, 255, 255, 26))
    if p > 0.002:
        d.rounded_rectangle([80, bar_y, 80 + (W - 160) * p, bar_y + 5], radius=3, fill=AMBER + (235,))


CAPTION_Y = 1576


def render_shot(sp, si, tl, scene_dur, box):
    s2 = shot_for(sp, si, box)
    p = clamp(tl / scene_dur)
    if sp["mode"] == "zoom":
        return s2.render(p, "zoom", sp["anchor"], z1=sp.get("z1", 2.5))
    if sp["mode"] == "rotate":
        e = clamp((p - 0.24) / 0.44)
        return s2.render(p, "hold", anchor=sp["anchor"], z1=1.12,
                         angle=lerp(-10, 0, ease_io(e)), bright=lerp(0.42, 1.0, ease_io(e)))
    return s2.render(p, "pan", sp["anchor"], sp.get("z0", 1.0), sp.get("z1", 1.05))


def scene_standard(key, sc, tl):
    look = LOOK[key]
    t = sc["start"] + tl
    kp = ease_out((tl - 0.05) / 0.5)
    kimg = text_img(look["kicker"], F_COND, 32, AMBER)
    paste(FRAME, kimg, ((W - kimg.width) / 2 - 4, 268 + 14 * (1 - kp)), kp)

    head = look["head"]
    size = fit_size(head, F_BLACK, 900, 112)
    lh = int(size * 1.03)
    head_bottom = block(FRAME, head, F_BLACK, size, INK + (255,), W / 2, 322, lh, t,
                        sc["start"] + 0.10, stagger=0.12)

    # card geometry: screenshots stay uncropped, all shots share one centre
    specs = look["shots"]
    ch = 104
    region_top = head_bottom + 40
    region_bot = CAPTION_Y - 40 - 24 - ch
    card_h_max = region_bot - region_top
    boxes = []
    for sp in specs:
        pr = Image.open(sp["img"])
        a = pr.width / pr.height
        h = min(940 / a, card_h_max, 660)
        w = h * a
        if w > 960:
            w, h = 960, 960 / a
        boxes.append((int(w), int(h)))
    h_max = max(b[1] for b in boxes)
    centre_y = (region_top + region_bot) / 2
    chip_y = int(centre_y + h_max / 2 + 34)

    idx, mix_p = 0, 0.0
    if len(specs) > 1:
        sw = sc["dur"] * look["switch"]
        if tl >= sw:
            idx = 1
            mix_p = clamp((tl - sw) / 0.32)

    bw, bh = boxes[idx]
    cx = (W - bw) / 2
    enter = ease_out(tl / 0.55)
    cy = int(centre_y - bh / 2 + (1 - enter) * 60)

    shadow = drop_shadow(bw, bh, 26)
    pad = shadow.width - bw
    paste(FRAME, shadow, (cx - pad / 2, cy - pad / 2), 0.85 * enter)

    img = render_shot(specs[idx], idx, tl, sc["dur"], (bw, bh))
    paste(FRAME, img, (cx, cy), enter * (mix_p if idx else 1.0))

    if enter > 0.02:
        d = ImageDraw.Draw(FRAME)
        d.rounded_rectangle([cx, cy, cx + bw - 1, cy + bh - 1], radius=26,
                            outline=(255, 255, 255, int(34 * enter)), width=2)

    chip_row(look["chips"], chip_y, t, sc["start"] + 0.75, alpha=enter)


def scene_hero(key, sc, tl):
    t = sc["start"] + tl
    lg = logo_at(360)
    p = ease_out(tl / 0.6)
    fl = math.sin(tl * 1.6) * 6
    paste(FRAME, BLOB_A, (W / 2 - BLOB_A.width / 2, 330 + fl - 120), 0.30 * p)
    paste(FRAME, lg, ((W - lg.width) / 2, 300 + (1 - p) * 40 + fl), p)
    y = block(FRAME, ["DOGGY"], F_BLACK, 168, INK + (255,), W / 2, 585, 178, t, sc["start"] + 0.28)
    block(FRAME, ["PLAYER"], F_BLACK, 168, AMBER + (255,), W / 2, y - 12, 178, t, sc["start"] + 0.40)
    sub = text_img("A DESKTOP VIDEO PLAYER  \u00b7  FREE FOR PERSONAL USE", F_COND, 30, DIM + (255,), 4)
    sp = ease_out((tl - 1.05) / 0.55)
    paste(FRAME, sub, ((W - sub.width) / 2 - 4, 1078 + 22 * (1 - sp)), sp)
    tease = text_img("SEEK   \u00b7   ZOOM   \u00b7   SUBTITLES   \u00b7   IPTV", F_COND, 28, (214, 205, 196, 210), 5)
    tp = ease_out((tl - 1.55) / 0.55)
    paste(FRAME, tease, ((W - tease.width) / 2 - 4, 1210 + 20 * (1 - tp)), tp)


def scene_statement(key, sc, tl):
    t = sc["start"] + tl
    cx, cy = W / 2, 780
    # orbiting ring
    ring = Image.new("RGBA", (620, 620), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    for rr, al, wd in ((280, 26, 2), (215, 18, 2)):
        d.ellipse([310 - rr, 310 - rr, 310 + rr, 310 + rr], outline=(255, 255, 255, al), width=wd)
    rot = (tl * 70) % 360
    d.arc([310 - 280, 310 - 280, 310 + 280, 310 + 280], rot, rot + 74, fill=AMBER + (200,), width=5)
    d.arc([310 - 215, 310 - 215, 310 + 215, 310 + 215], rot + 180, rot + 232, fill=AMBER + (140,), width=4)
    paste(FRAME, ring, (cx - 310, cy - 310), 0.95 * ease_out(tl / 0.6))
    block(FRAME, ["NOTHING LEAVES"], F_BLACK, 96, INK + (255,), W / 2, 690, 104, t, sc["start"] + 0.12)
    block(FRAME, ["YOUR MACHINE."], F_BLACK, 96, AMBER + (255,), W / 2, 794, 104, t, sc["start"] + 0.26)
    sub = text_img("ONE OPTIONAL PING A DAY \u2014 THAT'S IT", F_COND, 30, DIM + (255,), 5)
    sp = ease_out((tl - 0.9) / 0.5)
    paste(FRAME, sub, ((W - sub.width) / 2 - 4, 960 + 20 * (1 - sp)), sp)
    chip_row(["NO ACCOUNT", "NO UPLOADS", "PING CAN BE OFF"], 1090, t, sc["start"] + 1.15)


def scene_cta(key, sc, tl):
    t = sc["start"] + tl
    lg = logo_at(260)
    p = ease_out(tl / 0.55)
    paste(FRAME, BLOB_A, (W / 2 - BLOB_A.width / 2, 420), 0.26 * p)
    paste(FRAME, lg, ((W - lg.width) / 2, 400 + (1 - p) * 30), p)
    y = block(FRAME, ["FREE FOR"], F_BLACK, 118, INK + (255,), W / 2, 660, 124, t, sc["start"] + 0.22)
    block(FRAME, ["PERSONAL USE"], F_BLACK, 118, AMBER + (255,), W / 2, y - 8, 124, t, sc["start"] + 0.34)
    chip_row(["WINDOWS", "macOS", "LINUX"], 1000, t, sc["start"] + 0.9)
    # url chip
    url = text_img("GITHUB.COM/nRn-World/Doggy-Player", F_COND, 34, (255, 255, 255, 240), 2)
    pad = 40
    cw, ch = url.width - 8 + pad * 2, 96
    box = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dd = ImageDraw.Draw(box)
    dd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=ch // 2, fill=AMBER + (255,))
    box.alpha_composite(url, (pad - 4, (ch - url.height) // 2))
    up = ease_out((tl - 1.35) / 0.5)
    paste(FRAME, box, ((W - cw) / 2, 1140 + 24 * (1 - up)), up)
    hint = text_img("DOWNLOAD THE LATEST RELEASE", F_COND, 26, (200, 192, 182, 200), 6)
    hp = ease_out((tl - 1.9) / 0.5)
    paste(FRAME, hint, ((W - hint.width) / 2 - 4, 1290 + 18 * (1 - hp)), hp)


def render_scene(i, tl):
    sc = SCENES[i]
    key = sc["key"]
    look = LOOK[key]
    if look["layout"] == "hero":
        scene_hero(key, sc, tl)
    elif look["layout"] == "statement":
        scene_statement(key, sc, tl)
    elif look["layout"] == "cta":
        scene_cta(key, sc, tl)
    else:
        scene_standard(key, sc, tl)


XFADE = 0.38


def frame_at(t):
    global FRAME
    FRAME = BG.copy()
    # moving glow
    FRAME.alpha_composite(BLOB_A, (int(80 + 40 * math.sin(t * 0.31)), int(1000 + 60 * math.cos(t * 0.23))))
    FRAME.alpha_composite(BLOB_B, (int(560 + 50 * math.cos(t * 0.19)), int(220 + 40 * math.sin(t * 0.27))))

    i = 0
    for j, sc in enumerate(SCENES):
        if t >= sc["start"]:
            i = j
    tl = t - SCENES[i]["start"]

    if i > 0 and tl < XFADE:
        prev_t = SCENES[i - 1]["dur"] - 0.001
        FRAME = BG.copy()
        FRAME.alpha_composite(BLOB_A, (int(80 + 40 * math.sin(prev_t * 0.31)), int(1000 + 60 * math.cos(prev_t * 0.23))))
        FRAME.alpha_composite(BLOB_B, (int(560 + 50 * math.cos(prev_t * 0.19)), int(220 + 40 * math.sin(prev_t * 0.27))))
        render_scene(i - 1, prev_t)
        a = FRAME.convert("RGB")
        FRAME = BG.copy()
        FRAME.alpha_composite(BLOB_A, (int(80 + 40 * math.sin(t * 0.31)), int(1000 + 60 * math.cos(t * 0.23))))
        FRAME.alpha_composite(BLOB_B, (int(560 + 50 * math.cos(t * 0.19)), int(220 + 40 * math.sin(t * 0.27))))
        render_scene(i, tl)
        b = FRAME.convert("RGB")
        shift = int(H * ease_io(tl / XFADE))
        canvas = Image.new("RGB", (W, H))
        canvas.paste(a, (0, -shift))
        canvas.paste(b, (0, H - shift))
        FRAME = canvas.convert("RGBA")
    else:
        render_scene(i, tl)
        draw_caption(SCENES[i], t)

    draw_chrome(t)
    return FRAME


def main():
    out = os.path.join(OUTDIR, "doggy-player-9x16.mp4")
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", os.path.join(TMP, "mix.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.2", "-g", "60",
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    step = 10
    for n in range(TOTAL_F):
        fr = frame_at(n / FPS)
        proc.stdin.write(fr.convert("RGB").tobytes())
        if n % (FPS * step) == 0:
            print(f"  {n}/{TOTAL_F}  ({n / TOTAL_F * 100:.0f}%)", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    print("ffmpeg exit", rc, "->", out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
