# Import Plan: dissertation-data → PRT-Analysis

What's worth bringing over from `external/dissertation-data` (the birth center
dissertation project) into this transit analysis project.

## Submodule location

```
external/dissertation-data/   # git submodule, read-only reference
```

---

## Website features

The dissertation site (`products/website/`) has several features the PRT site
doesn't. These are ranked by effort and value.

### 1. Glossary auto-linking (high value, medium effort)

**What it does:** Scans every rendered HTML page for glossary terms and wraps
the first occurrence with a tooltip link back to the glossary page. Tracks which
pages use which terms and displays that on the glossary page.

**Source files:**
- `external/dissertation-data/products/website/main.py` — `build_glossary_index()`, `scan_glossary_usage()`, `autolink_glossary_terms()`, `_replace_in_text_nodes()`

**Why it's useful:** PRT already has `docs/GLOSSARY.md` and a `glossary.yaml`
powering the website glossary page. Auto-linking would make those terms
discoverable in context — readers hovering over "OTP" or "headway" on any
analysis page would see the definition without navigating away.

**Effort:** Medium. The logic is ~150 lines of Python that operates on rendered
HTML strings. Needs integration into `products/website/main.py`'s page
rendering loop and the glossary template needs a "used in" section.

---

### 2. Flashcards (medium value, low effort)

**What it does:** An interactive study tool built from `glossary.yaml`. Users
flip cards (term → definition), rate confidence (know / unsure / don't know),
filter by category, and shuffle. Progress persists in localStorage.

**Source files:**
- `external/dissertation-data/products/website/templates/flashcards.html` — fully self-contained template with inline JS

**Why it's useful:** Useful for onboarding new people to transit terminology
(OTP, headway, deadhead, etc.) or for presentations. No backend needed.

**Effort:** Low. Copy the template, add a nav link in `base.html`, and wire up
the `terms_json` variable in `main.py` (a JSON dump of glossary terms). The
dissertation already has a working implementation.

---

### 3. Mermaid diagram support (medium value, low effort)

**What it does:** Converts markdown code fences tagged `mermaid` into rendered
diagrams via the Mermaid JS library. Useful for data lineage, pipeline flow, and
entity-relationship diagrams.

**Source files:**
- `external/dissertation-data/products/website/main.py` — `render_markdown()` regex rewrite
- `external/dissertation-data/products/website/templates/base.html` — Mermaid JS include and init

**Why it's useful:** PRT analyses could benefit from data flow diagrams (e.g.,
GTFS → stops table → route-level OTP → analysis). Currently no way to embed
diagrams in the site.

**Effort:** Low. Add the Mermaid CDN script to `base.html` and a 3-line regex
to `render_markdown()` that rewrites `<pre><code class="language-mermaid">` to
`<pre class="mermaid">`.

---

### 4. Data dictionary as a website page (medium value, low effort)

**What it does:** Renders a project data dictionary / codebook markdown file as
a standalone page on the site.

**Source files:**
- `external/dissertation-data/products/website/templates/codebook.html` — simple template

**Why it's useful:** PRT has `data/DATA_DICTIONARY.md` and `data/SCHEMA.md` but
these are only readable on GitHub or locally. Putting them on the site makes the
data documentation accessible to non-developers (transit agency staff, city
council, etc.).

**Effort:** Low. Add a template, a nav link, and a few lines in `main.py` to
render the markdown.

---

### 5. Methods primer page (low–medium value, medium effort)

**What it does:** A dedicated page explaining statistical methods in plain
language, with KaTeX math rendering for formulas.

**Source files:**
- `external/dissertation-data/products/website/templates/primer.html`
- `external/dissertation-data/products/website/primer.md`

**Why it's useful:** PRT uses Granger causality, clustering, multivariate
regression, and other methods that a general audience may not know. A primer
would help transit advocates and agency staff interpret findings.

**Effort:** Medium. The template is simple, but writing the content (explaining
OTP calculation, seasonal decomposition, Granger causality, etc.) is the real
work. KaTeX integration is a small addition to `base.html`.

---

### 6. Literature aggregation page (low value for PRT, high effort)

**What it does:** Collects per-analysis `LITERATURE.md` files, deduplicates
references, and builds a combined page with alphabetical topic navigation.

**Source files:**
- `external/dissertation-data/products/website/templates/literature.html`
- `external/dissertation-data/products/website/main.py` — literature collection logic

**Why it's useful:** Less relevant for PRT. The dissertation is an academic
project with extensive citations. PRT analyses reference data sources (already
tracked via `SOURCES.yaml`) more than scholarly literature.

**Effort:** High relative to value. Would need per-analysis `LITERATURE.md`
files to exist, plus the aggregation logic.

**Recommendation:** Skip unless PRT starts citing academic transit research.

---

## Data assets

### County/tract demographics (medium value)

**Files:**
- `data/output/county_data.csv` — 3,108 counties with income, poverty, race
- `data/output/tract_data.csv` — ~72k tracts with fertility, poverty, education, race
- `data/output/segregation_indices.csv` — dissimilarity, isolation, ICE per county

**Why useful:** PRT's equity analyses (04, 15, 25) use demographic data. The
tract-level race/poverty data could enrich transit-stop-level equity analysis
without needing a separate Census API pipeline.

**Caveat:** The dissertation data is ACS 2019 5-year. PRT may want more recent
estimates. The Census fetch pipeline (`pipeline/01_census_fetch/`) could be
adapted to pull updated data.

### Census fetch pipeline (medium value, reference only)

**Files:** `pipeline/01_census_fetch/main.py`, `src/dissertation_data/common.py`

**Why useful:** If PRT ever needs to pull Census data directly, this is a
tested, working implementation with variable validation and error handling.
Better used as a reference than imported directly.

---

## Recommended import order

1. **Mermaid support** — smallest change, immediate utility
2. **Data dictionary page** — quick win for data transparency
3. **Flashcards** — self-contained, fun, good for outreach
4. **Glossary auto-linking** — biggest UX improvement, moderate integration work
5. **Methods primer** — template is easy, content takes time
6. **Census data** — only when an analysis needs it
