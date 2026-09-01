#!/usr/bin/env python3
"""Tests for the client-friendly handoff zip layout.

The curated handoff zip presents a non-technical client with ONE file to click
(the client website, renamed "OPEN ME.html") and a single "Supporting Files"
folder holding every other page. Moving the website to the top level while the
rest nests breaks the flat sibling links the generators emit, so the builder
rewrites them per file. These tests lock down that rewriting and the resulting
zip structure.

Run: python3 tests/test_handoff_layout.py
"""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import generate  # noqa: E402

ENTRY = generate.HANDOFF_ENTRY_NAME       # "OPEN ME.html"
SUP = generate.HANDOFF_SUPPORT_DIR        # "Supporting Files"

# target_map mirrors what build_curated_handoff_zip builds.
TARGET_MAP = {
    "1-client-website.html": ENTRY,
    "2-process-map.html": f"{SUP}/2-process-map.html",
    "3-findings.html": f"{SUP}/3-findings.html",
    "4-waste.html": f"{SUP}/4-waste.html",
    "5-blueprint.html": f"{SUP}/5-blueprint.html",
}

_failures = []


def check(cond, msg):
    if cond:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        _failures.append(msg)


# --------------------------------------------------------------------------- #
# Unit: _rewrite_handoff_links per page location
# --------------------------------------------------------------------------- #
def test_rewrite_website_root():
    print("\n_rewrite_handoff_links — client website at bundle root (OPEN ME.html)")
    html = (
        '<a href="#zone-sales">Sales</a>'                       # in-page anchor: must NOT change
        '<a href="2-process-map.html">map</a>'
        '<a href="3-findings.html" target="_blank">find</a>'
        '<a href="4-waste.html">waste</a>'
        '<a href="5-blueprint.html">bp</a>'
        'var items = [{"file": "2-process-map.html", "label": "x"}, '
        '{"file": "5-blueprint.html", "label": "y"}];'
    )
    out = generate._rewrite_handoff_links(html, ENTRY, TARGET_MAP)
    check('href="#zone-sales"' in out, "in-page #anchor left untouched")
    check(f'href="{SUP.replace(" ", "%20")}/2-process-map.html"' in out,
          "static href -> Supporting%20Files/2-process-map.html")
    check(f'href="{SUP.replace(" ", "%20")}/5-blueprint.html"' in out,
          "static href -> Supporting%20Files/5-blueprint.html")
    check(f'"file": "{SUP.replace(" ", "%20")}/2-process-map.html"' in out,
          "downloads JSON file -> Supporting%20Files/2-process-map.html")
    check('href="2-process-map.html"' not in out and 'href="3-findings.html"' not in out,
          "no bare (unprefixed) section hrefs remain")


def test_rewrite_section_page():
    print("\n_rewrite_handoff_links — section page at Supporting Files/ (depth 1)")
    html = (
        '<a href="1-client-website.html"><img src="logo"></a>'  # back to portal
        '<a href="1-client-website.html">Portal</a>'
        '<a href="4-waste.html">sibling</a>'                    # sibling: stays relative
        '<a href="processes/sales/index.html">stage</a>'        # into processes: stays
    )
    out = generate._rewrite_handoff_links(html, f"{SUP}/5-blueprint.html", TARGET_MAP)
    check('href="../OPEN%20ME.html"' in out, "back-link 1-client-website -> ../OPEN%20ME.html")
    check('href="4-waste.html"' in out, "sibling section link unchanged")
    check('href="processes/sales/index.html"' in out, "processes/ link untouched")
    check("1-client-website.html" not in out, "no 1-client-website.html reference left")


def test_rewrite_process_subpage():
    print("\n_rewrite_handoff_links — BPMN sub-page at Supporting Files/processes/{stage}/ (depth 3)")
    html = (
        '<a href="../../1-client-website.html"><img src="../../assets/logo.png"></a>'
        '<a href="../../1-client-website.html">Portal</a>'
        '<a href="../../2-process-map.html">Landscape</a>'
        '<a href="index.html">this stage</a>'
        '<link href="../../assets/bpmn-viewer.css">'
        '<script src="../../assets/bpmn-viewer.min.js"></script>'
    )
    out = generate._rewrite_handoff_links(html, f"{SUP}/processes/sales/index.html", TARGET_MAP)
    check('href="../../../OPEN%20ME.html"' in out,
          "depth-3 back-link ../../1-client-website -> ../../../OPEN%20ME.html")
    check('href="../../2-process-map.html"' in out,
          "breadcrumb to landscape unchanged (both inside Supporting Files)")
    check('src="../../assets/bpmn-viewer.min.js"' in out, "assets/ refs untouched")
    check('href="index.html"' in out, "self-relative link untouched")
    check("1-client-website.html" not in out, "no 1-client-website.html reference left")


# --------------------------------------------------------------------------- #
# Integration: build_curated_handoff_zip end-to-end
# --------------------------------------------------------------------------- #
def _write_synthetic_deliverables(out_dir: Path):
    (out_dir / "1-client-website.html").write_text(
        '<!DOCTYPE html><html><body>'
        '<a href="#zone-sales">Sales</a>'
        '<a href="2-process-map.html" class="btn-pm">Open Process Map</a>'
        '<a href="3-findings.html" target="_blank">findings</a>'
        '<a href="4-waste.html" target="_blank">waste</a>'
        '<a href="5-blueprint.html" target="_blank">blueprint</a>'
        '<script>var items = [{"file": "2-process-map.html", "label": "How You Work"}, '
        '{"file": "3-findings.html", "label": "What We Found"}];</script>'
        '</body></html>', encoding="utf-8")
    (out_dir / "2-process-map.html").write_text(
        '<div class="topbar"><a href="1-client-website.html"><img src="l"></a>'
        '<a href="1-client-website.html">Portal</a></div>'
        '<a href="processes/sales/index.html">Sales stage</a>', encoding="utf-8")
    for f in ("3-findings.html", "4-waste.html"):
        (out_dir / f).write_text('<a href="1-client-website.html">Audit overview</a>', encoding="utf-8")
    (out_dir / "5-blueprint.html").write_text(
        '<a href="1-client-website.html">Portal</a>'
        '<a href="4-waste.html">See the full opportunity breakdown</a>', encoding="utf-8")
    assets = out_dir / "assets"
    assets.mkdir()
    (assets / "bpmn-viewer.min.js").write_text("// viewer", encoding="utf-8")
    (assets / "bpmn-viewer.css").write_text("/* viewer */", encoding="utf-8")
    stage = out_dir / "processes" / "sales"
    stage.mkdir(parents=True)
    (stage / "index.html").write_text(
        '<a href="../../1-client-website.html"><img src="../../assets/logo.png"></a>'
        '<a href="../../1-client-website.html">Portal</a>'
        '<a href="../../2-process-map.html">Landscape</a>'
        '<a href="index.html">Sales</a>'
        '<link href="../../assets/bpmn-viewer.css">'
        '<script src="../../assets/bpmn-viewer.min.js"></script>', encoding="utf-8")
    (stage / "lead.bpmn").write_text("<bpmn/>", encoding="utf-8")


def test_build_zip_structure():
    print("\nbuild_curated_handoff_zip — full bundle structure & links")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        out_dir = td / "deliverables"
        out_dir.mkdir()
        _write_synthetic_deliverables(out_dir)

        # Redirect the handoff output dir into the temp tree.
        handoff_root = td / "handoff"
        generate._get_client_subdir = lambda slug, name: handoff_root  # noqa: ARG005

        zip_path = generate.build_curated_handoff_zip(
            {"company_name": "Test Co"}, out_dir, "test-co")
        check(zip_path.exists(), f"zip created at {zip_path}")
        check(zip_path.parent.name == "v1", "written into versioned dir v1")

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            root = "Test Co - APG Audit"

            # Exactly ONE file at the bundle top level, and it's the entry point.
            top_level_files = [
                n for n in names
                if n.startswith(f"{root}/") and "/" not in n[len(root) + 1:] and not n.endswith("/")
            ]
            check(top_level_files == [f"{root}/{ENTRY}"],
                  f"exactly one top-level file: {ENTRY} (got {[t.split('/')[-1] for t in top_level_files]})")

            check(f"{root}/{SUP}/2-process-map.html" in names, "process map nested under Supporting Files")
            check(f"{root}/{SUP}/5-blueprint.html" in names, "blueprint nested under Supporting Files")
            check(f"{root}/{SUP}/assets/bpmn-viewer.min.js" in names, "assets nested under Supporting Files")
            check(f"{root}/{SUP}/processes/sales/index.html" in names, "process subpage nested")
            check(f"{root}/{SUP}/processes/sales/lead.bpmn" in names, ".bpmn copied verbatim")
            check("How to View Your Audit.html" not in " ".join(names), "no separate instructions page")

            entry = zf.read(f"{root}/{ENTRY}").decode("utf-8")
            check('href="#zone-sales"' in entry, "[entry] in-page anchor preserved")
            check('href="Supporting%20Files/2-process-map.html"' in entry, "[entry] static link prefixed")
            check('"file": "Supporting%20Files/3-findings.html"' in entry, "[entry] downloads JSON prefixed")
            check('href="2-process-map.html"' not in entry, "[entry] no bare section href remains")

            bp = zf.read(f"{root}/{SUP}/5-blueprint.html").decode("utf-8")
            check('href="../OPEN%20ME.html"' in bp, "[blueprint] back-link -> ../OPEN%20ME.html")
            check('href="4-waste.html"' in bp, "[blueprint] sibling link unchanged")

            sub = zf.read(f"{root}/{SUP}/processes/sales/index.html").decode("utf-8")
            check('href="../../../OPEN%20ME.html"' in sub, "[subpage] back-link -> ../../../OPEN%20ME.html")
            check('href="../../2-process-map.html"' in sub, "[subpage] landscape breadcrumb unchanged")
            check('src="../../assets/bpmn-viewer.min.js"' in sub, "[subpage] asset ref unchanged")

            # No page anywhere should still point at the old website filename.
            leftover = [n for n in names if n.endswith(".html")
                        and "1-client-website.html" in zf.read(n).decode("utf-8")]
            check(not leftover, f"no 1-client-website.html links remain (offenders: {leftover})")


if __name__ == "__main__":
    test_rewrite_website_root()
    test_rewrite_section_page()
    test_rewrite_process_subpage()
    test_build_zip_structure()
    print()
    if _failures:
        print(f"FAILED: {len(_failures)} check(s)")
        sys.exit(1)
    print("ALL HANDOFF LAYOUT TESTS PASSED")
