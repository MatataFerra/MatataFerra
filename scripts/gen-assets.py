"""Genera los SVG glass del README (variantes dark/light)."""
import pathlib, sys

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "assets")
OUT.mkdir(parents=True, exist_ok=True)

SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,monospace"

THEMES = {
    "dark": dict(
        bg="#0A0A10", ink="#F4F1FA", muted="#A7A1B8", faint="#6E6880",
        glass="#FFFFFF", glass_a=0.045, stroke_a=0.16, hi_a=0.22,
        blobs=["#7C3AED", "#DB2777", "#4F46E5", "#A855F7"], blob_a=0.38,
        grain_a=0.07, pill="#FFFFFF", pill_a=0.06,
    ),
    "light": dict(
        bg="#F6F4FA", ink="#16131F", muted="#5B5569", faint="#8D8799",
        glass="#FFFFFF", glass_a=0.55, stroke_a=0.9, hi_a=0.7,
        blobs=["#C4B5FD", "#F9A8D4", "#A5B4FC", "#D8B4FE"], blob_a=0.85,
        grain_a=0.05, pill="#16131F", pill_a=0.05,
    ),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def blobs(t, w, h, uid, seed=0):
    """Manchas de color que derivan lentamente (aurora)."""
    c = t["blobs"]
    spots = [
        (0.18, 0.30, 0.34, c[0], "40 18", 19),
        (0.78, 0.25, 0.30, c[1], "-36 24", 23),
        (0.55, 0.85, 0.36, c[2], "28 -22", 27),
        (0.95, 0.90, 0.22, c[3], "-24 -16", 21),
    ]
    out = []
    for i, (x, y, r, col, d, dur) in enumerate(spots[seed:] + spots[:seed]):
        out.append(
            f'<circle cx="{x*w:.0f}" cy="{y*h:.0f}" r="{r*max(w,h):.0f}" fill="{col}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {d}; 0 0" dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>'
        )
    return f'<g id="b{uid}" opacity="{t["blob_a"]}">' + "".join(out) + "</g>"


def defs(t, w, h, uid, card, seed=0):
    x, y, cw, ch, rx = card
    return f"""<defs>
  {blobs(t, w, h, uid, seed)}
  <filter id="soft{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{max(w,h)*0.05:.0f}"/></filter>
  <filter id="frost{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{max(w,h)*0.08:.0f}"/></filter>
  <filter id="grain{uid}"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1 0"/></filter>
  <clipPath id="clip{uid}"><rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="{rx}"/></clipPath>
  <linearGradient id="sheen{uid}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="{t['hi_a']*0.6}"/>
    <stop offset=".45" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="edge{uid}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="{t['stroke_a']*1.6 if t is THEMES['dark'] else t['stroke_a']}"/>
    <stop offset=".5" stop-color="#fff" stop-opacity="{t['stroke_a']*0.4}"/>
    <stop offset="1" stop-color="#fff" stop-opacity="{t['stroke_a']}"/>
  </linearGradient>
</defs>"""


def glass(t, uid, card):
    """Panel esmerilado: copia más borrosa del fondo recortada + velo + borde."""
    x, y, cw, ch, rx = card
    return f"""<g clip-path="url(#clip{uid})">
  <rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{t['bg']}" opacity="{.35 if t is THEMES['dark'] else .2}"/>
  <use href="#b{uid}" filter="url(#frost{uid})"/>
  <rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{t['glass']}" fill-opacity="{t['glass_a']}"/>
  <rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="url(#sheen{uid})"/>
</g>
<rect x="{x+.5}" y="{y+.5}" width="{cw-1}" height="{ch-1}" rx="{rx}" fill="none" stroke="url(#edge{uid})"/>"""


def frame(t, w, h, uid, card, body, seed=0, title=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
{defs(t, w, h, uid, card, seed)}
<rect width="{w}" height="{h}" rx="24" fill="{t['bg']}"/>
<g clip-path="url(#outer{uid})"><use href="#b{uid}" filter="url(#soft{uid})"/></g>
<clipPath id="outer{uid}"><rect width="{w}" height="{h}" rx="24"/></clipPath>
{glass(t, uid, card)}
<rect width="{w}" height="{h}" rx="24" filter="url(#grain{uid})" opacity="{t['grain_a']}"/>
{body}
</svg>"""


def header(name, t):
    w, h = 1200, 400
    card = (56, 56, 1088, 288, 28)
    body = f"""
<g font-family="{MONO}" font-size="14" letter-spacing="4" fill="{t['muted']}">
  <text x="112" y="128">WRITER <tspan fill="{t['faint']}">/</tspan> DEVELOPER <tspan fill="{t['faint']}">/</tspan> BLOGGER</text>
</g>
<text x="108" y="218" font-family="{SERIF}" font-size="76" fill="{t['ink']}" letter-spacing="-1.5">Matias Ferraro</text>
<text x="112" y="268" font-family="{SERIF}" font-style="italic" font-size="24" fill="{t['muted']}">I build things for the web and write things for the soul.</text>
<g font-family="{MONO}" font-size="15" fill="{t['muted']}">
  <text x="1088" y="300" text-anchor="end">~/code &amp;&amp; prose</text>
  <rect x="1094" y="287" width="9" height="17" rx="1.5" fill="{t['blobs'][0] if t is THEMES['light'] else '#C4B5FD'}">
    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>
</g>
<line x1="112" y1="300" x2="172" y2="300" stroke="{t['ink']}" stroke-opacity=".35" stroke-width="1.5"/>
"""
    (OUT / f"header-{name}.svg").write_text(
        frame(t, w, h, "h", card, body, title="Matias Ferraro — Writer, Developer, Blogger"))


def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > n:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return lines + [cur]


def card(slug, title, kicker, desc, tags, status, accent_idx, seed, name, t):
    w, h = 600, 280
    c = (14, 14, 572, 252, 22)
    acc = t["blobs"][accent_idx] if name == "light" else "#fff"
    dot = (["#7C3AED", "#DB2777", "#4F46E5", "#9333EA"] if name == "light" else ["#C4B5FD", "#F9A8D4", "#A5B4FC", "#E9D5FF"])[accent_idx]
    lines = wrap(desc, 52)
    desc_svg = "".join(
        f'<text x="46" y="{150 + i*24}">{esc(l)}</text>' for i, l in enumerate(lines[:2]))
    # pastillas de tecnologías
    px, pills = 46, []
    for tag in tags:
        tw = len(tag) * 7.6 + 22
        pills.append(
            f'<rect x="{px}" y="206" width="{tw:.0f}" height="26" rx="13" fill="{t["pill"]}" fill-opacity="{t["pill_a"]}" stroke="{t["pill"]}" stroke-opacity=".12"/>'
            f'<text x="{px + tw/2:.0f}" y="223.5" text-anchor="middle">{esc(tag)}</text>')
        px += tw + 8
    sw = len(status) * 7.4 + 34
    body = f"""
<text x="46" y="70" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{t['muted']}">{esc(kicker.upper())}</text>
<g font-family="{MONO}" font-size="12" fill="{t['muted']}">
  <rect x="{554 - sw:.0f}" y="52" width="{sw:.0f}" height="26" rx="13" fill="{t['pill']}" fill-opacity="{t['pill_a']}" stroke="{t['pill']}" stroke-opacity=".12"/>
  <circle cx="{554 - sw + 16:.0f}" cy="65" r="3.5" fill="{dot}">
    <animate attributeName="opacity" values="1;.35;1" dur="2.4s" repeatCount="indefinite"/>
  </circle>
  <text x="{554 - sw + 26:.0f}" y="69">{esc(status)}</text>
</g>
<text x="44" y="118" font-family="{SERIF}" font-size="36" fill="{t['ink']}" letter-spacing="-.5">{esc(title)}</text>
<g font-family="{SANS}" font-size="16" fill="{t['muted']}">{desc_svg}</g>
<g font-family="{MONO}" font-size="12" fill="{t['ink']}" fill-opacity=".8">{''.join(pills)}</g>
"""
    (OUT / f"card-{slug}-{name}.svg").write_text(
        frame(t, w, h, slug[:3], c, body, seed=seed, title=f"{title} — {desc}"))


def footer(name, t):
    w, h = 1200, 120
    c = (56, 28, 1088, 64, 32)
    body = f"""
<text x="600" y="66" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="19" fill="{t['muted']}">Thanks for stopping by — see you on the blog.</text>
"""
    (OUT / f"footer-{name}.svg").write_text(
        frame(t, w, h, "f", c, body, seed=2, title="Thanks for stopping by"))


PROJECTS = [
    ("prosalimpia", "Prosa Limpia", "AI · Writing tool",
     "Literary proofreading powered by AI, with streaming suggestions and a full revision history.",
     ["Next.js", "Supabase", "DeepSeek", "Zustand"], "Live", 0, 0),
    ("diario", "El Diario de Mati", "Blog · Travel writing",
     "Stories, travel and culture — my personal blog, with a hand-built editorial design system.",
     ["Astro", "Svelte 5", "Tailwind", "Nanostores"], "Live", 1, 1),
    ("disposable", "disposable-check", "Library · TypeScript",
     "Detects throwaway email addresses before they reach your sign-up form.",
     ["TypeScript", "Node.js", "npm"], "In progress", 2, 2),
    ("lineas", "Líneas", "Concept · Books × AI",
     "Book recommendations drawn as a map of literary influences, built from the clues you leave.",
     ["AI", "Graphs", "Literature"], "Sketching", 3, 3),
]

for name, t in THEMES.items():
    header(name, t)
    footer(name, t)
    for p in PROJECTS:
        card(*p, name, t)
print("ok", sorted(x.name for x in OUT.iterdir()))
