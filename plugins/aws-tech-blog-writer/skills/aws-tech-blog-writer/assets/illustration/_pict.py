"""Pictograms and layout helpers for illustrated concept figures in AWS Tech Blog posts.

Copy this file next to your spec_*.py files (init_workspace.py puts it in <work>/diagrams/_specs/) and
build with scripts/build_figures.py. It needs awsdiag from the aws-diagram-design skill, which the build
script puts on sys.path. Style rules and the catalog are in references/illustrations.md.

Conventions
- Every pictogram returns an SVG string. Standing objects (arm, person, humanoid, cup) take the point where
  they touch the ground; boxes (frame, monitor, server, panel, model_box) take their top-left corner.
- Ink outlines, gray bodies, orange for the thing the reader should look at. Green and red only in mark().
- A figure is a list of strings handed to canvas(); later items paint over earlier ones.
"""
import math
from awsdiag import Canvas, SANS, INK, MUTED, PAPER, SOFT, ACCENT, esc

TINT = "#FFF4E3"; GRAY = "#E9EBED"; GREEN = "#1D8102"; RED = "#D13212"; PALE = "#F7F8F8"


def g(x, y, body, s=1.0):
    return f'<g transform="translate({x},{y}) scale({s})">{body}</g>'


def txt(x, y, s, size=14, weight=400, color=MUTED, anchor="middle"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="{SANS}" text-anchor="{anchor}">{esc(s)}</text>'


def lines(x, y, items, size=14, weight=400, color=MUTED, anchor="middle", lh=None):
    lh = lh or size + 5
    return "".join(txt(x, y + i * lh, s, size, weight, color, anchor) for i, s in enumerate(items))


def title(x, y, name, sub=(), anchor="middle"):
    return txt(x, y, name, 16, 600, INK, anchor) + lines(x, y + 22, list(sub), 14, 400, MUTED, anchor)


def arrow(x1, y1, x2, y2, dashed=False, color=MUTED, via=None):
    d = f"M {x1},{y1} " + (" ".join(f"L {x},{y}" for x, y in via) + " " if via else "") + f"L {x2},{y2}"
    dash = ' stroke-dasharray="5,4"' if dashed else ""
    mk = "arrow-accent" if color == ACCENT else "arrow"
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round"{dash} marker-end="url(#{mk})"/>'


def panel(x, y, w, h, fill=PALE, dashed=False):
    dash = ' stroke-dasharray="5,4"' if dashed else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="rgba(35,47,62,0.22)" stroke-width="1"{dash}/>'


def link(x1, y1, x2, y2, w=13):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GRAY}" stroke-width="{w-4}" stroke-linecap="round"/>')


def joint(x, y, r=6.5):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{ACCENT}" stroke="{INK}" stroke-width="1.5"/>'


def arm(a1=75, a2=-15, l1=62, l2=54, gd=-90, hold=False, open_=7):
    """Robot arm, origin at the bottom centre of its base. Returns (svg, gripper tip xy in local coords)."""
    sx, sy = 0, -34
    ex, ey = sx + l1 * math.cos(math.radians(a1)), sy - l1 * math.sin(math.radians(a1))
    wx, wy = ex + l2 * math.cos(math.radians(a2)), ey - l2 * math.sin(math.radians(a2))
    dx, dy = math.cos(math.radians(gd)), -math.sin(math.radians(gd))
    px, py = -dy, dx
    cx, cy = wx + 9 * dx, wy + 9 * dy
    o = open_
    grip = "".join(
        f'<path d="M {cx + s*o*px:.1f},{cy + s*o*py:.1f} L {cx + s*o*px + 13*dx:.1f},{cy + s*o*py + 13*dy:.1f}" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>'
        for s in (-1, 1))
    palm = f'<line x1="{cx - (o+1)*px:.1f}" y1="{cy - (o+1)*py:.1f}" x2="{cx + (o+1)*px:.1f}" y2="{cy + (o+1)*py:.1f}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
    wrist = f'<line x1="{wx:.1f}" y1="{wy:.1f}" x2="{cx:.1f}" y2="{cy:.1f}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    tip = (cx + 13 * dx, cy + 13 * dy)
    held = cup(tip[0], tip[1] + 13) if hold else ""
    body = (f'<rect x="-24" y="-10" width="48" height="10" rx="3" fill="{INK}"/>'
            f'<rect x="-13" y="-34" width="26" height="26" rx="4" fill="{SOFT}" stroke="{INK}" stroke-width="1.5"/>'
            + link(sx, sy, ex, ey) + link(ex, ey, wx, wy, 11) + held + wrist + palm + grip
            + joint(sx, sy, 7.5) + joint(ex, ey) + joint(wx, wy, 5))
    return body, tip


def cup(x, y, s=1.0):
    """Cup with its bottom centre at (x, y)."""
    return g(x, y, f'<path d="M 8,-15 q 9,1 7,7 q -2,5 -8,4" fill="none" stroke="{INK}" stroke-width="2"/>'
                   f'<path d="M -9,-20 L 9,-20 L 7,0 L -7,0 Z" fill="{ACCENT}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>', s)


def table(x, y, w):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="2" fill="{SOFT}"/>'
            f'<rect x="{x+14}" y="{y+7}" width="6" height="22" fill="{SOFT}"/><rect x="{x+w-20}" y="{y+7}" width="6" height="22" fill="{SOFT}"/>')


def shelf(x, y, w, h):
    """Shelf whose board top is at y; stands on the table at y + h."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="6" rx="2" fill="{INK}"/>'
            f'<rect x="{x+w-7}" y="{y+6}" width="5" height="{h-6}" fill="{INK}"/><rect x="{x+2}" y="{y+6}" width="5" height="{h-6}" fill="{INK}"/>')


def camera(x, y, rot=0):
    body = (f'<rect x="-15" y="-10" width="30" height="20" rx="4" fill="{INK}"/>'
            f'<path d="M 15,-5 L 27,-11 L 27,11 L 15,5 Z" fill="{INK}"/><circle cx="-6" cy="0" r="4" fill="{PAPER}"/>')
    return f'<g transform="translate({x},{y}) rotate({rot})">{body}</g>'


def person(x, y, s=1.0, controller=True, flip=False):
    """Person, origin at the bottom centre of the torso."""
    ctrl = (f'<path d="M 11,-36 L 27,-26 M -11,-36 L 16,-22" stroke="{MUTED}" stroke-width="6" stroke-linecap="round" fill="none"/>'
            f'<rect x="14" y="-32" width="24" height="13" rx="4" fill="{INK}"/>'
            f'<line x1="20" y1="-32" x2="18" y2="-39" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<line x1="32" y1="-32" x2="34" y2="-39" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>') if controller else \
           f'<path d="M 11,-36 L 34,-44" stroke="{MUTED}" stroke-width="6" stroke-linecap="round" fill="none"/>'
    return g(x, y, f'<path d="M -17,0 L -14,-38 Q 0,-52 14,-38 L 17,0 Z" fill="{MUTED}"/>'
                   f'<circle cx="0" cy="-62" r="11" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>' + ctrl, s if not flip else f"{-s},{s}")


def humanoid(x, y, s=1.0, step=True):
    """Humanoid robot, origin at the ground under its hips."""
    legs = (f'<path d="M -6,-42 L -15,-22 L -10,-2 M 6,-42 L 15,-24 L 24,-4" ' if step else
            f'<path d="M -6,-42 L -8,-22 L -8,-2 M 6,-42 L 8,-22 L 8,-2" ')
    feet = ('<path d="M -14,-1 L -2,-1 M 20,-3 L 32,-3" ' if step else '<path d="M -13,-1 L -2,-1 M 3,-1 L 14,-1" ')
    kn = ((-15, -22), (15, -24)) if step else ((-8, -22), (8, -22))
    return g(x, y,
             legs + f'stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
             + feet + f'stroke="{INK}" stroke-width="5" stroke-linecap="round" fill="none"/>'
             + f'<path d="M -14,-70 L -23,-50 M 14,-70 L 24,-54" stroke="{INK}" stroke-width="6" stroke-linecap="round" fill="none"/>'
             + f'<rect x="-14" y="-78" width="28" height="38" rx="6" fill="{GRAY}" stroke="{INK}" stroke-width="1.8"/>'
             + f'<circle cx="0" cy="-62" r="4.5" fill="{ACCENT}"/>'
             + f'<rect x="-10" y="-100" width="20" height="18" rx="5" fill="{PAPER}" stroke="{INK}" stroke-width="1.8"/>'
             + f'<rect x="-6" y="-94" width="12" height="4" rx="2" fill="{ACCENT}"/>'
             + "".join(joint(a, b, 3.5) for a, b in kn), s)


def nn(x, y, s=1.0):
    """Small neural network icon, about 60 x 50, origin top-left."""
    cols = [(6, [8, 25, 42]), (30, [4, 18, 32, 46]), (54, [16, 34])]
    out = []
    for (xa, ya), (xb, yb) in zip(cols, cols[1:]):
        for p in ya:
            for q in yb:
                out.append(f'<line x1="{xa}" y1="{p}" x2="{xb}" y2="{q}" stroke="{SOFT}" stroke-width="0.8"/>')
    for i, (xc, ys) in enumerate(cols):
        for p in ys:
            out.append(f'<circle cx="{xc}" cy="{p}" r="4.2" fill="{ACCENT if i == 2 else PAPER}" stroke="{INK}" stroke-width="1.3"/>')
    return g(x, y, "".join(out), s)


def model_box(x, y, w, h, name, sub=(), focal=True):
    """Model box: network icon on the left, name and detail lines on the right."""
    fill, stroke = (TINT, ACCENT) if focal else (PAPER, INK)
    n = len(sub)
    ty = y + h / 2 - (n * 19) / 2 + 5
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
            + nn(x + 14, y + h / 2 - 25) + txt(x + 86, ty, name, 16, 600, INK, "start")
            + lines(x + 86, ty + 21, list(sub), 14, 400, MUTED, "start"))


def frame(x, y, w=64, h=46, cupx=0.5, lifted=False, grip=True, fill=PAPER, dashed=False):
    """Camera frame thumbnail: table, cup, gripper above it."""
    cx = x + w * cupx; ty = y + h - 9
    cy = ty - (12 if lifted else 0)
    dash = ' stroke-dasharray="4,3"' if dashed else ""
    gr = (f'<path d="M {cx},{y+3} V {cy-16} M {cx-6},{cy-16} H {cx+6} M {cx-6},{cy-16} v 6 M {cx+6},{cy-16} v 6" '
          f'stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>') if grip else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{INK}" stroke-width="1.4"{dash}/>'
            f'<line x1="{x+5}" y1="{ty}" x2="{x+w-5}" y2="{ty}" stroke="{SOFT}" stroke-width="3" stroke-linecap="round"/>'
            + gr + cup(cx, cy - 1.5, 0.5))


def monitor(x, y, w, h, inner=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{PAPER}" stroke="{INK}" stroke-width="1.8"/>'
            f'<rect x="{x + w/2 - 4}" y="{y+h}" width="8" height="8" fill="{INK}"/>'
            f'<rect x="{x + w/2 - 16}" y="{y+h+8}" width="32" height="4" rx="2" fill="{INK}"/>' + inner)


def server(x, y, w=74, h=92):
    # rows are 15 px tall on purpose: verify-geometry.py reads 8-14 px tall rects as label masks
    rows = "".join(
        f'<rect x="{x+8}" y="{y+10+i*20}" width="{w-16}" height="15" rx="3" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/>'
        f'<circle cx="{x+16}" cy="{y+17+i*20}" r="2.5" fill="{ACCENT}"/>'
        f'<line x1="{x+26}" y1="{y+17+i*20}" x2="{x+w-14}" y2="{y+17+i*20}" stroke="{SOFT}" stroke-width="2" stroke-linecap="round"/>'
        for i in range(4))
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{GRAY}" stroke="{INK}" stroke-width="1.6"/>' + rows


def mark(x, y, ok=True, r=10):
    p = '<path d="M -5,0 L -1.5,4 L 5,-4"' if ok else '<path d="M -4,-4 L 4,4 M 4,-4 L -4,4"'
    return g(x, y, f'<circle r="{r}" fill="{GREEN if ok else RED}"/>' + p + f' stroke="{PAPER}" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def bubble(x, y, w, h, text, tail="down"):
    t = (f'<path d="M {x+26},{y+h-1} l 6,12 l 8,-12" fill="{PAPER}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
         f'<line x1="{x+27}" y1="{y+h}" x2="{x+39}" y2="{y+h}" stroke="{PAPER}" stroke-width="2.5"/>') if tail == "down" else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2 if h < 40 else 12}" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/>' + t
            + txt(x + w / 2, y + h / 2 + 5, text, 14, 400, INK))


def chip(x, y, text, w=None, color=INK, fill=PAPER):
    w = w or 16 + len(text) * 9
    return (f'<rect x="{x - w/2}" y="{y-13}" width="{w}" height="24" rx="12" fill="{fill}" stroke="{color}" stroke-width="1.2"/>'
            + txt(x, y + 4, text, 13, 600, color))


def doc(x, y, w=44, h=56):
    """Document sheet with a folded corner and text lines, origin top-left."""
    rows = "".join(f'<line x1="{x+8}" y1="{y+20+i*9}" x2="{x+w-8 - (10 if i == 3 else 0)}" y2="{y+20+i*9}" stroke="{SOFT}" stroke-width="2" stroke-linecap="round"/>' for i in range(4))
    return (f'<path d="M {x},{y} H {x+w-12} L {x+w},{y+12} V {y+h} H {x} Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>'
            f'<path d="M {x+w-12},{y} V {y+12} H {x+w}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>' + rows)


def db(x, y, w=56, h=62):
    """Storage cylinder, origin top-left."""
    r = 9
    return (f'<path d="M {x},{y+r} V {y+h-r} A {w/2},{r} 0 0 0 {x+w},{y+h-r} V {y+r}" fill="{GRAY}" stroke="{INK}" stroke-width="1.6"/>'
            f'<ellipse cx="{x+w/2}" cy="{y+r}" rx="{w/2}" ry="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>'
            f'<path d="M {x},{y+h/2} A {w/2},{r} 0 0 0 {x+w},{y+h/2}" fill="none" stroke="{SOFT}" stroke-width="1.4"/>'
            f'<circle cx="{x+12}" cy="{y+h-16}" r="2.5" fill="{ACCENT}"/>')


def ground(x1, x2, y):
    """Floor line under standing objects that have no table."""
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{SOFT}" stroke-width="3" stroke-linecap="round"/>'


def motion(d, color=ACCENT, head=True):
    """Dashed path for intended motion or a teleoperation link. d is an SVG path, e.g. 'M 200,268 Q 270,170 352,214'."""
    mk = f' marker-end="url(#arrow-accent)"' if head and color == ACCENT else (' marker-end="url(#arrow)"' if head else "")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" stroke-dasharray="5,4"{mk}/>'


def put_arm(x, y, **kw):
    """Place arm() with its base centre at (x, y). Returns (svg, gripper tip in canvas coords)."""
    body, tip = arm(**kw)
    return g(x, y, body), (x + tip[0], y + tip[1])


GRASP = dict(a1=70, a2=-50)                 # gripper around a cup standing 56 px right of the base
CARRY = dict(a1=80, a2=10, hold=True)       # cup held in the air, up and to the right


def canvas(slug, title_, desc, h, parts, w=960, lang="ko"):
    """Canvas of w x h (viewBox px) whose body is the list of SVG strings in parts."""
    c = Canvas(w, h, slug, title_, desc, lang)
    c.overlay.append("".join(parts))
    return c
