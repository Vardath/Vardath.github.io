"""Stage 1: audit interiors and cover source; no inferred print geometry.
Requires PyMuPDF and Pillow. Supply paperback, hardcover, artwork and output directory.
"""
import argparse, hashlib, json, re
from pathlib import Path
import fitz
from PIL import Image

def sha(data):
    return hashlib.sha256(data).hexdigest()

def interior(path):
    doc = fitz.open(path)
    raw = []
    sizes = set()
    for page in doc:
        sizes.add(tuple(round(x / 72, 6) for x in (page.rect.width, page.rect.height)))
        raw.append(re.sub(r"^\d+\s*\n", "", page.get_text()))
    text = "".join(raw)
    # Contents and index references legitimately differ between layouts.
    text = re.sub(r"·\s*\d+", "", text)
    text = re.sub(r"\bpp?\.\s*\d+(?:\s*[–-]\s*\d+)?", "PAGE_REF", text)
    text = re.sub(r"\s+", "", text)
    last = doc[-1]
    # Conservative: text, vector drawing or image counts as content.
    occupied = bool(last.get_text().strip() or last.get_images() or last.get_drawings())
    pages = len(doc)
    production = pages + (1 if pages % 2 else (2 if occupied else 0))
    return {
        "file_sha256": sha(Path(path).read_bytes()),
        "pdf_pages": pages,
        "trim_sizes_inches": sorted(sizes),
        "last_page_has_content": occupied,
        "expected_production_pages": production,
        "normalized_text_sha256": sha(text.encode()),
        "normalized_text_characters": len(text),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paperback", required=True)
    parser.add_argument("--hardcover", required=True)
    parser.add_argument("--artwork", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {n: interior(getattr(args, n)) for n in ("paperback", "hardcover")}
    report["text_matches_ignoring_layout_references"] = (
        report["paperback"]["normalized_text_sha256"] ==
        report["hardcover"]["normalized_text_sha256"])
    im = Image.open(args.artwork)
    report["artwork"] = {
        "pixels": im.size,
        "sha256": sha(Path(args.artwork).read_bytes()),
        "note": "1536x909 supplied wrap. Original text/detail is about 91 pixels per vertical printed inch at 10 inches high; upsampling cannot recover original detail.",
    }
    report["status"] = "WAITING_FOR_OFFICIAL_EDITION_TEMPLATES"
    report["required_inputs"] = [
        "Paperback and hardcover ISBNs",
        "Email for official template delivery",
        "Confirm B&W 50lb white paper and case laminate hardcover",
        "Official template PDF for each edition, including measured panel/spine/barcode bounds",
    ]
    (out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["text_matches_ignoring_layout_references"]:
        raise SystemExit("Interior content mismatch: investigate before cover layout.")

if __name__ == "__main__":
    main()
