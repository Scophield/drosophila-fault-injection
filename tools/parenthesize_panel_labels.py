"""Add only vector parentheses to approved panel labels; never redraw figures.

The original content streams, images, dimensions and label glyphs are preserved.
This is a presentation-only derivative, not a new analysis or plotting run.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pymupdf as fitz
from fontTools import subset
from fontTools.ttLib import TTFont
from matplotlib.font_manager import FontProperties, findfont


FIGURES = {
    "evidence_v10_overview.pdf": "abcd",
    "v10f_reuse.pdf": "abc",
    "v10h_rf.pdf": "abcd",
    "v10f_warning.pdf": "ab",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--font-file", type=Path, help="Arial Bold TTF matching the approved labels")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.out.mkdir(parents=True, exist_ok=False)
    # The approved PDFs use a glyph-index subset, not a Unicode-reusable TTF.
    # Embed only two glyphs from the matching installed Arial Bold family.
    font_path = args.font_file or Path(findfont(
        FontProperties(family="Arial", weight="bold"), fallback_to_default=False))
    original_font = font_path.read_bytes()
    font = TTFont(io.BytesIO(original_font))
    sub = subset.Subsetter()
    sub.populate(text="()")
    sub.subset(font)
    buffer = io.BytesIO()
    font.save(buffer)
    font_bytes = buffer.getvalue()
    metrics = fitz.Font(fontbuffer=font_bytes)
    assert all(metrics.has_glyph(ord(c)) for c in "()")
    report = []
    scale = 600 / 72
    for name, letters in FIGURES.items():
        source = root / "paper/figs" / name
        data = source.read_bytes()
        doc = fitz.open(stream=data, filetype="pdf")
        page = doc[0]
        original_contents = [doc.xref_stream(x) for x in page.get_contents()]
        original_images = [sha(doc.xref_stream(f[0])) for f in page.get_images()]
        before = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        before = np.frombuffer(before.samples, np.uint8).reshape(before.height, before.width, 3)
        labels = []
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = "".join(c["c"] for c in span["chars"])
                    if (span["flags"] & 16 and span["size"] >= 8.4
                            and (text in letters or text[:2] in [c + " " for c in letters])):
                        labels.append((text[0], span, span["chars"][0]))
        assert "".join(q[0] for q in labels) == letters, (name, labels)
        page.insert_font(fontname="PanelParentheses", fontbuffer=font_bytes)
        rectangles = []
        for letter, span, char in labels:
            size = span["size"]
            x, y = char["origin"]
            width = metrics.text_length("(", fontsize=size)
            # At the left edge, use the available white margin; no cropping.
            positions = [("(", max(0, x-width)), (")", char["bbox"][2])]
            rgb = tuple(((span["color"] >> b) & 255) / 255 for b in (16, 8, 0))
            for glyph, xx in positions:
                page.insert_text((xx, y), glyph, fontname="PanelParentheses",
                                 fontsize=size, color=rgb, overlay=True)
                rectangles.append(fitz.Rect(xx, y-size*metrics.ascender,
                                           xx+width, y-size*metrics.descender))
        # Original streams and image payloads must be byte-identical.
        current_contents = [doc.xref_stream(x) for x in page.get_contents()]
        assert all(stream in current_contents for stream in original_contents)
        assert [sha(doc.xref_stream(f[0])) for f in page.get_images()] == original_images
        target = args.out / (source.stem + "_parenthesized.pdf")
        doc.save(target, deflate=True)
        with fitz.open(target) as checked:
            assert checked[0].rect == page.rect
            saved_contents = [checked.xref_stream(x) for x in checked[0].get_contents()]
            assert all(stream in saved_contents for stream in original_contents)
            assert [sha(checked.xref_stream(f[0])) for f in checked[0].get_images()] == original_images
            pix = checked[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            after = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
            changed = np.any(before != after, axis=2)
            allowed = np.zeros(changed.shape, dtype=bool)
            for rect in rectangles:
                rect = (rect + (-0.5, -0.5, 0.5, 0.5)) * scale
                allowed[max(0, int(rect.y0)):int(np.ceil(rect.y1)),
                        max(0, int(rect.x0)):int(np.ceil(rect.x1))] = True
            assert not np.any(changed & ~allowed), name
            checked[0].get_pixmap(dpi=150).save(args.out / (source.stem + "_preview.png"))
        assert sha(source.read_bytes()) == sha(data)
        report.append(dict(source=str(source.relative_to(root)), source_sha256=sha(data),
                           derivative=target.name, derivative_sha256=sha(target.read_bytes()),
                           labels=list(letters), original_streams_unchanged=True,
                           original_image_payloads_unchanged=True,
                           pixels_outside_parentheses_unchanged_at_dpi=600))
    result = dict(passed=True, scope="Only panel-label parentheses; no redraw or data processing",
                  figures=report, source_sha256=sha(Path(__file__).read_bytes()))
    (args.out / "check.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
