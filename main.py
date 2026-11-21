# news-image-20261121, variant 4: a Saturday-edition front page for
# Saturday 21 November 2026, built as a broadcast-style bulletin.
#
# Layout (1024 x 1024, warm paper, red masthead) is deliberately unlike
# variants 1-3 (broadsheet grid / single-lead poster / dark world map):
# a full-width cinematic lead panel whose dominant graphic is a
# seismograph trace for the Peru earthquake, then four stories in one
# horizontal row, then a red ticker strip of briefs. The six stories
# are all different from v1-v3: Peru quake, Rikers Island closure plan,
# record foreign investment into India, Anthropic's post-IPO slide,
# the Palisades Fire verdict, plus briefs (Nepal PM, Austria hack,
# Kuno cheetah cubs, India women's hockey). Every story was verified
# against live news roundups for 21 November 2026 before drawing.
#
# Pure Python 3.13 standard library, no network, fully deterministic:
# the same run always writes the same bytes. Text is rendered with a
# small embedded 5x7 bitmap font; the PNG is encoded by hand with zlib.

import os
import struct
import zlib

W, H = 1024, 1024

# --- palette: warm paper, signal red, ink ----------------------------------
PAPER = (247, 242, 232)
PAPER2 = (255, 252, 244)
INK = (24, 24, 30)
INK2 = (38, 38, 48)
RED = (178, 34, 34)
RED_DK = (140, 24, 24)
AMBER = (232, 163, 61)
WHITE = (250, 248, 242)
MUTED = (96, 92, 84)
RULE = (200, 192, 176)
TEAL = (36, 110, 102)

# --- 5x7 bitmap font: A-Z, 0-9 and a small punctuation set ------------------
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is empty.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}


def chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb, w, h):
    """Encode an RGB byte string as a deterministic PNG (filter 0 rows)."""
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    return png


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, color)

    def hline(self, x0, x1, y, color, t=1):
        for yy in range(y, y + t):
            for x in range(x0, x1):
                self.set(x, yy, color)

    def vline(self, x, y0, y1, color, t=1):
        for xx in range(x, x + t):
            for y in range(y0, y1):
                self.set(xx, y, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x + a, y + b, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def polyline(self, pts, color, t=1):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], color, t)

    def disc(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def ring(self, cx, cy, r, color, t=2):
        for k in range(t):
            rr = r - k
            for a in range(360):
                import math
                x = cx + int(rr * math.cos(math.radians(a)))
                y = cy + int(rr * math.sin(math.radians(a)))
                self.set(x, y, color)

    def text(self, x, y, s, color, string):
        """Draw uppercase text at scale s (glyph 5x7, 1px gap). Returns width."""
        cx = x
        for ch in string:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                for c in range(5):
                    if row[c] == "#":
                        self.rect(cx + c * s, y + r * s, cx + (c + 1) * s,
                                  y + (r + 1) * s, color)
            cx += 6 * s
        return cx - x

    def text_w(self, s, string):
        return 6 * s * len(string) - s

    def center(self, y, s, color, string, x0=0, x1=W):
        w = self.text_w(s, string)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, color, string)

    def wrap(self, s, string, max_w):
        """Greedy word wrap; returns a list of lines fitting max_w pixels."""
        lines, cur = [], ""
        for word in string.split(" "):
            trial = (cur + " " + word).strip()
            if self.text_w(s, trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# --- small pictograms for the four middle stories ---------------------------
def icon_jail(cv, x, y, s, color):
    # prison bars: a frame with vertical bars (Rikers Island)
    cv.rect(x, y, x + 3 * s, y + 26 * s, color)
    cv.rect(x + 21 * s, y, x + 24 * s, y + 26 * s, color)
    cv.rect(x, y, x + 24 * s, y + 3 * s, color)
    cv.rect(x, y + 23 * s, x + 24 * s, y + 26 * s, color)
    for bx in (7, 12, 17):
        cv.rect(x + bx * s, y + 3 * s, x + (bx + 2) * s, y + 23 * s, color)


def icon_chart(cv, x, y, s, color):
    # rising bars with an arrow (record investment into India)
    bars = [(0, 12), (6, 8), (12, 10), (18, 4)]
    for bx, bh in bars:
        cv.rect(x + bx * s, y + (16 - bh) * s, x + (bx + 4) * s, y + 16 * s,
                color)
    cv.polyline([(x, y + 12 * s), (x + 8 * s, y + 6 * s),
                 (x + 14 * s, y + 8 * s), (x + 24 * s, y - 2 * s)], color, 2)


def icon_chip(cv, x, y, s, color):
    # a microchip (Anthropic / AI shares)
    cv.rect(x + 4 * s, y + 4 * s, x + 20 * s, y + 20 * s, color)
    cv.rect(x + 9 * s, y + 9 * s, x + 15 * s, y + 15 * s, PAPER)
    for px in (7, 12, 17):
        cv.rect(x + px * s, y, x + (px + 2) * s, y + 4 * s, color)
        cv.rect(x + px * s, y + 20 * s, x + (px + 2) * s, y + 24 * s, color)
    for py in (7, 12, 17):
        cv.rect(x, y + py * s, x + 4 * s, y + (py + 2) * s, color)
        cv.rect(x + 20 * s, y + py * s, x + 24 * s, y + (py + 2) * s, color)


def icon_flame(cv, x, y, s, color):
    # a flame (Palisades Fire verdict)
    cv.disc(x + 12 * s, y + 15 * s, 9 * s, color)
    pts = [(x + 12 * s, y), (x + 20 * s, y + 12 * s),
           (x + 16 * s, y + 10 * s), (x + 18 * s, y + 16 * s),
           (x + 6 * s, y + 16 * s), (x + 8 * s, y + 10 * s),
           (x + 4 * s, y + 12 * s)]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        cv.line(a[0], a[1], b[0], b[1], color, 2)
    cv.disc(x + 12 * s, y + 16 * s, 4 * s, AMBER)


def draw():
    cv = Canvas(W, H, PAPER)
    M = 28                      # margin
    CW = W - 2 * M              # content width

    # --- masthead: red band -------------------------------------------------
    cv.rect(0, 0, W, 118, RED)
    cv.hline(0, W, 118, RED_DK, 4)
    cv.center(16, 2, AMBER, "THE SATURDAY EDITION")
    cv.center(40, 6, WHITE, "THE WORLD IN A DAY")
    cv.center(128, 2, INK, "SATURDAY 21 NOVEMBER 2026  -  SIX STORIES FROM AROUND THE WORLD")
    cv.hline(M, W - M, 158, INK, 3)

    # --- lead panel: the Peru earthquake, drawn as a seismograph ------------
    y0, y1 = 172, 556
    cv.rect(M, y0, W - M, y1, INK)
    cv.rect(M, y0, W - M, y0 + 4, RED)
    # faint mountain silhouettes along the bottom of the panel
    peaks = [(M, y1), (120, 470), (210, 520), (300, 462), (390, 525),
             (480, 478), (560, 530), (660, 468), (760, 522), (860, 472),
             (940, 520), (W - M, 486), (W - M, y1)]
    for i in range(len(peaks) - 1):
        a, b = peaks[i], peaks[i + 1]
        cv.line(a[0], a[1], b[0], b[1], INK2, 2)
    # seismograph trace: a calm line that erupts into a big spike
    import math
    trace = []
    for x in range(M + 16, W - M - 16, 6):
        t = (x - M) / CW
        if 0.52 < t < 0.62:
            amp = 52 * math.sin((t - 0.52) / 0.10 * math.pi)
            yy = 330 - amp
        elif 0.62 <= t < 0.70:
            amp = 26 * math.sin((t - 0.62) / 0.08 * math.pi)
            yy = 330 - amp
        else:
            yy = 330 + 3 * math.sin(t * 40)
        trace.append((x, int(yy)))
    cv.polyline(trace, WHITE, 2)
    cv.disc(trace[len(trace) // 2][0], trace[len(trace) // 2][1], 5, RED)
    cv.text(M + 16, y0 + 126, 2, AMBER, "SEISMOGRAPH - JUNIN, PERU")
    # kicker, headline, big magnitude, dek
    cv.text(M + 16, y0 + 20, 2, AMBER, "EARTHQUAKE  -  PERU")
    cv.text(M + 16, y0 + 48, 5, WHITE, "THE GROUND SHOOK")
    cv.text(M + 16, y0 + 84, 5, WHITE, "IN PERU")
    cv.text(W - M - 250, y0 + 28, 12, RED, "6.8")
    cv.text(W - M - 250, y0 + 118, 2, WHITE, "MAGNITUDE")
    dek = [
        "A MAGNITUDE 6.8 QUAKE STRIKES JUNIN IN THE ANDES,",
        "FELT 320 KM AWAY IN LIMA. RESIDENTS RUSH INTO THE",
        "STREETS AND LAWMAKERS LEAVE CONGRESS. NO",
        "CASUALTIES OR MAJOR DAMAGE REPORTED.",
    ]
    for i, line in enumerate(dek):
        cv.text(M + 16, y0 + 168 + i * 18, 2, WHITE, line)
    cv.text(M + 16, y0 + 168 + 4 * 18 + 10, 2, MUTED,
            "DEPTH 129 KM  -  FIRST QUAKE OF THIS SIZE FELT THERE, OFFICIALS SAY")

    # --- middle row: four stories side by side ------------------------------
    cols = [
        ("NEW YORK", "RIKERS TO CLOSE BY 2032",
         "MAYOR MAMDANI UNVEILS THE FIRST FULL PLAN TO SHUT THE JAIL COMPLEX BY 2032.",
         icon_jail, RED),
        ("INDIA MARKETS", "RECORD CASH FLOODS INTO INDIA",
         "FOREIGN INVESTORS POUR A RECORD RS 1.22 LAKH CRORE INTO INDIAN SHARES IN NOVEMBER.",
         icon_chart, TEAL),
        ("TECH", "ANTHROPIC SLIDES 9%",
         "SHARES FALL A DAY AFTER THE AI FIRM'S RECORD MARKET DEBUT, AS THE TECH SELL-OFF DEEPENS.",
         icon_chip, RED),
        ("JUSTICE - LA", "GUILTY: PALISADES FIRE",
         "JONATHAN RINDERKNECHT, 30, CONVICTED ON TWO ARSON COUNTS OVER THE 2025 BLAZE THAT KILLED 12.",
         icon_flame, RED),
    ]
    cy0, cy1 = 572, 828
    colw = (CW - 3 * 16) // 4
    for i, (kick, head, body, icon, accent) in enumerate(cols):
        x0 = M + i * (colw + 16)
        x1 = x0 + colw
        cv.rect(x0, cy0, x1, cy1, PAPER2)
        cv.rect(x0, cy0, x1, cy0 + 5, accent)
        cv.hline(x0, x1, cy1, RULE, 2)
        icon(cv, x0 + 12, cy0 + 18, 1, accent)
        cv.text(x0 + 48, cy0 + 24, 2, accent, kick)
        hy = cy0 + 62
        for ln in cv.wrap(3, head, colw - 24):
            cv.text(x0 + 12, hy, 3, INK, ln)
            hy += 24
        by = hy + 10
        for ln in cv.wrap(2, body, colw - 24):
            cv.text(x0 + 12, by, 2, INK, ln)
            by += 16

    # --- ticker strip: briefs ----------------------------------------------
    ty0, ty1 = 844, 922
    cv.rect(M, ty0, W - M, ty1, RED)
    cv.text(M + 16, ty0 + 12, 2, AMBER, "ALSO TODAY")
    ticker = [
        "NEPAL PM BALEN HEADS TO DELHI ON HIS FIRST FOREIGN TRIP",
        "AUSTRIA SAYS ITS FOREIGN MINISTRY WEBSITE WAS HACKED",
        "CHEETAH GIVES BIRTH TO FOUR CUBS AT KUNO",
        "INDIA WOMEN BEAT MALAYSIA 4-1 IN HOCKEY OPENER",
    ]
    for i, line in enumerate(ticker):
        yy = ty0 + 12 + i * 17
        cv.disc(M + 148, yy + 7, 3, AMBER)
        cv.text(M + 160, yy, 2, WHITE, line)

    # --- footer --------------------------------------------------------------
    cv.center(942, 2, MUTED,
              "EVERY STORY HERE HAPPENED OR WAS FIRST REPORTED ON SATURDAY 21 NOVEMBER 2026")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw()
    png = encode_png(bytes(cv.buf), W, H)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
