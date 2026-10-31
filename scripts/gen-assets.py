"""Genera los SVG estilo cartel risográfico del README.

Uso: python3 riso.py <carpeta_salida> <node_modules/@fontsource>

Todo el texto se convierte a trazados (paths): GitHub sirve los SVG del repo
con una CSP que puede bloquear fuentes incrustadas, así que no dependemos de
ninguna fuente en el navegador de quien visita.
"""
import io, math, pathlib, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
FS = pathlib.Path(sys.argv[2])

# Tintas risográficas
PAPER, INK = "#F3EEE3", "#1C1A22"
PINK, BLUE, YELLOW, ORANGE = "#FF48B0", "#0078BF", "#FFE800", "#FF6C2F"

FONTS = {
    "Anton": "anton/files/anton-latin-400-normal.woff2",
    "Grotesk": "space-grotesk/files/space-grotesk-latin-500-normal.woff2",
    "Plex": "ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2",
    "Serif": "instrument-serif/files/instrument-serif-latin-400-italic.woff2",
}


class Font:
    def __init__(self, path):
        self.tt = TTFont(str(path))
        buf = io.BytesIO(); self.tt.flavor = None; self.tt.save(buf)
        self.hbfont = hb.Font(hb.Face(buf.getvalue()))
        self.upm = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()

    def shape(self, text):
        b = hb.Buffer(); b.add_str(text); b.guess_segment_properties()
        hb.shape(self.hbfont, b, {"kern": True, "liga": True})
        return [(self.order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(b.glyph_infos, b.glyph_positions)]


F = {k: Font(FS / v) for k, v in FONTS.items()}


def width(text, fam, size, tracking=0):
    f = F[fam]
    return sum(a for _, a, _, _ in f.shape(text)) / f.upm * size + tracking * len(text)


def d_of(text, fam, size, x, y, tracking=0, anchor="start"):
    f = F[fam]; s = size / f.upm
    w = width(text, fam, size, tracking)
    x0 = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
    pen = SVGPathPen(f.gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    cx = x0
    for g, adv, xo, yo in f.shape(text):
        f.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx + xo * s, y - yo * s)))
        cx += adv * s + tracking
    return pen.getCommands()


def txt(text, x, y, fam, size, fill=INK, tracking=0, anchor="start", extra=""):
    return f'<path d="{d_of(text, fam, size, x, y, tracking, anchor)}" fill="{fill}" {extra}/>'


def wrap(text, fam, size, maxw):
    lines, cur = [], ""
    for wd in text.split():
        t = (cur + " " + wd).strip()
        if width(t, fam, size) > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = t
    return lines + [cur]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


STYLE = "<style>.mul{mix-blend-mode:multiply}</style>"


def common_defs(uid):
    return f"""
<filter id="grain{uid}" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="2" seed="7" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.6 1.05"/>
</filter>
<filter id="rough{uid}"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="5"/></filter>
<pattern id="dotsP{uid}" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(18)"><circle cx="6" cy="6" r="3.6" fill="{PINK}"/></pattern>
<pattern id="dotsB{uid}" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(-15)"><circle cx="5" cy="5" r="2.6" fill="{BLUE}"/></pattern>
<pattern id="dotsY{uid}" width="11" height="11" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><circle cx="5.5" cy="5.5" r="3.4" fill="{YELLOW}"/></pattern>"""


def svg(w, h, uid, body, title, bg=PAPER):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
{STYLE}
<defs>{common_defs(uid)}</defs>
<rect width="{w}" height="{h}" fill="{bg}"/>
<g style="isolation:isolate">{body}</g>
<rect width="{w}" height="{h}" filter="url(#grain{uid})" opacity=".3" class="mul"/>
</svg>"""


def asterisk(cx, cy, r, color, arms=8, spin=0):
    t = r * .26
    rects = "".join(
        f'<rect x="{-t/2:.1f}" y="{-r}" width="{t:.1f}" height="{2*r}" rx="{t/2:.1f}" transform="rotate({180/arms*i:.1f})"/>'
        for i in range(arms))
    anim = (f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{spin}s" repeatCount="indefinite"/>'
            if spin else "")
    return f'<g transform="translate({cx} {cy})"><g fill="{color}">{rects}{anim}</g></g>'


def misreg(text, x, y, size, a=INK, b=PINK, dx=7, dy=5, fam="Anton"):
    d = d_of(text, fam, size, 0, 0)
    return (f'<path d="{d}" fill="{a}" class="mul" transform="translate({x} {y})"/>'
            f'<g class="mul" transform="translate({x+dx} {y+dy})"><path d="{d}" fill="{b}">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;-2 1;1 -1;0 0" dur="5s" repeatCount="indefinite"/>'
            f'</path></g>')


# ---------------------------------------------------------------- cabecera
def header():
    w, h = 1200, 600
    mono = lambda s, x, y, fill=INK, anchor="start": txt(s, x, y, "Plex", 15, fill, 2.5, anchor)
    body = f"""
<circle cx="965" cy="345" r="215" fill="{YELLOW}" class="mul"/>
<circle cx="1075" cy="170" r="135" fill="url(#dotsPh)" class="mul"/>
<g transform="rotate(-4 430 395)">
  <rect x="34" y="300" width="752" height="196" fill="{BLUE}" class="mul" filter="url(#roughh)"/>
</g>
{misreg("MATIAS", 52, 288, 232, a=INK, b=PINK, dx=8, dy=6)}
<g transform="rotate(-4 430 395)">{txt("FERRARO", 70, 474, "Anton", 196, PAPER, 2)}</g>
{asterisk(1095, 470, 62, ORANGE, 8, spin=26)}
<path d="M790 118 q22 -26 44 0 t44 0 t44 0 t44 0" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
{mono("N°01 — PORTFOLIO / FANZINE", 56, 62)}
{mono("VOL. MMXXVI", 1144, 62, anchor="end")}
{txt("I build things for the web", 812, 318, "Serif", 34)}
{txt("and write things for the soul.", 812, 358, "Serif", 34)}
{mono("WRITER", 56, 560)}{mono("×", 148, 560, PINK)}
{mono("DEVELOPER", 172, 560)}{mono("×", 306, 560, BLUE)}
{mono("BLOGGER", 330, 560)}
{mono("ELDIARIODEMATI.COM", 1110, 560, anchor="end")}
<path d="M1122 555 h20 m-7 -7 l7 7 l-7 7" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>{""}
<line x1="56" y1="530" x2="1144" y2="530" stroke="{INK}" stroke-width="2"/>
"""
    (OUT / "header.svg").write_text(svg(w, h, "h", body, "Matias Ferraro — writer, developer, blogger"))


# ---------------------------------------------------------------- tarjetas
def stamp(x, y, text, color, u, rot=-9):
    tw = width(text, "Plex", 15, 3) + 28
    return f"""<g transform="rotate({rot} {x} {y})">
  <rect x="{x - tw/2:.0f}" y="{y-20}" width="{tw:.0f}" height="40" fill="none" stroke="{color}" stroke-width="3" filter="url(#rough{u})"/>
  {txt(text, x, y + 5.5, "Plex", 15, color, 3, "middle")}
</g>"""


def tags(x, y, items):
    out, px = [], x
    for t in items:
        tw = width(t, "Plex", 13, .5) + 22
        out.append(
            f'<rect x="{px+3}" y="{y+3}" width="{tw:.0f}" height="28" fill="{INK}"/>'
            f'<rect x="{px}" y="{y}" width="{tw:.0f}" height="28" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
            + txt(t, px + tw / 2, y + 18.5, "Plex", 13, INK, .5, "middle"))
        px += tw + 10
    return "".join(out)


ART = {
    # comillas gigantes: la escritura
    "prosalimpia": lambda u: f"""
<circle cx="478" cy="128" r="104" fill="url(#dotsB{u})" class="mul"/>
{txt("“", 368, 300, "Serif", 380, PINK, extra='class="mul"')}
""",
    # sol y olas: el viaje
    "diario": lambda u: f"""
<circle cx="470" cy="135" r="98" fill="{YELLOW}" class="mul">
  <animate attributeName="cy" values="135;125;135" dur="6s" repeatCount="indefinite"/></circle>
<g fill="none" stroke="{BLUE}" stroke-width="10" stroke-linecap="round" class="mul">
  <path d="M440 192 q22 -20 44 0 t44 0 t44 0"/>
  <path d="M462 220 q22 -20 44 0 t44 0 t44 0"/>
</g>
<circle cx="510" cy="160" r="70" fill="url(#dotsP{u})" class="mul"/>
""",
    # sobre tachado: mails desechables
    "disposable": lambda u: f"""
<g transform="rotate(8 470 150) translate(10 -20) scale(.9)">
  <rect x="370" y="80" width="200" height="140" fill="{BLUE}" class="mul"/>
  <path d="M370 80 L470 160 L570 80" fill="none" stroke="{PAPER}" stroke-width="8" stroke-linejoin="round"/>
</g>
<g stroke="{ORANGE}" stroke-width="22" stroke-linecap="round" class="mul">
  <line x1="410" y1="56" x2="555" y2="200"/><line x1="555" y1="56" x2="410" y2="200"/>
</g>
""",
    # constelación: mapa de influencias
    "lineas": lambda u: f"""
<circle cx="470" cy="160" r="112" fill="url(#dotsY{u})" class="mul"/>
<g stroke="{BLUE}" stroke-width="3" class="mul">
  <line x1="390" y1="100" x2="480" y2="70"/><line x1="480" y1="70" x2="560" y2="140"/>
  <line x1="390" y1="100" x2="440" y2="190"/><line x1="440" y1="190" x2="560" y2="140"/>
  <line x1="440" y1="190" x2="520" y2="245"/><line x1="480" y1="70" x2="440" y2="190"/>
</g>
<g class="mul">
  <circle cx="390" cy="100" r="14" fill="{PINK}"/><circle cx="480" cy="70" r="10" fill="{BLUE}"/>
  <circle cx="560" cy="140" r="18" fill="{PINK}"/><circle cx="440" cy="190" r="22" fill="{ORANGE}">
    <animate attributeName="r" values="22;26;22" dur="3s" repeatCount="indefinite"/></circle>
  <circle cx="520" cy="245" r="9" fill="{BLUE}"/>
</g>
""",
}


def card(n, slug, title, kicker, desc, tg, status, scolor):
    w, h = 600, 400
    u = slug[:3]
    tsize = min(68, 420 / width(title.upper(), "Anton", 1))
    lines = wrap(desc, "Grotesk", 18, 520)
    dsvg = "".join(txt(l, 40, 290 + i * 25, "Grotesk", 18, INK, extra='fill-opacity=".85"')
                   for i, l in enumerate(lines[:2]))
    body = f"""
{ART[slug](u)}
<path d="{d_of(n, "Anton", 118, 34, 178)}" fill="none" stroke="{INK}" stroke-width="2.5"/>
{txt(kicker.upper(), 40, 46, "Plex", 13, INK, 3)}
{misreg(title.upper(), 38, 252, tsize, a=INK, b=scolor, dx=4, dy=3)}
{dsvg}
{tags(40, 344, tg)}
{stamp(520, 352, status.upper(), scolor, u)}
<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" fill="none" stroke="{INK}" stroke-width="3"/>
"""
    (OUT / f"card-{slug}.svg").write_text(svg(w, h, u, body, f"{title} — {desc}"))


# ---------------------------------------------------------------- cinta
def ticker(name, words, bg, fg, sep_colors, title, speed=60):
    w, size = 1200, 46
    parts, x = [], 0
    for i, wd in enumerate(words):
        parts.append(txt(wd, x, 62, "Anton", size, fg, 1))
        x += width(wd, "Anton", size, 1) + 34
        parts.append(asterisk(x, 41, 17, sep_colors[i % len(sep_colors)], 6))
        x += 51
    period = x
    reps = math.ceil(w / period) + 1
    unit = "".join(parts)
    row = f'<g id="u{name}">{unit}</g>' + "".join(
        f'<use href="#u{name}" x="{period*r:.0f}"/>' for r in range(1, reps))
    body = f"""<g>{row}
  <animateTransform attributeName="transform" type="translate" from="0 0" to="{-period:.0f} 0" dur="{period/speed:.1f}s" repeatCount="indefinite"/>
</g>"""
    (OUT / f"{name}.svg").write_text(svg(w, 84, name[:2], body, title, bg=bg))


# ---------------------------------------------------------------- colofón
def colophon():
    w, h = 1200, 340
    text = ("Set in TypeScript. Composed with Next.js, React, Astro & Svelte. "
            "Styled with Tailwind. Bound with Supabase, PostgreSQL & Prisma. "
            "Printed on Node & Vercel — with a little Ruby on Rails in the margins.")
    lines = wrap(text, "Serif", 40, 800)
    tsp = "".join(txt(l, 330, 108 + i * 48, "Serif", 40) for i, l in enumerate(lines))
    ly = 108 + len(lines) * 48 - 14
    body = f"""
<circle cx="150" cy="170" r="118" fill="{PINK}" class="mul"/>
<circle cx="215" cy="215" r="88" fill="url(#dotsBc)" class="mul"/>
{txt("TOOLS", 150, 196, "Anton", 64, INK, 1, "middle")}
{txt("COLOPHON", 56, 44, "Plex", 13, INK, 3)}
{tsp}
<line x1="330" y1="{ly}" x2="420" y2="{ly}" stroke="{ORANGE}" stroke-width="6" stroke-linecap="round"/>
<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" fill="none" stroke="{INK}" stroke-width="3"/>
"""
    (OUT / "colophon.svg").write_text(svg(w, h, "c", body, "Colophon — " + text))


header()
card("01", "prosalimpia", "Prosa Limpia", "AI · Writing tool",
     "Literary proofreading with AI — streaming suggestions and a full revision history.",
     ["Next.js", "Supabase", "DeepSeek"], "Live", PINK)
card("02", "diario", "El Diario de Mati", "Blog · Travel writing",
     "Stories, travel and culture. My blog, with a hand-built editorial design system.",
     ["Astro", "Svelte 5", "Tailwind"], "Live", BLUE)
card("03", "disposable", "disposable-check", "Library · TypeScript",
     "Spots throwaway email addresses before they reach your sign-up form.",
     ["TypeScript", "Node.js", "npm"], "WIP", ORANGE)
card("04", "lineas", "Líneas", "Concept · Books × AI",
     "Book recommendations drawn as a map of literary influences, from the clues you leave.",
     ["AI", "Graphs", "Literature"], "Sketch", BLUE)
ticker("ticker", ["WRITE", "CODE", "TRAVEL", "READ", "REPEAT"], INK, PAPER,
       [PINK, YELLOW, BLUE, ORANGE], "Write, code, travel, read, repeat")
ticker("ticker-footer", ["THANKS FOR READING", "NOS LEEMOS EN EL BLOG"], PINK, INK,
       [YELLOW, BLUE], "Thanks for reading — nos leemos en el blog", speed=45)
colophon()
for p in sorted(OUT.glob("*.svg")):
    print(f"{p.name:24} {p.stat().st_size/1024:6.1f} KB")
