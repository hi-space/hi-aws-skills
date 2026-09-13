#!/usr/bin/env python3
"""
PPTX Layout & Copy QA (aws-ppt-master)

Catches structural issues that visual inspection misses because rendered
images clip objects at slide boundaries.

Problem: When a shape extends beyond the slide edge, soffice/pdftoppm
simply crops it. The QA subagent sees a normal-looking image and passes it.
This script reads the OOXML directly and flags what the renderer hides.

Checks:
  - bounds:     Shapes/groups outside slide boundaries. Exempts a low-alpha
                full-bleed wash ellipse: an unstroked ellipse whose solid
                fill is at or below WASH_MAX_ALPHA (20%). That bleed off the
                stage is intentional, because a fully contained ellipse reads
                as a drawn oval at any alpha, so flagging it would push a
                builder into the very defect the exemption prevents. Above
                the ceiling it is the banned decorative orb and still reports
                critical, which makes this check the enforcement of the
                alpha rule rather than a contradiction of it.
  - connector:  Arrow/line endpoints outside slide, zero-length connectors
  - font_size:  Text below 15pt minimum (body) or 8pt (caption)
  - zero_size:  Invisible shapes (0 width or 0 height). Exempts a LINE with
                exactly one zero dimension, which is how a horizontal rule
                is drawn. A LINE with both dimensions zero, or any other
                shape with a zero dimension, is still reported.
  - image_aspect: Embedded PNG/JPEG whose slide placement aspect differs
                  from the source pixel aspect by more than 2%. This catches
                  SVG-rasterized diagrams whose labels are visibly stretched
                  because the caller hand-typed (w, h) instead of computing
                  them from the source aspect ratio.
  - ai_copy:    Machine-detectable signatures of AI-drafted slide copy
                (full rules in references/copy-voice.md). Two severities:

                CRITICAL, fails the build:
                  * em dash / en dash anywhere in slide copy. Banned
                    outright, spaced or tight. Hyphenated compounds
                    (cloud-native, m5.xlarge) are never touched: the rule
                    is about dash as punctuation, not the hyphen glyph.
                  * a middot (·) or bullet (•) used as an inline separator
                    between phrases ("자동화 · 관측 · 회수"). A leading list
                    bullet is fine; a dot between words is the tell.
                  * meta-commentary labels that occupy the slot where the
                    answer belongs ("왜 중요한가", "핵심 시사점",
                    "Why this matters", "Key takeaway").

                WARNING, advisory:
                  * the contrastive reflex ("단순히 A가 아니라 B",
                    "not just X but Y") and meta narration
                    ("이는 ~을 의미합니다"), which need human judgment
                    because both are occasionally the right call.
                  * an ASCII hyphen with a space on both sides doing a
                    colon's job.

                Judgment-level tells (번역투, tricolon reflex, monotone
                endings) are NOT machine-checked. They live in the
                copy-voice recipe and the Bedrock copy pass.

Usage: python3 scripts/pptx_qa_check.py <deck.pptx> [--checks ...] [--json] [--strict]

Exit codes:
    0  No critical issues found
    1  Critical issues found — must fix before delivery
    2  Error (file not found, parse failure, etc.)

Ported from jesamkim/oh-my-skills myslide qa_validate.py (MIT).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

try:
    from pptx import Presentation
except ImportError:
    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "python-pptx", "lxml", "-q"]
    )
    from pptx import Presentation


# ── Constants ──────────────────────────────────────────────────────────

EMU_PER_INCH = 914400

# Font thresholds in 100ths-of-a-point (OOXML stores sizes this way).
# 1500 = 15pt (body minimum), 800 = 8pt (caption minimum).
MIN_BODY_SZ = 1500
MIN_CAPTION_SZ = 800

# Shapes covering >90% of slide area are treated as backgrounds/overlays
# and excluded from bounds checking (they're intentionally full-bleed).
BG_AREA_RATIO = 0.90

# Image aspect-ratio mismatch threshold. Anything beyond this means
# labels and icons inside the image are visibly distorted. 2% catches
# the SVG-stretch defect without false-positives from rounding.
ASPECT_TOLERANCE = 0.02

# Backgrounds/full-bleed images intentionally fill the slide; they are
# typically gradients/blobs without meaningful in-image content, so a
# stretch is fine. We skip aspect checks for any image covering >90% of
# the slide (same threshold as bounds) AND for very small images
# (icons, footer logos) where stretching is nearly imperceptible.
ASPECT_MIN_AREA_IN2 = 1.0  # square inches; below this, skip the check

# OOXML namespaces
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


# ── Issue ──────────────────────────────────────────────────────────────


class Issue:
    def __init__(self, level, slide_num, check, message, **details):
        self.level = level  # "critical" | "warning" | "info"
        self.slide_num = slide_num
        self.check = check
        self.message = message
        self.details = details

    def to_dict(self):
        d = {
            "level": self.level,
            "slide": self.slide_num,
            "check": self.check,
            "message": self.message,
        }
        d.update(self.details)
        return d

    def __str__(self):
        tag = self.level.upper()
        return f"[{tag}] {self.message}"


# ── Helpers ────────────────────────────────────────────────────────────


def emu_to_in(emu):
    """EMU → inches, 2 decimal places."""
    return round(emu / EMU_PER_INCH, 2) if emu is not None else None


def _is_bg(shape, sw, sh):
    """True if shape covers >90% of slide (background/overlay)."""
    w, h = shape.width, shape.height
    if w is None or h is None:
        return False
    return (w * h) > (sw * sh * BG_AREA_RATIO)


# OOXML alpha is in thousandths of a percent, so 20% is 20000. This ceiling is
# the measured boundary for the sanctioned exception: a low-alpha full-bleed
# wash ellipse rendered at 8 / 16 / 25 / 40% put the point where an ellipse
# stops reading as atmosphere and starts reading as a drawn oval between 16%
# and 25%.
WASH_MAX_ALPHA = 20000


def _shape_geom(shape):
    """Return the shape's prstGeom preset name, or None."""
    spPr = shape._element.find(f"{{{P_NS}}}spPr")
    if spPr is None:
        return None
    geom = spPr.find(f"{{{A_NS}}}prstGeom")
    return geom.get("prst") if geom is not None else None


def _solid_fill_alpha(shape):
    """Solid-fill alpha in OOXML thousandths, or None when there is no solid
    fill (missing fill element, gradient fill, or picture fill)."""
    spPr = shape._element.find(f"{{{P_NS}}}spPr")
    if spPr is None:
        return None
    clr = spPr.find(f"{{{A_NS}}}solidFill/{{{A_NS}}}srgbClr")
    if clr is None:
        return None
    alpha = clr.find(f"{{{A_NS}}}alpha")
    return int(alpha.get("val")) if alpha is not None else 100000


def _has_stroke(shape):
    """True if the shape draws a visible outline."""
    spPr = shape._element.find(f"{{{P_NS}}}spPr")
    if spPr is None:
        return False
    ln = spPr.find(f"{{{A_NS}}}ln")
    if ln is None or ln.find(f"{{{A_NS}}}noFill") is not None:
        return False
    return (
        ln.find(f"{{{A_NS}}}solidFill") is not None
        or ln.find(f"{{{A_NS}}}gradFill") is not None
    )


def _is_cover_wash(shape):
    """True for a sanctioned native cover-wash ellipse.

    A low-alpha full-bleed wash ellipse is the sanctioned exception permitted
    to bleed off the stage: an unstroked ellipse whose solid fill sits at or
    below WASH_MAX_ALPHA, used in place of a background PNG. The off-stage
    bleed is intentional, because a fully contained ellipse reads as a drawn
    oval at any alpha. Reporting it as out-of-bounds would push a builder to
    pull the ellipse inside the slide to clear the gate, producing exactly the
    defect the exemption exists to prevent.

    The alpha ceiling is what stops this from being a hole in check_bounds. An
    ellipse bleeding off the stage above the ceiling is the banned decorative
    orb, and it still reports critical.

    Known limit: a legitimately oversized low-alpha ellipse used as a diagram
    element (not as a cover wash) is also exempted. That is the deliberate
    trade, since a false critical on a correct deck teaches builders to ignore
    this check, and the visual QA pass still reads the slide.
    """
    if _shape_geom(shape) != "ellipse":
        return False
    if _has_stroke(shape):
        return False
    alpha = _solid_fill_alpha(shape)
    return alpha is not None and alpha <= WASH_MAX_ALPHA


def _is_rule_line(shape):
    """True for a straight rule drawn as a LINE with one zero dimension.

    A horizontal rule is drawn as a zero-height line (w>0/h=0) and a vertical
    rule as a zero-width line (w=0/h>0), so the zero dimension is the intended
    geometry rather than an invisible shape. Both dimensions zero is still
    degenerate and stays reported.
    """
    if _shape_geom(shape) != "line":
        return False
    w, h = shape.width or 0, shape.height or 0
    return (w == 0) != (h == 0)


def _font_sz(run_elem):
    """Return font size in 100ths-pt from <a:rPr sz='...'>, or None."""
    rPr = run_elem.find(f"{{{A_NS}}}rPr")
    if rPr is not None:
        sz = rPr.get("sz")
        if sz is not None:
            return int(sz)
    return None


def _shape_name_from_cxn(cxn_elem):
    """Extract shape name from a <p:cxnSp> element."""
    nvPr = cxn_elem.find(f"{{{P_NS}}}nvCxnSpPr")
    if nvPr is not None:
        cNvPr = nvPr.find(f"{{{P_NS}}}cNvPr")
        if cNvPr is not None:
            return cNvPr.get("name", "Connector")
    return "Connector"


# ── Check: bounds ──────────────────────────────────────────────────────


def check_bounds(prs):
    """Flag shapes whose bounding box extends beyond the slide."""
    issues = []
    sw, sh = prs.slide_width, prs.slide_height

    for idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if shape.left is None or shape.top is None:
                continue
            if _is_bg(shape, sw, sh):
                continue
            if _is_cover_wash(shape):
                continue

            l, t = shape.left, shape.top
            w = shape.width or 0
            h = shape.height or 0
            r, b = l + w, t + h

            overflows = []
            if l < 0:
                overflows.append(f"left by {emu_to_in(abs(l))}\"")
            if t < 0:
                overflows.append(f"top by {emu_to_in(abs(t))}\"")
            if r > sw:
                overflows.append(f"right by {emu_to_in(r - sw)}\"")
            if b > sh:
                overflows.append(f"bottom by {emu_to_in(b - sh)}\"")

            if not overflows:
                continue

            fully_outside = r <= 0 or b <= 0 or l >= sw or t >= sh
            verb = "entirely outside" if fully_outside else "extends beyond"

            issues.append(
                Issue(
                    "critical",
                    idx,
                    "bounds",
                    f"Shape '{shape.name}' {verb} slide ({', '.join(overflows)})",
                    shape=shape.name,
                    position=f"({emu_to_in(l)}\", {emu_to_in(t)}\")",
                    size=f"({emu_to_in(w)}\" x {emu_to_in(h)}\")",
                )
            )

    return issues


# ── Check: connectors ─────────────────────────────────────────────────


def check_connectors(prs):
    """Validate connector/arrow endpoints and lengths."""
    issues = []
    sw, sh = prs.slide_width, prs.slide_height

    for idx, slide in enumerate(prs.slides, 1):
        slide_xml = slide._element

        for cxn in slide_xml.findall(f".//{{{P_NS}}}cxnSp"):
            name = _shape_name_from_cxn(cxn)

            xfrm = cxn.find(f".//{{{A_NS}}}xfrm")
            if xfrm is None:
                continue

            off = xfrm.find(f"{{{A_NS}}}off")
            ext = xfrm.find(f"{{{A_NS}}}ext")
            if off is None or ext is None:
                continue

            x = int(off.get("x", 0))
            y = int(off.get("y", 0))
            cx = int(ext.get("cx", 0))
            cy = int(ext.get("cy", 0))

            # Zero-length connector → invisible
            if cx == 0 and cy == 0:
                issues.append(
                    Issue(
                        "warning",
                        idx,
                        "connector",
                        f"Connector '{name}' has zero length (invisible)",
                        shape=name,
                    )
                )
                continue

            # Determine actual start/end considering flips
            flip_h = xfrm.get("flipH") == "1"
            flip_v = xfrm.get("flipV") == "1"

            sx = (x + cx) if flip_h else x
            sy = (y + cy) if flip_v else y
            ex = x if flip_h else (x + cx)
            ey = y if flip_v else (y + cy)

            for label, px, py in [("start", sx, sy), ("end", ex, ey)]:
                if px < 0 or py < 0 or px > sw or py > sh:
                    issues.append(
                        Issue(
                            "critical",
                            idx,
                            "connector",
                            f"Connector '{name}' {label} point outside slide "
                            f"at ({emu_to_in(px)}\", {emu_to_in(py)}\")",
                            shape=name,
                        )
                    )

            # Very short connector (< 0.1") — often a positioning mistake
            length_sq = cx * cx + cy * cy
            min_len = int(0.1 * EMU_PER_INCH)
            if 0 < length_sq < min_len * min_len:
                length_in = emu_to_in(int(length_sq**0.5))
                issues.append(
                    Issue(
                        "info",
                        idx,
                        "connector",
                        f"Connector '{name}' is very short ({length_in}\")",
                        shape=name,
                    )
                )

    return issues


# ── Check: font sizes ─────────────────────────────────────────────────


def check_font_sizes(prs):
    """Flag text below the 15pt body minimum or 8pt caption minimum."""
    issues = []

    for idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue

            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    sz = _font_sz(run._r)
                    if sz is None:
                        continue  # inherited from theme — can't check

                    text = run.text.strip()
                    if not text:
                        continue

                    preview = text[:40]
                    pt = sz / 100

                    if sz < MIN_CAPTION_SZ:
                        issues.append(
                            Issue(
                                "critical",
                                idx,
                                "font_size",
                                f"Text {pt}pt in '{shape.name}' (min 8pt): \"{preview}\"",
                                shape=shape.name,
                                size_pt=pt,
                            )
                        )
                    elif sz < MIN_BODY_SZ:
                        issues.append(
                            Issue(
                                "warning",
                                idx,
                                "font_size",
                                f"Text {pt}pt in '{shape.name}' (body min 15pt): \"{preview}\"",
                                shape=shape.name,
                                size_pt=pt,
                            )
                        )

    return issues


# ── Check: image aspect ratio mismatch ────────────────────────────────


def _read_image_dimensions(blob: bytes):
    """Return (width_px, height_px) from PNG/JPEG bytes, or None.

    Uses PIL if available (handles every format), otherwise falls back
    to a tiny PNG/JPEG header parser so the script works without extra
    deps in CI.
    """
    try:
        import io

        from PIL import Image  # type: ignore

        with Image.open(io.BytesIO(blob)) as im:
            return im.size
    except ImportError:
        pass
    except Exception:
        return None

    # PNG signature: 8 bytes, then IHDR chunk has width/height as big-endian uint32
    if blob[:8] == b"\x89PNG\r\n\x1a\n" and len(blob) >= 24:
        import struct

        w, h = struct.unpack(">II", blob[16:24])
        return w, h

    # Minimal JPEG SOF parser
    if blob[:2] == b"\xff\xd8" and len(blob) > 4:
        import struct

        i = 2
        try:
            while i < len(blob):
                if blob[i] != 0xFF:
                    return None
                marker = blob[i + 1]
                # Standalone markers
                if marker in (0xD8, 0xD9):
                    i += 2
                    continue
                seg_len = struct.unpack(">H", blob[i + 2 : i + 4])[0]
                # SOF0..SOF15 (excluding DHT=C4, DAC=CC, DNL=DC)
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", blob[i + 5 : i + 9])
                    return w, h
                i += 2 + seg_len
        except Exception:
            return None

    return None


def check_image_aspect(prs):
    """Flag images whose placement aspect ratio differs from source by > 2%."""
    issues = []
    sw, sh = prs.slide_width, prs.slide_height
    sw_in = sw / EMU_PER_INCH
    sh_in = sh / EMU_PER_INCH

    for idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            # Picture is shape_type 13 (MSO_SHAPE_TYPE.PICTURE)
            if shape.shape_type != 13:
                continue

            try:
                blob = shape.image.blob
            except Exception:
                continue

            if shape.width is None or shape.height is None:
                continue
            if shape.width == 0 or shape.height == 0:
                continue

            # Skip backgrounds/full-bleed
            if _is_bg(shape, sw, sh):
                continue

            placement_w_in = shape.width / EMU_PER_INCH
            placement_h_in = shape.height / EMU_PER_INCH

            # Skip very small images (icons, footer logos) — stretch
            # imperceptible at this scale, and not worth the noise.
            if placement_w_in * placement_h_in < ASPECT_MIN_AREA_IN2:
                continue

            # Skip images that nearly fill the slide — they are
            # intentionally full-bleed gradients/photos.
            if (
                placement_w_in / sw_in > 0.95
                and placement_h_in / sh_in > 0.95
            ):
                continue

            dims = _read_image_dimensions(blob)
            if dims is None:
                continue
            src_w, src_h = dims
            if src_w == 0 or src_h == 0:
                continue

            src_aspect = src_w / src_h
            placement_aspect = shape.width / shape.height
            stretch = abs(placement_aspect - src_aspect) / src_aspect

            if stretch <= ASPECT_TOLERANCE:
                continue

            # Direction of stretch
            direction = (
                "horizontal stretch (image squashed wider)"
                if placement_aspect > src_aspect
                else "vertical stretch (image squashed taller)"
            )
            level = "critical" if stretch > 0.10 else "warning"

            issues.append(
                Issue(
                    level,
                    idx,
                    "image_aspect",
                    f"Image '{shape.name}' aspect mismatch: source "
                    f"{src_w}x{src_h} (ratio {round(src_aspect, 3)}) "
                    f"placed at {round(placement_w_in, 2)}\" x "
                    f"{round(placement_h_in, 2)}\" (ratio "
                    f"{round(placement_aspect, 3)}) — "
                    f"{round(stretch * 100, 1)}% {direction}",
                    shape=shape.name,
                    source_px=f"{src_w}x{src_h}",
                    source_aspect=round(src_aspect, 3),
                    placement_in=f"{round(placement_w_in, 2)}x{round(placement_h_in, 2)}",
                    placement_aspect=round(placement_aspect, 3),
                    stretch_pct=round(stretch * 100, 1),
                )
            )

    return issues


# ── Check: zero-size shapes ───────────────────────────────────────────


def check_zero_size(prs):
    """Flag shapes with zero width or height (invisible/broken)."""
    issues = []

    for idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if _is_rule_line(shape):
                continue
            w, h = shape.width, shape.height
            if w is not None and h is not None and (w == 0 or h == 0):
                dim = "width" if w == 0 else "height"
                issues.append(
                    Issue(
                        "warning",
                        idx,
                        "zero_size",
                        f"Shape '{shape.name}' has zero {dim} (invisible)",
                        shape=shape.name,
                    )
                )

    return issues


# ── Check: AI-copy signature (space-padded dash) ──────────────────────

# Detectors for the copy patterns in references/copy-voice.md. Kept in step
# with the html-slide sibling's scripts/check_copy.py: if you change a pattern
# here, change it there too, or the two skills disagree about what ships.
import re

# BANNED. Em dash and en dash do not appear in slide copy at all, spaced or
# tight. Hyphenated compounds and identifiers (cloud-native, m5.xlarge, 24-7)
# use U+002D HYPHEN-MINUS, which is a different character and never matches.
_BANNED_DASH = re.compile(r"[—–]")

# BANNED. A middle dot (U+00B7) or bullet (U+2022) used as an INLINE SEPARATOR
# between phrases ("빠르고 · 저렴하고 · 안전한", "자동화·관측·회수") is one of the
# most reliable machine fingerprints of AI-drafted slide copy, like the em dash.
# Requiring a non-space on BOTH sides of the dot is what distinguishes a
# separator from a legitimate leading list bullet: _slide_lines strips each
# paragraph, so a leading "• 항목" / "· 항목" has the dot at index 0 with nothing
# before it and never matches. Genuine PowerPoint bullets are paragraph
# properties (buChar), not run text, so they never reach this check either.
_BANNED_MIDDOT_SEP = re.compile(r"\S[ \t]*[·•][ \t]*\S")

# An ASCII hyphen with a space on both sides, doing a colon's job. Softer than
# the above (it is also how some people legitimately type a range), so warning.
_SPACED_HYPHEN = re.compile(r"\S\s(?:-|--)\s\S")

# Meta-commentary labels: the slot that should hold the answer holds the
# category instead. Bad in any slot, which is why this needs no slot analysis.
# Deliberately NOT included: navigational section labels whose answer sits next
# to them ("무엇을 했는가", "지금의 문제", "다음 단계"). See copy-voice.md
# "Where this rule stops" — flagging those would punish well-built decks.
_META_LABEL = [
    "왜 중요한가", "왜 중요할까", "왜 중요한지", "왜 중요합니까",
    "핵심 시사점", "주요 시사점",
    "이것이 의미하는", "이것은 무엇을 의미", "무엇을 의미하는가",
    "무엇을 의미하나", "무엇을 의미할까", "무엇을 뜻하는가",
    "why this matters", "why it matters", "why that matters",
    "key takeaway", "the key takeaway", "what this means",
    "the bigger picture",
]

# Softer meta markers: often filler, occasionally the right word. Warning.
_META_SOFT = ["더 큰 그림", "한 걸음 물러나", "주목할 점", "핵심 포인트",
              "눈여겨볼 점", "시사점", "zoom out", "stepping back"]

# Includes the BARE "A가 아니라 B" form. Measured over 8 generation runs
# (2026-08-18): 0.77 hits/slide on Opus 5, 0.23 on Fable 5, and every instance
# omitted "단순히", so a rule scoped to that adverb catches almost none of them.
# A single hit can be a real correction, so severity is decided by density.
# Excluded because they are different constructions, not the contrastive tic:
#   아니라면 (conditional), 아니라도 (concessive), 아니라서 (reason),
#   아니라고 (quotative), and "뿐만 아니라" (additive "not only X but also Y").
_CONTRAST = re.compile(
    r"(?<!뿐만 )아니라(?![면도서고])"
    r"|아닌\s+(?:것|게)\b"
    r"|\bnot\s+(?:just|only|merely)\b"
    r"|[,\u2014\u2013]\s*not\s+\w",
    re.IGNORECASE,
)

# Above this per-slide average the reflex is systemic rather than deliberate.
# Set below the measured Fable floor (0.23) so a genuinely comparison-heavy
# deck can still use it once or twice without tripping the deck-level finding.
_CONTRAST_DENSITY = 0.4
_CONTRAST_MIN = 3

# Meta narration: a sentence commenting on the previous sentence.
_META_NARRATION = re.compile(r"(?:이는|이것은|이 결과는|이러한 변화는)\s*.{0,40}?(?:의미|뜻)합니")


# Code is not copy. A code sample legitimately contains arithmetic ("n - 1"),
# shell separators ("npm run build -- --watch"), and identifiers, none of which
# are prose tics. PPTX has no <code> element, so monospace font is the only
# available signal, and it is a reliable one: the docs-style code patterns in
# this skill all set a monospace face. The html-slide sibling excludes
# <pre>/<code> for the same reason, which keeps the two checkers equivalent.
# Matched on whole tokens, never as a substring. A substring test looks fine
# until "Monotype Corsiva" (a decorative serif) matches "mono" and the paragraph
# is skipped, which silently disables the critical dash check for that text.
# A false negative here is worse than the false positive it was meant to fix.
# Families whose names carry no "mono" token, so they need naming outright.
_MONO_FAMILIES = ("courier", "consolas", "monaco", "menlo", "d2coding",
                  "inconsolata", "iosevka", "fira code", "source code pro",
                  "andale", "lucida console", "sfmono", "cascadia code",
                  "cascadia mono")
_MONO_TOKENS = {"mono", "monospace", "monospaced"}
_MONO_SPLIT = __import__("re").compile(r"[\s\-_,]+")


def _is_mono_run(run):
    """True if this run is set in a monospace face, i.e. it is code.

    PPTX has no <code> element, so the font is the only available signal. When
    the face is inherited from the theme, run.font.name is None and this returns
    False, so the run is checked as prose. That is the safe direction: it can
    produce a warning on code, never a missed critical finding on prose.

    Matched on whole tokens, never as a substring. A substring test looks fine
    until "Monotype Corsiva" (a decorative serif) matches "mono" and its text is
    dropped, which silently disables the critical dash check for that text.
    """
    raw = (run.font.name or "").strip().lower()
    if not raw:
        return False
    # Normalise separators first so "Fira-Code" and "Fira Code" behave alike.
    name = " ".join(t for t in _MONO_SPLIT.split(raw) if t)
    if set(name.split()) & _MONO_TOKENS:
        return True
    return any(name == f or name.startswith(f + " ") for f in _MONO_FAMILIES)


def _slide_lines(slide):
    """Every on-slide prose paragraph as one string, code runs removed.

    Runs are joined because PowerPoint routinely splits a single visible
    sentence across runs at formatting boundaries, so a per-run scan misses any
    pattern that straddles one.

    Code is filtered per RUN, not per paragraph. Dropping a whole paragraph
    because one run is monospace is a real bypass: styling a single inline
    identifier in a code face is common, so
    "배포 주기는 " + "m5.xlarge"(mono) + " 기준 — 하루 단위입니다"
    would have taken its banned em dash with it and exited 0. A fully
    monospace paragraph still yields nothing and is skipped.
    """
    lines = []
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            line = "".join(r.text for r in para.runs
                           if not _is_mono_run(r)).strip()
            if line:
                lines.append(line)
    return lines


def check_ai_copy(prs):
    """Flag machine-detectable AI-copy signatures (see copy-voice.md).

    Dash and meta-label findings are critical: they fail the build, because
    the user's rule on them is absolute and both are unambiguous to detect.
    Contrast reflexes and meta narration are warnings, since each is
    occasionally correct and needs a human or the copy pass to judge.
    """
    issues = []
    dash_total, dash_slides = 0, []
    middot_total, middot_slides = 0, []
    contrast_total, contrast_slides, contrast_examples = 0, [], []

    for idx, slide in enumerate(prs.slides, 1):
        lines = _slide_lines(slide)
        blob = "\n".join(lines)
        low = blob.lower()

        # ── critical: banned dashes ──
        hits = [ln for ln in lines if _BANNED_DASH.search(ln)]
        if hits:
            n = sum(len(_BANNED_DASH.findall(ln)) for ln in hits)
            dash_total += n
            dash_slides.append(idx)
            issues.append(
                Issue(
                    "critical",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: {n} em/en dash(es) in slide copy, which is "
                    f"banned. Use a period, a colon, a line break, or ~ for a "
                    f"range. Offending line(s): "
                    + " | ".join(h[:70] for h in hits[:3]),
                    count=n,
                )
            )

        # ── critical: middot / bullet-dot inline separator ──
        mhits = [ln for ln in lines if _BANNED_MIDDOT_SEP.search(ln)]
        if mhits:
            n = sum(len(_BANNED_MIDDOT_SEP.findall(ln)) for ln in mhits)
            middot_total += n
            middot_slides.append(idx)
            issues.append(
                Issue(
                    "critical",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: {n} middot/bullet separator(s) ('·' or '•' "
                    f"between phrases) in slide copy, which is banned. Use a "
                    f"comma, a line break, or a real list item instead. A "
                    f"leading list bullet is fine; a dot between words is the "
                    f"tell. Offending line(s): "
                    + " | ".join(h[:70] for h in mhits[:3]),
                    count=n,
                )
            )

        # ── critical: meta-commentary labels ──
        found = [p for p in _META_LABEL if p in blob or p in low]
        if found:
            issues.append(
                Issue(
                    "critical",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: meta-commentary label(s) "
                    f"{', '.join(repr(f) for f in found)}. This slot should "
                    f"hold the answer, with its number, not the category of "
                    f"the answer. If nothing on the slide answers it, the fix "
                    f"is the missing fact, not a reworded label.",
                    count=len(found),
                )
            )

        # ── warning: softer meta markers ──
        # Skip any soft marker already covered by a critical hit above, since
        # "시사점" is a substring of "핵심 시사점" and would double-report one label.
        soft = [p for p in _META_SOFT
                if (p in blob or p in low) and not any(p in f for f in found)]
        if soft:
            issues.append(
                Issue(
                    "warning",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: possible meta filler "
                    f"{', '.join(repr(s) for s in soft)}. Keep it only if it "
                    f"introduces a specific that is actually on the slide.",
                    count=len(soft),
                )
            )

        # ── warning: contrastive reflex ──
        cl = [ln for ln in lines if _CONTRAST.search(ln)]
        if cl:
            contrast_total += len(cl)
            contrast_slides.append(idx)
            contrast_examples.extend(cl)
            issues.append(
                Issue(
                    "warning",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: contrastive reflex ('A가 아니라 B' / "
                    f"'not just X but Y') on {len(cl)} line(s). Delete the "
                    f"foil and keep the claim, unless the room actually holds "
                    f"the belief being corrected: "
                    + " | ".join(c[:70] for c in cl[:2]),
                    count=len(cl),
                )
            )

        # ── warning: meta narration ──
        nl = [ln for ln in lines if _META_NARRATION.search(ln)]
        if nl:
            issues.append(
                Issue(
                    "warning",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: narration about the content on "
                    f"{len(nl)} line(s). Replace with the outcome itself: "
                    + " | ".join(x[:70] for x in nl[:2]),
                    count=len(nl),
                )
            )

        # ── warning: spaced ASCII hyphen as separator ──
        sh = [ln for ln in lines if _SPACED_HYPHEN.search(ln)]
        if sh:
            issues.append(
                Issue(
                    "warning",
                    idx,
                    "ai_copy",
                    f"Slide {idx}: {len(sh)} line(s) use ' - ' where a colon "
                    f"or a period reads better: "
                    + " | ".join(s[:70] for s in sh[:2]),
                    count=len(sh),
                )
            )

    if dash_total:
        issues.append(
            Issue(
                "critical",
                0,
                "ai_copy",
                f"Deck-wide: {dash_total} banned em/en dash(es) across "
                f"{len(dash_slides)} slide(s). Run the Opus 4.6 copy pass "
                f"(references/copy-voice.md) and rebuild before delivery.",
                count=dash_total,
                slides=dash_slides,
            )
        )

    if middot_total:
        issues.append(
            Issue(
                "critical",
                0,
                "ai_copy",
                f"Deck-wide: {middot_total} banned middot/bullet separator(s) "
                f"across {len(middot_slides)} slide(s). Run the copy pass "
                f"(references/copy-voice.md) and rebuild before delivery.",
                count=middot_total,
                slides=middot_slides,
            )
        )

    # A deck averaging more than _CONTRAST_DENSITY contrastive lines per slide
    # is using the reflex as a default sentence shape, not as an argument.
    n = len(prs.slides)
    if n and contrast_total >= _CONTRAST_MIN and contrast_total / n >= _CONTRAST_DENSITY:
        issues.append(
            Issue(
                "warning",
                0,
                "ai_copy",
                f"Deck-wide: {contrast_total} contrastive-reflex line(s) across "
                f"{len(contrast_slides)} slide(s) "
                f"(~{round(contrast_total / n, 2)}/slide). Budget is one per "
                f"deck. At this density it is the default sentence shape rather "
                f"than an argument, which is the most common reason Korean slide "
                f"copy reads machine-drafted. Run the Opus 4.6 copy pass. "
                f"Examples: " + " | ".join(c[:60] for c in contrast_examples[:3]),
                count=contrast_total,
                slides=contrast_slides,
            )
        )

    return issues


# ── Orchestration ──────────────────────────────────────────────────────


CHECKS = {
    "bounds": check_bounds,
    "connectors": check_connectors,
    "font_size": check_font_sizes,
    "zero_size": check_zero_size,
    "image_aspect": check_image_aspect,
    "copy": check_ai_copy,
}


def validate(pptx_path, strict=False, checks=None):
    """Run the selected checks (all by default). Returns (issues, presentation)."""
    prs = Presentation(pptx_path)
    selected = list(CHECKS) if not checks else list(checks)
    unknown = [c for c in selected if c not in CHECKS]
    if unknown:
        raise ValueError(f"unknown checks: {unknown}; valid: {sorted(CHECKS)}")
    all_issues = []
    for name in selected:
        all_issues.extend(CHECKS[name](prs))
    if not strict:
        all_issues = [i for i in all_issues if i.level != "info"]
    return all_issues, prs


def format_report(issues, prs, pptx_path):
    """Human-readable report."""
    sw = emu_to_in(prs.slide_width)
    sh = emu_to_in(prs.slide_height)
    n = len(prs.slides)

    lines = [
        "=== PPTX QA Validation Report ===",
        f"File: {Path(pptx_path).name}",
        f"Slides: {n}   Size: {sw}\" x {sh}\"",
        "",
    ]

    if not issues:
        lines.append("All checks passed — no issues found.")
        return "\n".join(lines)

    by_slide = defaultdict(list)
    for issue in issues:
        by_slide[issue.slide_num].append(issue)

    for sn in sorted(by_slide):
        header = "Deck-wide" if sn == 0 else f"Slide {sn}"
        lines.append(f"--- {header} ---")
        for issue in by_slide[sn]:
            lines.append(f"  {issue}")
            # Add position/size details for bounds issues
            if "position" in issue.details:
                lines.append(
                    f"    Position: {issue.details['position']}  "
                    f"Size: {issue.details['size']}"
                )
        lines.append("")

    crit = sum(1 for i in issues if i.level == "critical")
    warn = sum(1 for i in issues if i.level == "warning")
    info = sum(1 for i in issues if i.level == "info")

    lines.append("=== Summary ===")
    parts = []
    if crit:
        parts.append(f"{crit} critical")
    if warn:
        parts.append(f"{warn} warning")
    if info:
        parts.append(f"{info} info")
    lines.append(f"Total: {len(issues)} ({', '.join(parts)})")
    lines.append(f"Slides with issues: {len(by_slide)} / {n}")

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="PPTX Layout & Copy QA Validator"
    )
    parser.add_argument("pptx", help="Path to .pptx file")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Include INFO-level findings"
    )
    parser.add_argument("--checks", help="Comma-separated subset: " + ",".join(CHECKS))
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.exists():
        print(f"Error: {pptx_path} not found", file=sys.stderr)
        sys.exit(2)

    try:
        issues, prs = validate(
            str(pptx_path),
            strict=args.strict,
            checks=args.checks.split(",") if args.checks else None,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        out = {
            "file": str(pptx_path),
            "slides": len(prs.slides),
            "slide_width_in": emu_to_in(prs.slide_width),
            "slide_height_in": emu_to_in(prs.slide_height),
            "issues": [i.to_dict() for i in issues],
            "summary": {
                "total": len(issues),
                "critical": sum(1 for i in issues if i.level == "critical"),
                "warning": sum(1 for i in issues if i.level == "warning"),
                "info": sum(1 for i in issues if i.level == "info"),
            },
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(format_report(issues, prs, pptx_path))

    has_critical = any(i.level == "critical" for i in issues)
    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
