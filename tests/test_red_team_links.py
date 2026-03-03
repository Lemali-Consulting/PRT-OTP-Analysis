"""Checks for red-team report link targets used by analysis review history."""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"
RED_TEAM_DIR = PROJECT_ROOT / "RED-TEAM-REPORTS"
WEBSITE_RED_TEAM_DIR = PROJECT_ROOT / "products" / "website" / "output" / "RED-TEAM-REPORTS"

RED_TEAM_LINK_RE = re.compile(r"\(\.\./\.\./RED-TEAM-REPORTS/([^)]+\.md)\)")


def test_review_history_links_target_existing_repo_files():
    """Every red-team link in analysis findings should target a real report file."""
    links: set[str] = set()
    for findings in ANALYSES_DIR.glob("*/FINDINGS.md"):
        text = findings.read_text(encoding="utf-8")
        for match in RED_TEAM_LINK_RE.findall(text):
            links.add(match)
    assert links, "No red-team links found in analysis FINDINGS.md files"
    missing = [name for name in sorted(links) if not (RED_TEAM_DIR / name).exists()]
    assert not missing, "Missing red-team report files:\n" + "\n".join(missing)


def test_red_team_reports_are_published_to_static_output():
    """Static site output should include red-team reports for direct link access."""
    assert WEBSITE_RED_TEAM_DIR.exists(), "products/website/output/RED-TEAM-REPORTS is missing"
    md_files = sorted(WEBSITE_RED_TEAM_DIR.glob("*.md"))
    assert md_files, "No red-team markdown files published to website output"
