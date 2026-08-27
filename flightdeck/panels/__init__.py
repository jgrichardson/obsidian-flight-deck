"""Panel registry. To add a panel: write a module with a Panel subclass and
register it here by NAME. Enable in flightdeck.toml with [[panels]] name="...".
Panels requiring OAuth (calendar/email/slack) ship as separate optional modules;
see docs/PANELS.md."""
from .github_prs import GithubPRs
from .status import Status
from .embed import Embed
from .waiting_on import WaitingOn

REGISTRY = {
    GithubPRs.NAME: GithubPRs,
    Status.NAME: Status,
    Embed.NAME: Embed,
    WaitingOn.NAME: WaitingOn,
}

# Optional OAuth panels — imported lazily so a missing setup never breaks core.
def load_optional():
    try:
        from .google_panels import CalendarPanel, EmailPanel
        REGISTRY[CalendarPanel.NAME] = CalendarPanel
        REGISTRY[EmailPanel.NAME] = EmailPanel
    except Exception:
        pass
    try:
        from .slack_drafts import SlackDrafts
        REGISTRY[SlackDrafts.NAME] = SlackDrafts
    except Exception:
        pass
