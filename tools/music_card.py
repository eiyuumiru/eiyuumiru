#!/usr/bin/env python3
"""Render an Apple Music "now playing" style banner from a Spotify track link.

    python tools/music_card.py <spotify-track-url> --layout horizontal|vertical \
        [--out-dir assets] [--update-readme README.md]

The track title, artist and cover art come from the public Open Graph tags of the
Spotify track page (no API key needed). The banner is drawn with Pillow using
San Francisco, which ships with macOS (the GitHub workflow therefore runs on a
macOS runner). SF is never copied into this repository.
"""
import argparse, glob, html, io, os, re, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ICON = HERE / "apple-music-icon.png"
TRACK_RE = re.compile(r"^https://open\.spotify\.com/(?:intl-[a-z]{2,5}/)?track/([A-Za-z0-9]{10,30})(?:[/?#].*)?$")
MARK_START, MARK_END = "<!-- music-card:start -->", "<!-- music-card:end -->"
SF_PATHS = ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/SFNSRounded.ttf"]
FALLBACK_FONTS = ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
S = 2  # render at 2x for crisp edges
DISPLAY_WIDTH = {"horizontal": 520, "vertical": 300}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=25).read()


def track_info(url):
    m = TRACK_RE.match(url.strip())
    if not m:
        sys.exit("error: expected a Spotify track link, e.g. https://open.spotify.com/track/<id>")
    tid = m.group(1)
    page = fetch(f"https://open.spotify.com/track/{tid}").decode("utf-8", "ignore")

    def og(key):
        hit = re.search(r'<meta property="og:%s" content="([^"]*)"' % key, page)
        if not hit:
            sys.exit(f"error: could not read '{key}' from the Spotify page")
        return html.unescape(hit.group(1))

    cover = Image.open(io.BytesIO(fetch(og("image")))).convert("RGB")
    return tid, og("title"), og("description").split(" · ")[0], cover


def sf(pt, weight):
    """San Francisco (variable) at `pt` points, `weight` 100-900."""
    for path in SF_PATHS[:1]:
        if os.path.exists(path):
            f = ImageFont.truetype(path, int(pt * S))
            axes = {a["name"]: a for a in f.get_variation_axes()}
            vals = []
            for name, a in axes.items():
                n = name.decode() if isinstance(name, bytes) else name
                if n == "Weight": vals.append(weight)
                elif n == "Optical Size": vals.append(max(a["minimum"], min(a["maximum"], pt)))
                else: vals.append(a["default"])
            f.set_variation_by_axes(vals)
            return f
    for path in FALLBACK_FONTS:
        if os.path.exists(path):
            print("warning: San Francisco not found, using", path, file=sys.stderr)
            return ImageFont.truetype(path, int(pt * S))
    return ImageFont.load_default()


def fit(d, text, font, width):
    if d.textlength(text, font=font) <= width:
        return text
    while text and d.textlength(text + "…", font=font) > width:
        text = text[:-1]
    return text.rstrip() + "…"


def rr_mask(w, h, r, k=4):
    m = Image.new("L", (w * k, h * k), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * k - 1, h * k - 1), r * k, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def wash(cover, w, h):
    """Blurred, saturated colour wash taken from the cover (Apple Music look)."""
    side = max(w, h)
    bg = cover.resize((side, side), Image.LANCZOS)
    bg = bg.crop(((side - w) // 2, (side - h) // 2, (side - w) // 2 + w, (side - h) // 2 + h))
    bg = bg.filter(ImageFilter.GaussianBlur(70))
    return ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.5)).enhance(0.5)


def controls(size, cx, cy, p):
    """Previous / pause / next drawn with rounded joins, like SF Symbols."""
    K = 4
    layer = Image.new("RGBA", (size[0] * K, size[1] * K), (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    white = (255, 255, 255, 240)
    r = p["r"] * S

    def tri(x, direction):
        w, h = p["tw"] * S, p["th"] * S
        x0, x1 = x - w / 2 + r * 0.9, x + w / 2 - r * 0.9
        y0, y1 = cy - h / 2 + r * 0.9, cy + h / 2 - r * 0.9
        pts = [(x0, y0), (x0, y1), (x1, cy)] if direction > 0 else [(x1, y0), (x1, y1), (x0, cy)]
        pts = [(a * K, b * K) for a, b in pts]
        g.polygon(pts, fill=white)
        g.line(pts + [pts[0]], fill=white, width=int(2 * r * K), joint="curve")
        for a, b in pts:
            g.ellipse((a - r * K, b - r * K, a + r * K, b + r * K), fill=white)

    def bar(x0, x1):
        g.rounded_rectangle((x0 * K, (cy - p["bh"] * S) * K, x1 * K, (cy + p["bh"] * S) * K),
                            p["br"] * S * K, fill=white)

    tw, off, gap = p["tw"] * S, p["off"] * S, p["gap"] * S
    px, nx = cx - gap, cx + gap
    tri(px - tw / 2 + off, -1); tri(px + tw / 2 + off, -1)
    tri(nx - tw / 2 - off, 1); tri(nx + tw / 2 - off, 1)
    bar(cx - p["b_out"] * S, cx - p["b_in"] * S); bar(cx + p["b_in"] * S, cx + p["b_out"] * S)
    return layer.resize(size, Image.LANCZOS)


def more_button(d, cx, cy, radius, spread):
    d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(255, 255, 255, 55))
    for k in (-spread, 0, spread):
        d.ellipse((cx + k * S - 2 * S, cy - 2 * S, cx + k * S + 2 * S, cy + 2 * S), fill=(255, 255, 255, 235))


def render(layout, title, artist, cover):
    horizontal = layout == "horizontal"
    if horizontal:
        W, H, R, PAD = 620 * S, 188 * S, 28 * S, 22 * S
        cs, cx0, cy0, cr = H - 2 * PAD, 22 * S, 22 * S, 12 * S
    else:
        W, H, R, PAD = 340 * S, 538 * S, 30 * S, 28 * S
        cs, cx0, cy0, cr = W - 2 * PAD, 28 * S, 64 * S, 14 * S

    card = wash(cover, W, H).convert("RGBA")
    card.putalpha(rr_mask(W, H, R))

    # cover art + soft shadow
    dy, blur = (8, 12) if horizontal else (10, 14)
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((cx0, cy0 + dy * S, cx0 + cs, cy0 + cs + dy * S), cr, fill=150)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(blur * S)))
    card = Image.alpha_composite(card, shadow)
    cv = cover.resize((cs, cs), Image.LANCZOS).convert("RGBA")
    cv.putalpha(rr_mask(cs, cs, cr))
    card.alpha_composite(cv, (cx0, cy0))

    # Apple Music icon + header label
    isz = (22 if horizontal else 24) * S
    hx = cx0 + cs + 24 * S if horizontal else PAD
    hy = PAD if horizontal else 24 * S
    if ICON.exists():
        card.alpha_composite(Image.open(ICON).convert("RGBA").resize((isz, isz), Image.LANCZOS), (hx, hy))

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.text((hx + isz + 8 * S + (1 * S if not horizontal else 0), hy + isz // 2), "Recently favourite",
           font=sf(14 if horizontal else 15, 640), fill=(255, 255, 255, 210), anchor="lm")

    if horizontal:
        xr = W - PAD
        more_button(d, xr - 13 * S, PAD + 11 * S, 13 * S, 6)
        tf, af = sf(21, 620), sf(17, 400)
        tx, ty = hx, PAD + 36 * S
        maxw = xr - tx
        d.text((tx, ty), fit(d, title, tf, maxw), font=tf, fill=(255, 255, 255, 255))
        d.text((tx, ty + 28 * S), fit(d, artist, af, maxw), font=af, fill=(255, 255, 255, 150))
        bx0, bx1, by = tx, xr, ty + 64 * S
        ctrl_cx, ctrl_cy = (tx + xr) / 2, by + 38 * S
        p = dict(r=2.6, tw=16, th=20, off=2, gap=66, bh=13, br=3.0, b_in=2.5, b_out=12)
    else:
        tf, af = sf(21, 620), sf(19, 400)
        tx, ty = PAD, cy0 + cs + 24 * S
        maxw = W - 2 * PAD - 44 * S
        d.text((tx, ty), fit(d, title, tf, maxw), font=tf, fill=(255, 255, 255, 255))
        d.text((tx, ty + 30 * S), fit(d, artist, af, maxw), font=af, fill=(255, 255, 255, 150))
        more_button(d, W - PAD - 15 * S, ty + 24 * S, 15 * S, 7)
        bx0, bx1, by = PAD, W - PAD, ty + 70 * S
        ctrl_cx, ctrl_cy = W / 2, by + 52 * S
        p = dict(r=3.2, tw=19, th=24, off=3, gap=80, bh=16, br=3.6, b_in=3, b_out=14)

    ph = 5 * S  # static progress bar
    d.rounded_rectangle((bx0, by, bx1, by + ph), ph // 2, fill=(255, 255, 255, 70))
    d.rounded_rectangle((bx0, by, bx0 + int((bx1 - bx0) * 0.38), by + ph), ph // 2, fill=(255, 255, 255, 235))
    ov = Image.alpha_composite(ov, controls((W, H), ctrl_cx, ctrl_cy, p))
    card = Image.alpha_composite(card, ov)

    border = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((0, 0, W - 1, H - 1), R, outline=(255, 255, 255, 40), width=2)
    card = Image.alpha_composite(card, border)
    card.putalpha(Image.composite(card.getchannel("A"), Image.new("L", (W, H), 0), rr_mask(W, H, R)))
    return card


def update_readme(path, rel_png, url, alt, layout):
    text = Path(path).read_text(encoding="utf-8")
    block = (f'{MARK_START}\n<a href="{url}">\n'
             f'  <img src="./{rel_png}" width="{DISPLAY_WIDTH[layout]}" alt="{html.escape(alt, quote=True)}">\n'
             f'</a>\n{MARK_END}')
    pattern = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), re.S)
    if not pattern.search(text):
        sys.exit(f"error: {path} has no {MARK_START} ... {MARK_END} markers")
    Path(path).write_text(pattern.sub(lambda _: block, text, count=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
    ap.add_argument("--out-dir", default="assets")
    ap.add_argument("--update-readme")
    a = ap.parse_args()

    tid, title, artist, cover = track_info(a.url)
    print(f"track: {title} | artist: {artist} | layout: {a.layout}")
    card = render(a.layout, title, artist, cover)

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"music-{tid}-{a.layout}.png"
    for old in glob.glob(str(out_dir / "music-*.png")):  # one banner at a time
        if Path(old) != out:
            os.remove(old)
    card.save(out, optimize=True)
    print("wrote", out, card.size)

    if a.update_readme:
        update_readme(a.update_readme, out.as_posix(), f"https://open.spotify.com/track/{tid}",
                      f"{title} by {artist}", a.layout)
        print("updated", a.update_readme)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"title={title.replace(chr(10), ' ')}\nartist={artist.replace(chr(10), ' ')}\n")


if __name__ == "__main__":
    main()
