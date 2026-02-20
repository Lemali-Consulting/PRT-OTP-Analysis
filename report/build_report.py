"""Build a self-contained HTML report from all 35 PRT OTP analyses."""

import base64
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSES_DIR = PROJECT_ROOT / "analyses"
FINDINGS_PATH = PROJECT_ROOT / "FINDINGS.md"
APPENDIX_PATH = PROJECT_ROOT / "docs" / "ADDITIONAL_DATA_REQUESTS.md"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Static registry: (dir_name, title, [png_files])
ANALYSIS_REGISTRY = [
    ("01_system_trend", "System-Wide Trend", ["system_trend.png"]),
    ("02_mode_comparison", "Mode Comparison", ["mode_comparison.png"]),
    ("03_route_ranking", "Route Ranking", ["top_bottom_routes.png"]),
    ("04_neighborhood_equity", "Neighborhood Equity", ["neighborhood_equity.png", "weighted_vs_unweighted_otp.png"]),
    ("05_anomaly_investigation", "Anomaly Investigation", ["anomaly_profiles.png"]),
    ("06_seasonal_patterns", "Seasonal Patterns", ["seasonal_patterns.png"]),
    ("07_stop_count_vs_otp", "Stop Count vs OTP", ["stop_count_vs_otp.png"]),
    ("08_hotspot_map", "Hot-Spot Map", ["hotspot_map.png"]),
    ("09_incline_investigation", "Monongahela Incline Investigation", []),
    ("10_frequency_vs_otp", "Trip Frequency vs OTP", ["frequency_vs_otp.png"]),
    ("11_directional_asymmetry", "Directional Asymmetry", ["directional_asymmetry.png"]),
    ("12_geographic_span", "Route Geographic Span vs OTP", ["span_vs_otp.png", "density_vs_otp.png"]),
    ("13_correlation_clustering", "Cross-Route Correlation Clustering", ["correlation_heatmap.png", "dendrogram.png"]),
    ("14_covid_recovery", "COVID Recovery Trajectories", ["recovery_distribution.png", "recovery_by_mode.png", "regression_to_mean.png"]),
    ("15_municipal_equity", "Municipal/County Equity", ["top_bottom_municipalities.png", "pittsburgh_vs_suburban.png"]),
    ("16_transfer_hub_performance", "Transfer Hub Performance", ["connectivity_vs_otp.png", "hub_tier_comparison.png"]),
    ("17_weekend_weekday_profile", "Weekend vs Weekday Service Profile", ["weekend_ratio_vs_otp.png", "service_tier_comparison.png"]),
    ("18_multivariate_model", "Multivariate OTP Model", ["coefficient_plot.png", "predicted_vs_actual.png"]),
    ("19_ridership_weighted_otp", "Ridership-Weighted OTP", ["ridership_weighted_otp_trend.png"]),
    ("20_otp_ridership_causality", "OTP -> Ridership Causality", ["granger_summary.png", "lagged_crosscorr.png"]),
    ("21_covid_ridership_recovery", "COVID Ridership vs OTP Recovery", ["recovery_by_subtype.png", "recovery_scatter.png"]),
    ("22_delay_burden", "Passenger-Weighted Delay Burden", ["delay_burden_trend.png", "rate_vs_burden.png", "top10_burden.png"]),
    ("23_garage_performance", "Garage-Level Performance", ["garage_boxplot.png", "garage_otp_trend.png"]),
    ("24_daytype_ridership_trends", "Weekday vs Weekend Ridership Trends", ["daytype_ridership_trend.png", "weekend_share_trend.png", "weekend_share_vs_otp.png"]),
    ("25_ridership_equity", "Ridership Concentration & Equity", ["quintile_summary.png", "ridership_lorenz.png"]),
    ("26_ridership_multivariate", "Ridership in Multivariate OTP Model", ["coefficient_comparison.png", "partial_residual.png"]),
    ("27_traffic_congestion", "Traffic Congestion and OTP", ["aadt_vs_otp_scatter.png", "coefficient_comparison.png", "partial_residual.png"]),
    ("28_weather_impact", "Weather Impact on OTP", ["seasonal_weather_adjusted.png", "weather_correlation_heatmap.png", "weather_otp_timeseries.png", "weather_scatter_matrix.png"]),
    ("29_service_change_impact", "Service Change Impact", ["service_change_impact.png"]),
    ("30_service_level_otp_longitudinal", "Service Level vs OTP Longitudinal", ["service_level_scatter.png"]),
    ("31_stop_consolidation", "Stop Consolidation Candidates", ["candidate_map.png", "otp_gain_by_route.png"]),
    ("32_shelter_equity", "Shelter Equity", ["ridership_by_shelter.png", "shelter_coverage_by_mode.png"]),
    ("33_pandemic_ridership_geography", "Pandemic Ridership Geography", ["change_by_zone.png", "ridership_change_map.png"]),
    ("34_ridership_concentration", "Ridership Concentration / Pareto", ["gini_vs_otp.png", "pareto_curve.png"]),
    ("35_boarding_alighting_flows", "Boarding/Alighting Flow Analysis", ["net_flow_map.png", "top_generators_attractors.png"]),
]


def embed_image(path: Path) -> str:
    """Read a PNG file and return an <img> tag with base64-encoded data."""
    if not path.exists():
        print(f"  WARNING: image not found: {path}")
        return f'<p class="warning">Chart not available: {path.name}</p>'
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f'<img src="data:image/png;base64,{b64}" alt="{path.stem}" loading="lazy">'


def md_to_html(text: str) -> str:
    """Convert a narrow markdown subset to HTML.

    Handles: headings, bold, italic, inline code, links, tables, unordered
    lists, ordered lists, horizontal rules, and paragraphs.
    """
    lines = text.strip().split("\n")
    html_parts: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Blank line
        if not line.strip():
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^---+\s*$", line):
            html_parts.append("<hr>")
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            content = _inline(m.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            html_parts.append(f'<h{level} id="{slug}">{content}</h{level}>')
            i += 1
            continue

        # Table: collect all lines starting with |
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            html_parts.append(_parse_table(table_lines))
            continue

        # Unordered list
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]))
                i += 1
            html_parts.append(
                "<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>"
            )
            continue

        # Ordered list
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]))
                i += 1
            html_parts.append(
                "<ol>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ol>"
            )
            continue

        # Paragraph: collect contiguous non-blank, non-special lines
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i]):
            para_lines.append(lines[i])
            i += 1
        if para_lines:
            html_parts.append(f"<p>{_inline(' '.join(para_lines))}</p>")

    return "\n".join(html_parts)


def _is_block_start(line: str) -> bool:
    """Check whether a line starts a new block element."""
    if re.match(r"^#{1,6}\s+", line):
        return True
    if line.strip().startswith("|"):
        return True
    if re.match(r"^[-*]\s+", line):
        return True
    if re.match(r"^\d+\.\s+", line):
        return True
    if re.match(r"^---+\s*$", line):
        return True
    return False


def _inline(text: str) -> str:
    """Convert inline markdown: bold, italic, code, links."""
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text* (but not inside a bold)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    # Inline code: `text`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # En-dash from --
    text = text.replace("--", "&ndash;")
    return text


def _parse_table(lines: list[str]) -> str:
    """Parse markdown table lines into an HTML table."""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if len(rows) < 2:
        return ""

    # Row 1 is the separator (---|---), skip it
    header = rows[0]
    data_rows = rows[2:] if len(rows) > 2 else []

    html = "<table><thead><tr>"
    for cell in header:
        html += f"<th>{_inline(cell)}</th>"
    html += "</tr></thead><tbody>"
    for row in data_rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{_inline(cell)}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def parse_findings(path: Path) -> dict[str, str]:
    """Split FINDINGS.md into sections keyed by analysis number (str).

    Returns e.g. {"1": "PRT on-time performance...", "takeaways": "..."}.
    """
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return {}

    text = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}

    # Split on ## N. headers
    parts = re.split(r"(?=^## \d+\.)", text, flags=re.MULTILINE)
    for part in parts:
        m = re.match(r"^## (\d+)\.", part)
        if m:
            num = m.group(1)
            # Remove the heading line itself (we'll use our own heading)
            body = re.sub(r"^## \d+\..+\n+", "", part)
            sections[num] = body.strip()

    # Key Takeaways section
    m = re.search(r"## Key Takeaways\n+(.+)", text, re.DOTALL)
    if m:
        sections["takeaways"] = m.group(1).strip()

    return sections


def read_analysis_findings(dir_name: str) -> str | None:
    """Read an individual analysis's FINDINGS.md, return its content or None."""
    path = ANALYSES_DIR / dir_name / "FINDINGS.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    # Strip the top-level heading
    text = re.sub(r"^# .+\n+", "", text)
    return text.strip()


def build_toc(sections: dict[str, str]) -> str:
    """Generate a table of contents nav element."""
    items = []
    for dir_name, title, _ in ANALYSIS_REGISTRY:
        num = dir_name.split("_")[0].lstrip("0") or "0"
        anchor = f"analysis-{num}"
        items.append(f'<a href="#{anchor}">{num}. {title}</a>')

    items.append('<a href="#takeaways">Key Takeaways</a>')
    items.append('<a href="#appendix">Appendix: Additional Data</a>')

    links = "".join(f"<li>{item}</li>" for item in items)
    return f'<nav class="toc"><h2>Contents</h2><ul>{links}</ul></nav>'


def build_section(num: int, dir_name: str, title: str, pngs: list[str],
                  summary: str) -> str:
    """Build one analysis section with summary text and embedded charts."""
    anchor = f"analysis-{num}"
    html = f'<section id="{anchor}">'
    html += f"<h2>{num}. {title}</h2>"

    # Summary from main FINDINGS.md
    if summary:
        html += md_to_html(summary)
    else:
        html += '<p class="warning">No summary available for this analysis.</p>'

    # Embedded charts
    output_path = ANALYSES_DIR / dir_name / "output"
    for png in pngs:
        img_path = output_path / png
        html += f'<figure>{embed_image(img_path)}<figcaption>{png.replace("_", " ").replace(".png", "").title()}</figcaption></figure>'

    # Special case: hotspot map link
    if dir_name == "08_hotspot_map":
        html += (
            '<p class="map-note">An interactive version of this map is available as a '
            'companion file: <code>hotspot_map.html</code></p>'
        )

    # Collapsible detailed findings
    detail_text = read_analysis_findings(dir_name)
    if detail_text:
        html += "<details><summary>Detailed findings</summary>"
        html += md_to_html(detail_text)
        html += "</details>"

    html += "</section>"
    return html


def build_appendix(path: Path) -> str:
    """Convert ADDITIONAL_DATA_REQUESTS.md into an HTML appendix section."""
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return '<section id="appendix"><h2>Appendix: Additional Data Requests</h2><p>Not available.</p></section>'

    text = path.read_text(encoding="utf-8")
    # Strip the top-level heading
    text = re.sub(r"^# .+\n+", "", text)
    return f'<section id="appendix"><h2>Appendix: Additional Data Requests</h2>{md_to_html(text)}</section>'


def css() -> str:
    """Return the inline CSS for the report."""
    return """
    :root {
        --accent: #1a5276;
        --accent-light: #2980b9;
        --bg: #ffffff;
        --text: #2c3e50;
        --muted: #7f8c8d;
        --border: #dce1e4;
        --row-alt: #f8f9fa;
        --warning-bg: #fef3cd;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: var(--text);
        background: var(--bg);
        line-height: 1.7;
        max-width: 920px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
    }
    h1 { font-size: 1.9rem; color: var(--accent); margin-bottom: 0.3rem; }
    .subtitle { color: var(--muted); font-size: 0.95rem; margin-bottom: 2rem; }
    h2 { font-size: 1.45rem; color: var(--accent); margin: 2.5rem 0 0.8rem; padding-top: 1.5rem; border-top: 2px solid var(--border); }
    h3 { font-size: 1.15rem; color: var(--accent-light); margin: 1.5rem 0 0.5rem; }
    h4 { font-size: 1rem; color: var(--text); margin: 1rem 0 0.4rem; }
    p { margin: 0.6rem 0; }
    a { color: var(--accent-light); }
    code { background: #f0f0f0; padding: 0.15em 0.35em; border-radius: 3px; font-size: 0.9em; }
    hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }

    /* Table of contents */
    .toc {
        background: var(--row-alt);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1.2rem 1.5rem;
        margin: 1.5rem 0 2.5rem;
    }
    .toc h2 { font-size: 1.1rem; margin: 0 0 0.8rem; padding: 0; border: none; }
    .toc ul {
        list-style: none;
        columns: 2;
        column-gap: 2rem;
    }
    .toc li { margin: 0.2rem 0; break-inside: avoid; }
    .toc a { text-decoration: none; font-size: 0.92rem; }
    .toc a:hover { text-decoration: underline; }

    /* Tables */
    table { border-collapse: collapse; width: 100%; margin: 0.8rem 0; font-size: 0.92rem; }
    th, td { padding: 0.45rem 0.7rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { background: var(--accent); color: white; font-weight: 600; }
    tbody tr:nth-child(even) { background: var(--row-alt); }

    /* Figures */
    figure { margin: 1.2rem 0; text-align: center; }
    figure img { max-width: 100%; height: auto; border: 1px solid var(--border); border-radius: 4px; }
    figcaption { font-size: 0.85rem; color: var(--muted); margin-top: 0.3rem; }

    /* Lists */
    ul, ol { margin: 0.5rem 0 0.5rem 1.8rem; }
    li { margin: 0.2rem 0; }

    /* Collapsible details */
    details {
        background: var(--row-alt);
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 0.6rem 1rem;
        margin: 1rem 0;
    }
    details summary {
        cursor: pointer;
        font-weight: 600;
        color: var(--accent-light);
        font-size: 0.95rem;
    }
    details[open] summary { margin-bottom: 0.6rem; }
    details h2 { font-size: 1.1rem; border: none; margin: 1rem 0 0.5rem; padding: 0; }
    details h3 { font-size: 1rem; }

    /* Warnings */
    .warning { background: var(--warning-bg); padding: 0.5rem 0.8rem; border-radius: 4px; font-size: 0.9rem; }
    .map-note { font-style: italic; color: var(--muted); font-size: 0.9rem; }

    /* Sections */
    section { margin-bottom: 1rem; }

    /* Footer */
    footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.82rem; text-align: center; }

    /* Print */
    @media print {
        body { max-width: none; padding: 0.5in; }
        details[open] summary { display: none; }
        details { border: none; padding: 0; }
        details > * { display: block !important; }
        .toc { break-after: page; }
        section { break-inside: avoid; }
        h2 { break-after: avoid; }
    }
    """


def assemble_report(toc: str, sections: list[str], takeaways: str,
                    appendix: str) -> str:
    """Combine all pieces into the final HTML document."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    chart_count = sum(len(pngs) for _, _, pngs in ANALYSIS_REGISTRY)

    header = f"""<h1>PRT On-Time Performance Analysis</h1>
<p class="subtitle">35 analyses &middot; 98 routes &middot; {chart_count} charts &middot;
January 2019 &ndash; November 2025 &middot; 7,651 monthly observations</p>"""

    takeaways_html = ""
    if takeaways:
        takeaways_html = f'<section id="takeaways"><h2>Key Takeaways</h2>{md_to_html(takeaways)}</section>'

    footer = f"<footer>Generated {timestamp} from PRT-OTP-Analysis project</footer>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PRT On-Time Performance Analysis</title>
<style>{css()}</style>
</head>
<body>
{header}
{toc}
{"".join(sections)}
{takeaways_html}
{appendix}
{footer}
</body>
</html>"""


def main():
    """Orchestrate report generation: parse, embed, assemble, write."""
    print("Building PRT OTP Analysis report...")

    # Parse main findings
    print("  Parsing FINDINGS.md...")
    findings = parse_findings(FINDINGS_PATH)

    # Build TOC
    toc = build_toc(findings)

    # Build each analysis section
    sections = []
    for dir_name, title, pngs in ANALYSIS_REGISTRY:
        num_str = dir_name.split("_")[0].lstrip("0") or "0"
        num = int(num_str)
        summary = findings.get(num_str, "")
        print(f"  [{num:02d}] {title} ({len(pngs)} charts)")
        sections.append(build_section(num, dir_name, title, pngs, summary))

    # Key takeaways
    takeaways = findings.get("takeaways", "")

    # Appendix
    print("  Building appendix...")
    appendix = build_appendix(APPENDIX_PATH)

    # Assemble
    print("  Assembling HTML...")
    html = assemble_report(toc, sections, takeaways, appendix)

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "report.html"
    out_path.write_text(html, encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  Written: {out_path} ({size_mb:.1f} MB)")

    # Copy interactive map as companion file
    interactive_map = ANALYSES_DIR / "08_hotspot_map" / "output" / "hotspot_map.html"
    if interactive_map.exists():
        dest = OUTPUT_DIR / "hotspot_map.html"
        shutil.copy2(interactive_map, dest)
        print(f"  Copied: {dest}")

    print("Done.")


if __name__ == "__main__":
    main()
