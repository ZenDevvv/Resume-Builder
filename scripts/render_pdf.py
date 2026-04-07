import argparse
import contextlib
import functools
import http.server
import socketserver
import subprocess
import threading
from pathlib import Path


BROWSER_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def find_browser():
    for candidate in BROWSER_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find Edge or Chrome for headless PDF rendering.")


@contextlib.contextmanager
def serve_directory(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield httpd.server_address[1]
        finally:
            httpd.shutdown()
            thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description="Render a local HTML resume to PDF via headless browser.")
    parser.add_argument("--html", required=True, help="Path to the source HTML file.")
    parser.add_argument("--pdf", required=True, help="Path to the destination PDF file.")
    parser.add_argument("--timeout", type=int, default=60, help="Render timeout in seconds.")
    args = parser.parse_args()

    html_path = Path(args.html).resolve()
    pdf_path = Path(args.pdf).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    browser = find_browser()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with serve_directory(html_path.parent) as port:
        url = f"http://127.0.0.1:{port}/{html_path.name}"
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=4000",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            url,
        ]
        subprocess.run(command, check=True, timeout=args.timeout)

    print(f"Wrote PDF to {pdf_path}")


if __name__ == "__main__":
    main()
