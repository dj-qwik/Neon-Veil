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

def schedule_screen():
    """Landscape 'Terminal B' style schedule for the SM_Holoscreen_C wall screens, in English with Veyra stops."""
    W, H = 1024, 552
    im = Image.new("RGB", (W, H), (22, 26, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([24, 22, W - 24, 112], fill=(196, 52, 46))
    d.text((48, 26), "CROWN LINE", font=RB(80), fill=(236, 236, 236))
    for i in range(4):
        x = W - 230 + i * 48
        d.polygon([(x, 30), (x + 26, 30), (x + 56, 67), (x + 26, 104), (x, 104), (x + 30, 67)], fill=(70, 30, 30) if i < 2 else (240, 120, 110))
    d.text((56, 128), "Veyra Central  ·  Schedule  >>>", font=RS(34), fill=(200, 205, 210))
    d.line([(56, 172), (W - 56, 172)], fill=(70, 78, 86), width=2)
    def block(y, title, rows):
        d.rounded_rectangle([56, y + 6, 104, y + 150], 22, fill=(236, 150, 40))
        d.text((122, y), title, font=RB(40), fill=(230, 232, 235))
        for k, (a, b, c, t, st, col) in enumerate(rows):
            yy = y + 6 + k * 34
            d.text((330, yy), a, font=RS(27), fill=(205, 210, 215))
            d.text((560, yy), b, font=RS(27), fill=(205, 210, 215))
            d.text((660, yy), c, font=RS(27), fill=(205, 210, 215))
            d.text((790, yy), t, font=RS(27), fill=(205, 210, 215))
            d.text((880, yy), st, font=RB(27), fill=col)
    G, R, O = (80, 200, 110), (240, 80, 70), (250, 170, 60)
    block(186, "Arrivals", [("Glass Crown", "CL 04", "Plat 1", "23:40", "Held", O),
                            ("Meridian Exch.", "NL 12", "Plat 2", "23:47", "On time", G),
                            ("Kestrel Arcade", "CL 07", "Plat 2", "23:58", "On time", G),
                            ("The Gutter", "UL 01", "--", "--:--", "Suspended", R)])
    block(370, "Departures", [("Glass Crown", "CL 04", "Plat 1", "23:52", "Delayed", R),
                              ("Etherion Plaza", "CL 05", "Plat 2", "00:04", "Closed", R),
                              ("AION Spire", "CL 06", "Plat 2", "00:26", "Closed", R),
                              ("Glass Crown", "DIR 1", "Plat 1", "00:11", "Charter", O)])
    d.rounded_rectangle([12, 10, W - 12, H - 10], 26, outline=(205, 210, 215), width=6)
    scanlines(im, 14, 4).save(os.path.join(OUT, "T_NV_ScheduleScreen.png"))

def breaker_face():
    """Face of the Platform One traction-power breaker (TPS-04): base colour + emissive mask.
    Layout matches ANVBreakerPanel: plate 64 x 88 cm; viewer's right is the actor's -Y. Fuse windows at y -25..25
    (z 166), lamps at y -22 / -10 (z 128), lever pivot y 16 (z 130), hazard strip z 103."""
    W, H = 1024, 1408
    rnd = random.Random(4)
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        for x in range(W):
            n = rnd.randint(-6, 6)
            v = 58 + int(10 * math.sin(y * 0.9)) // 5 + n
            px[x, y] = (v, v + 3, v + 7)
    em = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    U = lambda yy: int((32 - yy) / 64 * W)              # actor y (cm) -> pixel x
    Vv = lambda zz: int((184 - zz) / 88 * H)            # actor z (cm) -> pixel y
    def bevel(box, r=10, dark=(22, 24, 28), lite=(110, 116, 124), fill=None):
        x0, y0, x1, y1 = box
        if fill:
            d.rounded_rectangle(box, r, fill=fill)
        d.rounded_rectangle([x0, y0, x1, y1], r, outline=dark, width=6)
        d.line([(x0 + r, y0 + 3), (x1 - r, y0 + 3)], fill=lite, width=3)
        d.line([(x0 + 3, y0 + r), (x0 + 3, y1 - r)], fill=lite, width=3)
    # panel border and seams
    bevel([10, 10, W - 10, H - 10], 26)
    for yy in (Vv(150),):
        d.line([(24, yy), (W - 24, yy)], fill=(28, 30, 34), width=5)
        d.line([(24, yy + 5), (W - 24, yy + 5)], fill=(96, 100, 108), width=2)
    for (bx, by) in ((44, 44), (W - 44, 44), (44, H - 44), (W - 44, H - 44), (W // 2, 44), (W // 2, H - 44)):
        d.ellipse([bx - 15, by - 15, bx + 15, by + 15], fill=(40, 42, 46), outline=(130, 136, 144), width=3)
        d.line([(bx - 8, by), (bx + 8, by)], fill=(20, 20, 22), width=4)
    # title plate
    bevel([70, 40, W - 70, 150], 12, fill=(24, 26, 30))
    d.text((96, 44), "TPS-04  TRACTION POWER", font=RB(52), fill=(232, 220, 190))
    d.text((96, 104), "PLATFORM 1  ·  1500 V DC  ·  CROWN LINE", font=RS(30), fill=(160, 170, 180))
    # fuse windows (the glowing fuse blocks sit in these)
    for i, yy in enumerate((-25, -15, -5, 5, 15, 25)):
        cx, cy = U(yy), Vv(166)
        bevel([cx - 60, cy - 122, cx + 60, cy + 122], 12, fill=(14, 16, 18))
        d.text((cx - 22, cy + 128), "F%d" % (i + 1), font=MONO(32), fill=(200, 205, 210))
    # lever slot (left of centre)
    lx, lz = U(16), Vv(130)
    bevel([lx - 70, lz - 230, lx + 70, lz + 150], 18, fill=(18, 19, 22))
    d.text((lx - 34, lz - 300), "ON", font=RB(44), fill=(90, 230, 120))
    d.text((lx - 46, lz + 166), "OFF", font=RB(44), fill=(240, 90, 70))
    d.text((lx - 110, lz + 226), "MAIN ISOLATOR", font=RS(28), fill=(170, 175, 182))
    # lamp bezels
    for yy, lab, col in ((-22, "FAULT", (240, 80, 60)), (-10, "LIVE", (90, 230, 120))):
        cx, cy = U(yy), Vv(128)
        d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(20, 21, 24), outline=(140, 146, 154), width=6)
        text_c(d, (cx, cy + 82), lab, RB(30), col)
    # digital readout + gauge strip
    rx0, ry0 = U(-4) - 40, Vv(150) + 30
    bevel([rx0, ry0, rx0 + 420, ry0 + 110], 10, fill=(6, 12, 10))
    for k in range(5):
        x = rx0 + 26 + k * 52
        de.rectangle([x, ry0 + 22, x + 36, ry0 + 88], fill=(30, 120, 60))
        d.rectangle([x, ry0 + 22, x + 36, ry0 + 88], outline=(30, 60, 40), width=2)
    d.text((rx0 + 290, ry0 + 34), "V DC", font=MONO(30), fill=(120, 200, 140))
    de.text((rx0 + 290, ry0 + 34), "V DC", font=MONO(30), fill=(60, 140, 80))
    # danger strip above the hazard band
    tx, ty = 110, 1182
    d.polygon([(tx, ty - 44), (tx + 50, ty + 40), (tx - 50, ty + 40)], fill=(240, 190, 30), outline=(20, 20, 20))
    d.polygon([(tx + 5, ty - 22), (tx - 13, ty + 8), (tx + 1, ty + 8), (tx - 7, ty + 32), (tx + 14, ty - 2), (tx + 1, ty - 2)], fill=(20, 20, 20))
    d.text((tx + 72, ty - 46), "DANGER  ·  HIGH VOLTAGE", font=RB(44), fill=(240, 190, 30))
    d.text((tx + 72, ty + 4), "Isolate before opening. Authorised crew only.", font=RS(28), fill=(210, 212, 215))
    # hazard band (bottom)
    hy0, hy1 = Vv(107), Vv(99)
    for k in range(-10, 40):
        x = k * 70
        d.polygon([(x, hy1), (x + 35, hy1), (x + 35 + (hy1 - hy0), hy0), (x + (hy1 - hy0), hy0)], fill=(230, 180, 20))
    d.rectangle([0, hy0, W, hy0 + 4], fill=(20, 20, 20)); d.rectangle([0, hy1 - 4, W, hy1], fill=(20, 20, 20))
    d.text((70, H - 42), "SAITKO CORP  ·  VEYRA TRANSIT AUTHORITY  ·  S/N 0447-TPS", font=MONO(26), fill=(150, 155, 160))
    # small status LEDs along the top right
    for k in range(4):
        x = W - 120 - k * 46
        col = (40, 200, 255) if k % 2 == 0 else (255, 150, 30)
        de.ellipse([x - 9, 86, x + 9, 104], fill=col)
        d.ellipse([x - 9, 86, x + 9, 104], fill=tuple(c // 2 for c in col))
    im.save(os.path.join(OUT, "T_NV_BreakerFace.png"))
    em.save(os.path.join(OUT, "T_NV_BreakerFace_E.png"))

def hazard_floor():
    W, H = 1024, 256
    im = Image.new("RGB", (W, H), (20, 20, 20))
    d = ImageDraw.Draw(im)
    for k in range(-4, 20):
        x = k * 96
        d.polygon([(x, H), (x + 48, H), (x + 48 + H, 0), (x + H, 0)], fill=(220, 170, 20))
    rnd = random.Random(9)
    px = im.load()
    for _ in range(26000):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r, g, b = px[x, y]
        k = rnd.uniform(0.55, 0.9)
        px[x, y] = (int(r * k), int(g * k), int(b * k))
    im.save(os.path.join(OUT, "T_NV_HazardFloor.png"))

if __name__ == "__main__":
    departures_board()
    line_map_poster()
    info_panel()
    aion_notice()
    schedule_screen()
    breaker_face()
    hazard_floor()
    if len(sys.argv) > 1:
        logo_screen(sys.argv[1])
        logo_ad(sys.argv[1])
    print("written:", sorted(os.listdir(OUT)))
