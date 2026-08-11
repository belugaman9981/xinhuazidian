"""
serve.py — quick local server for the 检字表 site.

Browsers block fetch() of local files opened via file://, so once you've
generated jianzi_data.json with build_unihan_data.py, run this script to
view the site with the full dataset:

    python serve.py

Then open the printed URL (http://localhost:8000) in your browser.
Run this from inside the project folder (same folder as index.html).
"""
import http.server
import socketserver
import webbrowser

PORT = 8000


def main():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"Serving at {url}  (Ctrl+C to stop)")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()


if __name__ == "__main__":
    main()
