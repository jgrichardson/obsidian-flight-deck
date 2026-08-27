"""Calendar + Email panels (Google, read-only). Requires `flightdeck setup google`.
Options:
  [[panels]] name="calendar"
  [[panels]] name="email"
    address = "you@example.com"      # your address, for to:me matching (optional)
Both are omitted automatically if Google isn't set up."""
from __future__ import annotations
import datetime, json, urllib.parse, urllib.request
from .base import Panel
from .. import creds

def _token():
    raw = creds.get_secret("google")
    if not raw:
        return None
    c = json.loads(raw)
    data = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
                                   "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
    try:
        return json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data, timeout=20).read())["access_token"]
    except Exception:
        return None

def _get(url, at):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {at}"}), timeout=20).read())

class CalendarPanel(Panel):
    NAME = "calendar"; CALLOUT = "calendar"; TITLE = "Calendar — today"
    def render(self):
        at = _token()
        if not at:
            return None
        now = self.ctx.now
        tmin = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        tmax = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        q = urllib.parse.urlencode({"timeMin": tmin, "timeMax": tmax, "singleEvents": "true", "orderBy": "startTime"})
        try:
            ev = _get(f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{q}", at)
        except Exception:
            return None
        L = []
        for e in ev.get("items", []):
            me = next((a for a in e.get("attendees", []) if a.get("self")), None)
            if me and me.get("responseStatus") == "declined":
                continue
            st = e.get("start", {}); when = st.get("dateTime") or st.get("date") or ""
            hm = when[11:16] if "T" in when else "all-day"
            link = e.get("htmlLink", "")
            summ = e.get("summary", "(no title)")
            lbl = f"[{summ}]({link})" if link else summ
            L.append(f"- **{hm}** {lbl}")
            if me and me.get("responseStatus") == "needsAction":
                L.append(f"- ✉️ **invite to respond** — {summ} ({hm})")
        return L or ["- no events today"]

class EmailPanel(Panel):
    NAME = "email"; CALLOUT = "mail"; TITLE = "Email — needs you"
    def render(self):
        at = _token()
        if not at:
            return None
        def collect(q, cap):
            out = []
            try:
                lst = _get("https://gmail.googleapis.com/gmail/v1/users/me/messages?" +
                           urllib.parse.urlencode({"q": q, "maxResults": str(cap * 3)}), at)
            except Exception:
                return []
            for m in lst.get("messages", []):
                if len(out) >= cap:
                    break
                try:
                    d = _get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{m['id']}"
                             "?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=List-Unsubscribe", at)
                except Exception:
                    continue
                h = {x["name"]: x["value"] for x in d.get("payload", {}).get("headers", [])}
                if h.get("List-Unsubscribe"):          # skip newsletters/bulk
                    continue
                frm = __import__("re").sub(r"\s*<[^>]+>", "", h.get("From", "?")).strip('"')
                out.append(f"- {frm} — {h.get('Subject','(no subject)')[:70]}")
            return out
        direct = collect("is:unread in:inbox to:me newer_than:7d", 8)
        return direct or ["- inbox clear"]
