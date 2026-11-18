"""Builds the prologue signage / screen textures (PNG) for the Veyra Central dressing pass.

    python3 Tools/signage_build.py <logo.png>

Writes Art/Signage/T_NV_*.png. All text is English and names stops on the Crown Line through Veyra.
Fonts are the project UI fonts in Content/UI/Fonts."""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Art", "Signage")
FONTS = os.path.join(ROOT, "Content", "UI", "Fonts")
os.makedirs(OUT, exist_ok=True)

def F(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)
RB = lambda s: F("Rajdhani-Bold.ttf", s)
RS = lambda s: F("Rajdhani-SemiBold.ttf", s)
RM = lambda s: F("Rajdhani-Medium.ttf", s)
ORB = lambda s: F("Orbitron.ttf", s)
MONO = lambda s: F("ShareTechMono-Regular.ttf", s)

CYAN = (70, 225, 255)
GOLD = (255, 196, 92)
ORANGE = (255, 120, 40)
MAGENTA = (255, 70, 200)
GREY = (120, 130, 140)
WHITE = (232, 240, 245)
RED = (255, 70, 60)
BG = (6, 10, 16)

# Crown Line, south to north. (name, sub-label, interchange)
CROWN = [
    ("VEYRA CENTRAL", "you are here", None),
    ("MERIDIAN EXCHANGE", "financial district", "NOVA"),
    ("KESTREL ARCADE", "markets  ·  hotels", "GUTTER"),
    ("ETHERION PLAZA", "Etherion campus", None),
    ("AION SPIRE", "civic oversight", None),
    ("GLASS CROWN", "Crown Sector  ·  Directorate", None),
]
NOVA = ["RAINMARKET", "NEON ROW", "MERIDIAN EXCHANGE", "ECHO DOCKS"]

def scanlines(im, alpha=22, step=4):
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, im.height, step):
        d.line([(0, y), (im.width, y)], fill=(0, 0, 0, alpha))
    return im

def text_c(d, xy, s, font, fill):
    w = d.textlength(s, font=font)
    d.text((xy[0] - w / 2, xy[1]), s, font=font, fill=fill)

def frame(d, w, h, col, inset=14, notch=34):
    pts = [(inset + notch, inset), (w - inset, inset), (w - inset, h - inset - notch), (w - inset - notch, h - inset),
           (inset, h - inset), (inset, inset + notch), (inset + notch, inset)]
    d.line(pts, fill=col, width=4)

def line_map(d, x0, y0, x1, y1, scale=1.0):
    """Crown Line runs bottom to top along a gentle diagonal; Nova Line crosses at Meridian; the Gutter link spurs off
    at Kestrel (suspended)."""
    n = len(CROWN)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = x0 + (x1 - x0) * (0.30 + 0.25 * math.sin(t * math.pi * 0.9))
        y = y1 - (y1 - y0) * t
        pts.append((x, y))
    # Nova Line (magenta) through Meridian
    mx, my = pts[1]
    nova = [(x0 + 10, my + 120 * scale), (mx - 160 * scale, my + 40 * scale), (mx, my), (mx + 220 * scale, my - 60 * scale), (x1 - 10, my - 60 * scale)]
    d.line(nova, fill=MAGENTA, width=int(10 * scale), joint="curve")
    nova_stops = [nova[0], nova[1], nova[3], nova[4]]
    for (sx, sy), name, dy in zip(nova_stops, ["RAINMARKET", "NEON ROW", "ECHO DOCKS", ""], (-48, -48, 16, 0)):
        if not name:
            continue
        r = 11 * scale
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=BG, outline=MAGENTA, width=int(5 * scale))
        d.text((sx - 10 * scale, sy + dy * scale), name, font=RS(int(26 * scale)), fill=(255, 150, 225))
    # Gutter link (grey dashed, suspended) from Kestrel
    kx, ky = pts[2]
    gx, gy = x1 - 50 * scale, ky - 40 * scale
    segs = 9
    for s in range(segs):
        if s % 2 == 0:
            a = s / segs; b = (s + 1) / segs
            d.line([(kx + (gx - kx) * a, ky + (gy - ky) * a), (kx + (gx - kx) * b, ky + (gy - ky) * b)], fill=GREY, width=int(8 * scale))
    r = 11 * scale
    d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=BG, outline=GREY, width=int(5 * scale))
    d.text((gx - 170 * scale, gy - 74 * scale), "THE GUTTER", font=RB(int(26 * scale)), fill=GREY)
    d.text((gx - 170 * scale, gy - 46 * scale), "service suspended", font=RM(int(20 * scale)), fill=(150, 90, 80))
    # Crown Line itself (gold core with cyan edge)
    d.line(pts, fill=CYAN, width=int(18 * scale), joint="curve")
    d.line(pts, fill=GOLD, width=int(8 * scale), joint="curve")
    for i, ((x, y), (name, sub, ic)) in enumerate(zip(pts, CROWN)):
        here = i == 0
        end = i == n - 1
        r = (19 if (here or end or ic) else 14) * scale
        d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE if ic else BG, outline=WHITE, width=int(6 * scale))
        if here:
            # pin
            px, py = x, y - 52 * scale
            d.ellipse([px - 20 * scale, py - 20 * scale, px + 20 * scale, py + 20 * scale], fill=(240, 255, 90))
            d.polygon([(px - 15 * scale, py + 10 * scale), (px + 15 * scale, py + 10 * scale), (px, py + 36 * scale)], fill=(240, 255, 90))
            d.ellipse([px - 7 * scale, py - 7 * scale, px + 7 * scale, py + 7 * scale], fill=BG)
        tx = x + 34 * scale
        d.text((tx, y - 24 * scale), name, font=RB(int(36 * scale)), fill=(255, 235, 190) if not here else (240, 255, 120))
        d.text((tx, y + 12 * scale), sub, font=RM(int(22 * scale)), fill=(150, 205, 225))
    return pts

def departures_board():
    W, H = 1024, 1760
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # header
    d.rectangle([0, 0, W, 150], fill=(14, 22, 32))
    d.polygon([(0, 0), (520, 0), (470, 150), (0, 150)], fill=(255, 92, 40))
    d.text((40, 30), "CROWN LINE", font=RB(92), fill=(20, 10, 6))
    d.text((560, 34), "DEPARTURES", font=ORB(50), fill=CYAN)
    d.text((560, 92), "VEYRA CENTRAL  ·  STATION 01", font=RS(30), fill=(150, 205, 225))
    # map panel
    d.text((48, 180), "LINE MAP", font=ORB(28), fill=CYAN)
    d.line([(48, 222), (W - 48, 222)], fill=(40, 70, 90), width=2)
    line_map(d, 40, 300, W - 40, 960, 1.0)
    # legend
    lx = 60
    for col, lab in ((GOLD, "CROWN LINE"), (MAGENTA, "NOVA LINE"), (GREY, "UNDERCITY LINK")):
        d.line([(lx, 1048), (lx + 50, 1048)], fill=col, width=10)
        d.text((lx + 62, 1030), lab, font=RS(28), fill=WHITE)
        lx += 300
    # departures table
    ty = 1110
    d.rectangle([0, ty - 10, W, ty + 46], fill=(14, 22, 32))
    for x, lab in ((40, "TIME"), (180, "DESTINATION"), (650, "PLAT"), (760, "STATUS")):
        d.text((x, ty), lab, font=ORB(26), fill=CYAN)
    rows = [
        ("23:52", "GLASS CROWN", "1", "DELAYED", ORANGE),
        ("", "  track inspection", "", "", (200, 150, 110)),
        ("00:04", "ETHERION PLAZA", "2", "CLOSED", RED),
        ("00:11", "GLASS CROWN", "1", "CHARTER", GOLD),
        ("", "  Directorate service", "", "", (200, 170, 120)),
        ("00:26", "AION SPIRE", "2", "CLOSED", RED),
        ("00:40", "MERIDIAN EXCH.", "2", "CLOSED", RED),
    ]
    y = ty + 70
    for t, dest, p, stat, col in rows:
        small = not t and not p
        f = RM(28) if small else MONO(38)
        d.text((40, y), t, font=MONO(38), fill=(255, 210, 120))
        d.text((180, y + (4 if small else 0)), dest, font=f if small else RB(42), fill=(170, 180, 190) if small else WHITE)
        d.text((665, y), p, font=MONO(38), fill=WHITE)
        d.text((760, y), stat, font=RB(40), fill=col)
        y += 40 if small else 64
    # advisory ticker
    d.rectangle([0, H - 110, W, H], fill=(30, 14, 8))
    d.text((40, H - 92), "PLATFORM 1 CLOSED FOR TRACK INSPECTION", font=RB(34), fill=ORANGE)
    d.text((40, H - 52), "Crown Sector access requires Directorate clearance.  AION thanks you.", font=RM(28), fill=(220, 190, 160))
    frame(d, W, H, (40, 120, 150), 8, 40)
    im = scanlines(im, 26, 4)
    im.save(os.path.join(OUT, "T_NV_CrownLineBoard.png"))

def line_map_poster():
    W, H = 1024, 1280
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 130], fill=(255, 92, 40))
    d.text((40, 22), "CROWN LINE", font=RB(86), fill=(20, 10, 6))
    d.text((580, 52), "VEYRA TRANSIT", font=ORB(34), fill=(20, 10, 6))
    line_map(d, 40, 250, W - 40, 1000, 1.0)
    d.text((40, H - 110), "Lift to the Crown Line concourse is straight ahead.", font=RS(34), fill=WHITE)
    d.text((40, H - 66), "Platform access: cleared personnel only.", font=RM(30), fill=(150, 205, 225))
    frame(d, W, H, (255, 120, 60), 8, 40)
    scanlines(im, 18, 4).save(os.path.join(OUT, "T_NV_CrownLineMap.png"))

def info_panel():
    W, H = 640, 896
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 120], fill=(14, 40, 52))
    text_c(d, (W / 2, 18), "VEYRA CENTRAL", RB(64), CYAN)
    text_c(d, (W / 2, 82), "CROWN LINE  ·  TRANSIT HUB", RS(26), (180, 230, 245))
    y = 160
    for head, body, col in (("SERVICE", "Crown Line to the Glass Crown", GOLD),
                            ("", "Platform 1  ·  delayed", ORANGE),
                            ("HOURS", "05:00 - 02:00 daily", WHITE),
                            ("ACCESS", "Lift to concourse  ·  level -1", WHITE),
                            ("", "Security screening in effect", WHITE),
                            ("NOTICE", "Directorate clearance required", RED),
                            ("", "beyond the concourse", RED)):
        if head:
            y += 14
            d.text((44, y), head, font=ORB(24), fill=CYAN)
            y += 34
        d.text((44, y), body, font=RS(34), fill=col)
        y += 44
    # pictograms: lift, tram
    py = H - 170
    d.rounded_rectangle([44, py, 164, py + 120], 14, outline=CYAN, width=5)
    d.polygon([(104, py + 22), (84, py + 52), (124, py + 52)], fill=CYAN)
    d.polygon([(104, py + 98), (84, py + 68), (124, py + 68)], fill=CYAN)
    d.rounded_rectangle([196, py, 316, py + 120], 14, outline=GOLD, width=5)
    d.rounded_rectangle([214, py + 22, 298, py + 84], 12, outline=GOLD, width=5)
    d.line([(222, py + 104), (290, py + 104)], fill=GOLD, width=5)
    d.ellipse([224, py + 60, 238, py + 74], fill=GOLD); d.ellipse([274, py + 60, 288, py + 74], fill=GOLD)
    d.text((350, py + 20), "ENTRANCE", font=RB(44), fill=WHITE)
    d.text((350, py + 70), "lift  ·  trams", font=RM(30), fill=(150, 205, 225))
    frame(d, W, H, (40, 150, 190), 8, 30)
    scanlines(im, 22, 4).save(os.path.join(OUT, "T_NV_HubInfo.png"))

def aion_notice():
    W, H = 640, 896
    im = Image.new("RGB", (W, H), (8, 6, 14))
    d = ImageDraw.Draw(im)
    # eye mark
    cx, cy = W / 2, 200
    d.ellipse([cx - 130, cy - 70, cx + 130, cy + 70], outline=(230, 230, 255), width=8)
    d.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], fill=(120, 200, 255))
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(8, 6, 14))
    text_c(d, (W / 2, 300), "AION", ORB(76), (230, 230, 255))
    text_c(d, (W / 2, 392), "CIVIC NOTICE", RS(34), (170, 190, 255))
    y = 450
    for s, col in (("This area is monitored", WHITE), ("for your safety.", WHITE), ("", WHITE),
                   ("Curfew  02:00 - 05:00", GOLD), ("Crown Sector: clearance only", GOLD), ("", WHITE),
                   ("Report irregularities to", (170, 190, 255)), ("any Directorate officer.", (170, 190, 255))):
        if s:
            text_c(d, (W / 2, y), s, RS(38), col)
        y += 42
    text_c(d, (W / 2, H - 60), "A SAFER VEYRA. TOGETHER.", RB(30), (120, 200, 255))
    frame(d, W, H, (120, 120, 220), 8, 30)
    scanlines(im, 22, 4).save(os.path.join(OUT, "T_NV_AIONNotice.png"))

def logo_screen(logo_path):
    """Lift-cab monitor: the 'system offline' screen, hijacked by the Monkey Business logo."""
    W, H = 1024, 576
    im = Image.new("RGB", (W, H), (4, 2, 2))
    logo = Image.open(logo_path).convert("RGB")
    lw = int(W * 0.66)
    logo = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
    im.paste(logo, ((W - lw) // 2, 10))
    d = ImageDraw.Draw(im)
    # a few horizontal glitch slices
    rnd = random.Random(7)
    for _ in range(7):
        y = rnd.randint(40, H - 120); h = rnd.randint(3, 14); dx = rnd.randint(-38, 38)
        band = im.crop((0, y, W, y + h))
        im.paste(band, (dx, y))
    text_c(d, (W / 2, H - 70), "SYSTEM OFFLINE  ·  CONTACT SYS ADMIN", MONO(30), (200, 60, 50))
    scanlines(im, 40, 3).save(os.path.join(OUT, "T_NV_MonkeyBiz_Screen.png"))

def logo_ad(logo_path):
    logo = Image.open(logo_path).convert("RGB")
    W, H = 1536, 1024
    im = logo.resize((W, H), Image.LANCZOS)
    im.save(os.path.join(OUT, "T_NV_MonkeyBiz_Ad.png"))

if __name__ == "__main__":
    departures_board()
    line_map_poster()
    info_panel()
    aion_notice()
    if len(sys.argv) > 1:
        logo_screen(sys.argv[1])
        logo_ad(sys.argv[1])
    print("written:", sorted(os.listdir(OUT)))
