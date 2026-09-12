#!/usr/bin/env python3
"""Regression tests for qa_validate's structural checks.

Scope: the two exemptions added when the native cover wash and the System
Boundary pattern were absorbed. Both exemptions exist because the checks were
reporting correct decks as defective, which is worse than a missed finding:
a gate that fails valid work teaches builders to ignore it.

  1. check_bounds exempts a cover-wash ellipse (unstroked, solid fill at or
     below WASH_MAX_ALPHA) that bleeds off the stage. The bleed is required by
     SKILL.md > Decoration Discipline. Above the alpha ceiling the same shape
     is the banned decorative orb and must still report critical, so these
     tests pin BOTH sides of the threshold.

  2. check_zero_size exempts a LINE with exactly one zero dimension, which is
     how a rule is drawn. A degenerate line and any non-line shape with a zero
     dimension must still be reported.

Run: python3 scripts/test_qa_checks.py
Needs python-pptx. No network, no node, no rendering.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

import pptx_qa_check as qa

A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _new_prs():
    prs = Presentation()
    prs.slide_width = Inches(13.3333)
    prs.slide_height = Inches(7.5)
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set_alpha_fill(shape, hexcol, alpha_thousandths):
    """Replace the shape's fill with a solid colour at the given OOXML alpha."""
    spPr = shape._element.spPr
    for tag in ("solidFill", "gradFill", "noFill", "blipFill", "pattFill"):
        el = spPr.find(f"{{{A}}}{tag}")
        if el is not None:
            spPr.remove(el)
    sf = etree.SubElement(spPr, f"{{{A}}}solidFill")
    clr = etree.SubElement(sf, f"{{{A}}}srgbClr")
    clr.set("val", hexcol)
    if alpha_thousandths is not None:
        a = etree.SubElement(clr, f"{{{A}}}alpha")
        a.set("val", str(int(alpha_thousandths)))
    # Keep <a:ln> last, matching what PptxGenJS emits.
    ln = spPr.find(f"{{{A}}}ln")
    if ln is not None:
        spPr.remove(ln)
        spPr.append(ln)


def _empty_ln(shape):
    """PptxGenJS writes `line: {type:"none"}` as an EMPTY <a:ln></a:ln>, not as
    <a:ln><a:noFill/></a:ln>. Reproduce that exactly: the detector has to treat
    an empty ln as no stroke, and this is the form real decks contain."""
    spPr = shape._element.spPr
    ln = spPr.find(f"{{{A}}}ln")
    if ln is None:
        ln = etree.SubElement(spPr, f"{{{A}}}ln")
    for child in list(ln):
        ln.remove(child)


def _stroke(shape, hexcol="22D3EE"):
    spPr = shape._element.spPr
    ln = spPr.find(f"{{{A}}}ln")
    if ln is None:
        ln = etree.SubElement(spPr, f"{{{A}}}ln")
    for child in list(ln):
        ln.remove(child)
    sf = etree.SubElement(ln, f"{{{A}}}solidFill")
    clr = etree.SubElement(sf, f"{{{A}}}srgbClr")
    clr.set("val", hexcol)


def _wash(slide, alpha, *, stroked=False, contained=False):
    """A cover-wash ellipse bleeding off the top-right corner by default."""
    x, y = (Inches(4.0), Inches(2.0)) if contained else (Inches(9.2), Inches(-1.5))
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, Inches(5.4), Inches(5.4))
    sh.shadow.inherit = False
    _set_alpha_fill(sh, "7B61FF", alpha)
    if stroked:
        _stroke(sh)
    else:
        _empty_ln(sh)
    return sh


def _bounds(prs):
    return qa.check_bounds(prs)


def _zeros(prs):
    return qa.check_zero_size(prs)


class TestCoverWashExemption(unittest.TestCase):
    def test_sanctioned_wash_is_not_a_bounds_defect(self):
        prs = _new_prs()
        _wash(_blank(prs), 16000)
        self.assertEqual(_bounds(prs), [], "16% wash bleeding off-stage must be silent")

    def test_secondary_wash_alpha_also_exempt(self):
        prs = _new_prs()
        _wash(_blank(prs), 10000)
        self.assertEqual(_bounds(prs), [])

    def test_ceiling_is_inclusive(self):
        prs = _new_prs()
        _wash(_blank(prs), qa.WASH_MAX_ALPHA)
        self.assertEqual(_bounds(prs), [], "exactly 20% is still a wash")

    def test_one_thousandth_above_the_ceiling_is_critical(self):
        """The threshold has to bite, or the exemption is a hole in the check."""
        prs = _new_prs()
        _wash(_blank(prs), qa.WASH_MAX_ALPHA + 1000)
        found = _bounds(prs)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].level, "critical")

    def test_opaque_orb_off_stage_is_critical(self):
        prs = _new_prs()
        _wash(_blank(prs), 40000)
        self.assertEqual(len(_bounds(prs)), 1)

    def test_fill_with_no_alpha_element_is_critical(self):
        """No <a:alpha> means fully opaque, which is the banned orb."""
        prs = _new_prs()
        _wash(_blank(prs), None)
        self.assertEqual(len(_bounds(prs)), 1)

    def test_stroked_low_alpha_ellipse_is_not_a_wash(self):
        """A visible outline makes it a diagram ring, not atmosphere, and a
        ring hanging off the stage edge is a real layout defect."""
        prs = _new_prs()
        _wash(_blank(prs), 16000, stroked=True)
        self.assertEqual(len(_bounds(prs)), 1)

    def test_non_ellipse_low_alpha_shape_off_stage_is_critical(self):
        prs = _new_prs()
        sh = _blank(prs).shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.2), Inches(-1.5), Inches(5.4), Inches(5.4)
        )
        sh.shadow.inherit = False
        _set_alpha_fill(sh, "7B61FF", 16000)
        _empty_ln(sh)
        self.assertEqual(len(_bounds(prs)), 1)

    def test_contained_wash_reports_nothing_because_it_is_in_bounds(self):
        """Documented limit: check_bounds only ever speaks about overflow, so a
        fully contained ellipse is outside its remit even though the rule wants
        the bleed. The visual QA pass owns that half."""
        prs = _new_prs()
        _wash(_blank(prs), 16000, contained=True)
        self.assertEqual(_bounds(prs), [])

    def test_ordinary_overflowing_shape_still_critical(self):
        """Guard against the exemption widening into a general amnesty."""
        prs = _new_prs()
        sh = _blank(prs).shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.0), Inches(3.0), Inches(4.0), Inches(2.0)
        )
        sh.shadow.inherit = False
        found = _bounds(prs)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].level, "critical")


class TestRuleLineExemption(unittest.TestCase):
    def _line(self, slide, w, h):
        sh = slide.shapes.add_shape(MSO_SHAPE.LINE_INVERSE, Inches(1), Inches(1), w, h)
        sh.shadow.inherit = False
        # python-pptx has no LINE preset, so set prstGeom directly to the same
        # value PptxGenJS writes for pres.shapes.LINE.
        geom = sh._element.spPr.find(f"{{{A}}}prstGeom")
        geom.set("prst", "line")
        return sh

    def test_horizontal_rule_is_exempt(self):
        prs = _new_prs()
        self._line(_blank(prs), Inches(11.7), 0)
        self.assertEqual(_zeros(prs), [])

    def test_vertical_rule_is_exempt(self):
        prs = _new_prs()
        self._line(_blank(prs), 0, Inches(4.8))
        self.assertEqual(_zeros(prs), [])

    def test_degenerate_line_still_reported(self):
        prs = _new_prs()
        self._line(_blank(prs), 0, 0)
        self.assertEqual(len(_zeros(prs)), 1)

    def test_non_line_zero_height_still_reported(self):
        prs = _new_prs()
        sh = _blank(prs).shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(3), 0
        )
        sh.shadow.inherit = False
        self.assertEqual(len(_zeros(prs)), 1)

    def test_non_line_zero_width_still_reported(self):
        prs = _new_prs()
        sh = _blank(prs).shapes.add_shape(MSO_SHAPE.OVAL, Inches(1), Inches(1), 0, Inches(2))
        sh.shadow.inherit = False
        self.assertEqual(len(_zeros(prs)), 1)


class TestHelpers(unittest.TestCase):
    def test_empty_ln_counts_as_no_stroke(self):
        """This is the form PptxGenJS actually emits for line:{type:"none"}.
        Reading it as a stroke would break every wash in every real deck."""
        prs = _new_prs()
        sh = _wash(_blank(prs), 16000)
        self.assertFalse(qa._has_stroke(sh))

    def test_solid_fill_alpha_defaults_to_opaque(self):
        prs = _new_prs()
        sh = _wash(_blank(prs), None)
        self.assertEqual(qa._solid_fill_alpha(sh), 100000)

    def test_geom_reads_the_preset_name(self):
        prs = _new_prs()
        sh = _wash(_blank(prs), 16000)
        self.assertEqual(qa._shape_geom(sh), "ellipse")


class ChecksFilterTests(unittest.TestCase):
    def test_checks_filter_limits_run(self) -> None:
        import tempfile
        prs = _new_prs()
        s = prs.slides.add_slide(prs.slide_layouts[6])
        tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1))
        tb.text_frame.text = "제목 — 부제"          # em dash: copy critical
        tb.text_frame.paragraphs[0].runs[0].font.size = Pt(10)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.pptx"
            prs.save(path)
            only_copy, _ = qa.validate(str(path), checks=["copy"])
            only_bounds, _ = qa.validate(str(path), checks=["bounds"])
        self.assertTrue(any(i.check == "ai_copy" for i in only_copy))
        self.assertFalse(any(i.check == "ai_copy" for i in only_bounds))


if __name__ == "__main__":
    unittest.main(verbosity=2)
