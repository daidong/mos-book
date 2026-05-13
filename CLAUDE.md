# CLAUDE.md — Modern Operating Systems (mos-book)

Guidance for Claude Code (and any agent) working in this repository.

## Project at a Glance

This is the source for *Modern Operating Systems*, a free open-source
textbook for senior undergrad and graduate CS students. It teaches
core OS concepts through modern systems (containers, Kubernetes,
distributed consensus, storage engines, AI agent runtimes), with a
hands-on lab at the end of every chapter.

The book is built with **mdBook**. Source markdown lives under `src/`,
the theme overlay under `theme/`, and the rendered output under `book/`.
Every push to `main` deploys to GitHub Pages via the workflow in
`.github/workflows/deploy.yml`.

Key files to know:
- `book.toml` — mdBook config (output html, search, print, mathjax)
- `src/SUMMARY.md` — chapter ordering and structure
- `theme/css/academic.css` — the entire visual style overlay
- `theme/head.hbs` — Google Fonts, OG tags
- `STYLE_GUIDE.md` — markdown conventions, callout grammar, code blocks
- `Makefile` — `make html`, `make serve`, `make pdf`, `make check`

## Build & Preview

```bash
make serve          # live-reload at http://localhost:3000
make html           # one-shot build to ./book/
make pdf            # PDF via headless Chrome on print.html
make check          # validate links and code blocks
```

Do not commit `book/` — it is the build output. CI rebuilds on push.

## Writing Conventions

Read `STYLE_GUIDE.md` before authoring or editing prose. Highlights:

- **Headings**: exactly one H1 per file, H2 numbered as `N.M`,
  H3 unnumbered subsection, avoid H4.
- **Callout grammar**: `> **Note:** …`, `> **Warning:** …`,
  `> **Key insight:** …`, `> **Tip:** …`, plus the chapter-opening
  `> **Learning objectives**` block. The CSS keys off the leading
  bold label.
- **Figures**: image immediately followed by `*Figure N.X: caption…*`
  on its own line. The CSS pairs them into a figure unit.
- **Voice**: clarity over cleverness, concrete over abstract, measure
  don't just describe, respect the reader's time.

## Design Context

This section is the source of truth for visual decisions on the web
edition. The full version lives in `.impeccable.md` — read that file
before doing visual work. Summary:

### Users

Senior CS students and practicing engineers reading on laptop or
external monitor for **sustained chapter-length sessions**, often
alongside a terminal running labs. Layout stability and findability
matter as much as first-read pleasure.

### Brand Personality

Three words: **curious, exploratory, playful** — held inside a
**classical scholarly** container. The form is restrained (Bringhurst /
MIT Press / Knuth lineage). The voice inside the form is the opposite:
asks questions, follows hunches, invites the reader into the
investigation.

### Aesthetic Direction

Source Serif 4 body on paper-tone background (#fbfaf6). Navy (#1f3a66)
primary accents, muted oxblood (#6b3f1d) secondary. Booktabs tables.
Fleuron section breaks. Drop cap on chapter opening paragraph. Light
theme is default; dark theme is a secondary mode.

**Anchor references**: Tufte, Bringhurst, MIT Press / Stripe Press,
Knuth TAOCP.

**Anti-references** (this must NOT look like any of):
1. Generic dev-docs (Docusaurus, GitBook, Mintlify, ReadtheDocs)
2. AI-era dark-with-cyan-glow
3. Times-New-Roman academic drab
4. Maximalist startup landing page

### Design Principles

1. **The reading column is sacred** — every decision serves 30+ minute
   reading sessions.
2. **One left edge** — prose, tables, code, figures, captions all share
   the same left edge. No per-element auto-centering.
3. **Restrained container, expressive voice** — CSS is quiet so prose
   can be loud. Bold moves are reserved for moments that earn them.
4. **Print-quality typography on screen** — real serif, old-style
   numerals, hyphenation, fluid clamp-based scale.
5. **Honest evidence over visual flourish** — tables, plots, code are
   first-class content, not decoration. No sparkline ornaments.
6. **No defaults** — every visible element has been chosen. mdBook
   defaults, generic doc conventions, and AI-era tics are rejected.
   If output could have come from any other site, treat it as a bug.

See `.impeccable.md` for the full design context, anchor references,
and rationale.
