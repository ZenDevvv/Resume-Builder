import argparse
import json
from pathlib import Path

from pypdf import PdfReader


def extract_links(page):
    links = []
    annotations = page.get("/Annots")
    if not annotations:
        return links

    for annotation in annotations:
        obj = annotation.get_object()
        action = obj.get("/A")
        uri = action.get("/URI") if action else None
        if uri:
            links.append(
                {
                    "uri": str(uri),
                    "rect": [float(value) for value in obj.get("/Rect", [])],
                }
            )
    return links


def main():
    parser = argparse.ArgumentParser(description="Extract text and links from a resume PDF.")
    parser.add_argument("--input", required=True, help="Path to the source PDF.")
    parser.add_argument("--output", required=True, help="Path to the JSON output.")
    args = parser.parse_args()

    pdf_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    pages = []

    for index, page in enumerate(reader.pages, start=1):
        pages.append(
            {
                "page_number": index,
                "text": page.extract_text() or "",
                "links": extract_links(page),
            }
        )

    payload = {
        "source_pdf": str(pdf_path),
        "page_count": len(reader.pages),
        "pages": pages,
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote extraction to {output_path}")


if __name__ == "__main__":
    main()
