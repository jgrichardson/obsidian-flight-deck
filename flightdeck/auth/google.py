"""Google auth (Calendar + Gmail, read-only) via loopback OAuth.
You provide an OAuth client (Desktop app) once; this stores a refresh token.
See docs/AUTH.md for the 5-minute Google Cloud setup (Internal consent = no verification)."""
from __future__ import annotations
import http.server, json, os, threading, time, urllib.parse, urllib.request, webbrowser
from .. import creds

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly",
          "https://www.googleapis.com/auth/gmail.readonly"]
PORT = 8731

def setup():
    cid = input("Google OAuth client_id (Desktop app): ").strip()
    csec = input("Google OAuth client_secret: ").strip()
    if not cid or not csec:
        print("Skipped."); return
    redirect = f"http://localhost:{PORT}/"
    holder = {}
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            holder.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200); self.end_headers()
            self.wfile.write(b"<h2>Flight Deck: Google connected. Close this tab.</h2>")
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("localhost", PORT), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent"})
    print("Opening browser for consent…"); webbrowser.open(url)
    for _ in range(180):
        if "code" in holder: break
        time.sleep(1)
    if "code" not in holder:
        print("Timed out."); return
    data = urllib.parse.urlencode({"code": holder["code"][0], "client_id": cid, "client_secret": csec,
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    r = json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data, timeout=25).read())
    if "refresh_token" not in r:
        print("No refresh token — revoke prior access and retry."); return
    creds.set_secret("google", json.dumps({"client_id": cid, "client_secret": csec,
                                            "refresh_token": r["refresh_token"]}))
    print("Stored Google credentials (read-only Calendar + Gmail).")
