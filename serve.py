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


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """Same as the default handler, but tells the browser never to cache
    anything — otherwise, after you regenerate index.html or the data
    files, your browser can keep showing an old cached copy even though
    the files on disk have changed."""
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    with socketserver.TCPServer(("", PORT), NoCacheHandler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"Serving at {url}  (Ctrl+C to stop)")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()


if __name__ == "__main__":
    main()
