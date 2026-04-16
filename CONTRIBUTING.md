# Contributing to Modern Operating Systems

Thank you for your interest in contributing to this book. This document
explains our workflow, conventions, and expectations so that many people
can collaborate effectively on a single, coherent textbook.

---

## Quick Start

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/<your-username>/mos-book.git
cd mos-book

# 3. Create a branch for your work
git checkout -b ch04-fix-scheduling-diagram

# 4. Make your changes (see conventions below)

# 5. Build locally to verify
make html        # or: make serve

# 6. Commit and push
git add -A && git commit -m "ch04: fix scheduling diagram label"
git push origin ch04-fix-scheduling-diagram

# 7. Open a Pull Request against `main`
```

## Repository Layout

```
src/            Book content (Markdown + figures)
code/           Lab source code (C, Python, shell, YAML)
projects/       Capstone project descriptions
templates/      Report and proposal templates
scripts/        Build and CI utilities
```

All prose lives under `src/`. All runnable code lives under `code/`.
Do not mix the two — chapters reference code via relative links.

## Branch and Commit Conventions

### Branch naming

```
ch<NN>-<short-description>    # chapter work
lab<NN>-<short-description>   # lab-specific work
infra-<short-description>     # build system, CI, templates
fix-<short-description>       # cross-cutting fixes
```

### Commit messages

Use the chapter prefix so changes are easy to trace:

```
ch05: add CFS vruntime walkthrough diagram
lab08: fix etcd cluster startup script
infra: add mdbook-pdf to CI build
fix: correct broken cross-references in Part IV
```

Keep the first line under 72 characters. Use the body for detail when
needed.

## What to Contribute

### High-impact contributions

- **Chapter drafts** — writing or expanding a chapter's `index.md`
- **Lab content** — instructions, starter code, solution sketches
- **Figures** — original diagrams (prefer SVG; PNG acceptable at 2x
  resolution)
- **Code samples** — lab implementations, scripts, Makefiles
- **Review** — technical accuracy, clarity, completeness

### Also welcome

- Typo and grammar fixes
- Broken link repairs
- Build system improvements
- Accessibility improvements (alt text, color contrast)
- Translations (coordinate in an issue first)

### What to avoid

- Do not add content from the `outdated/` or `archive/` directories in
  the course materials — that content has been superseded
- Do not introduce new dependencies without discussion in an issue
- Do not restructure chapters or move files without prior approval

## Chapter Ownership

Each chapter may have a **lead author** listed in its `index.md`
frontmatter. If a chapter has a lead author:

- Small fixes (typos, broken links): submit a PR directly
- Substantive changes (new sections, rewrites): open an issue first
  and tag the lead author for discussion

If no lead author is listed, the chapter is open for any contributor.

## Writing a Chapter

### Structure

Every chapter directory follows this layout:

```
src/partN-<name>/ch<NN>-<topic>/
    index.md              # Main chapter text
    lab-<name>.md         # Hands-on lab section
    figures/
        <descriptive-name>.png
        <descriptive-name>.svg
```

### Chapter template

```markdown
# Chapter N: Title

> **Learning objectives**
>
> After completing this chapter and its lab, you will be able to:
>
> - Objective 1
> - Objective 2
> - Objective 3

## N.1 First Section

...

## N.2 Second Section

...

## Summary

Key takeaways from this chapter:

- Point 1
- Point 2

## Further Reading

- Reference 1
- Reference 2
```

See [STYLE_GUIDE.md](STYLE_GUIDE.md) for detailed formatting rules.

## Writing a Lab

Labs are the heart of this book. Every lab must be:

1. **Reproducible** — runs on a standard Ubuntu 22.04/24.04 VM in
   VirtualBox with no special hardware
2. **Measurable** — produces quantitative results (latencies, counters,
   percentiles)
3. **Explainable** — the student must connect measurements to OS
   mechanisms

### Lab template

```markdown
# Lab N: Title

> **Estimated time:** X hours
>
> **Prerequisites:** Chapter N concepts, working Ubuntu VM
>
> **Tools used:** perf, strace, etc.

## Objectives

...

## Background

...

## Part A: Basic

...

## Part B: Intermediate

...

## Part C: Advanced (Optional)

...

## Deliverables

...

## Reflection Questions

...
```

### Lab code

Place all lab source code in `code/ch<NN>-<name>/` with its own
`README.md` explaining how to build and run. Include a `Makefile` when
applicable.

## Figures

- Place figures in the chapter's `figures/` directory
- Use descriptive filenames: `cfs-vruntime-tree.svg`, not `fig3.png`
- Prefer SVG for diagrams (they scale and are diffable)
- PNG is acceptable for screenshots and photos (use 2x resolution)
- Always include alt text in the Markdown image reference
- Reference figures with relative paths:
  `![CFS red-black tree](figures/cfs-vruntime-tree.svg)`

## Pull Request Process

1. **One PR per logical change.** Don't bundle a chapter rewrite with a
   typo fix in another chapter.
2. **Self-review first.** Build locally (`make html`) and read through
   your changes before requesting review.
3. **Fill in the PR template.** Describe what changed and why.
4. **Respond to review.** Address feedback with new commits (don't
   force-push during review).
5. **Squash on merge.** Maintainers will squash-merge to keep `main`
   history clean.

### PR checklist

Before submitting, verify:

- [ ] `make html` builds without errors
- [ ] All new images have alt text
- [ ] Cross-references and links work
- [ ] Code samples compile and run
- [ ] No content from `outdated/` or `archive/` sources
- [ ] Commit messages follow the `ch<NN>: description` convention

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/)
code of conduct. Be respectful, constructive, and inclusive.

## Questions?

Open an issue with the `question` label, or reach out to the maintainer
directly.
