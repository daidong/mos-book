/*
 * Theme-side DOM enhancements for the printed-textbook reading style.
 *
 * 1. Classify mdBook blockquotes by their leading bold label so the
 *    stylesheet can render each as a distinct LaTeX-style environment:
 *      > **Note:** …             -> .callout-note
 *      > **Warning:** …          -> .callout-warning
 *      > **Key insight:** …      -> .callout-insight
 *      > **Tip:** …              -> .callout-tip
 *      > **Learning objectives** -> .callout-objectives
 *
 * 2. Split the chapter H1 ("Chapter N: Title — Subtitle") into structured
 *    spans so the CSS can render a small-caps eyebrow above a serif
 *    display title with an optional italic subtitle, like a printed book.
 *
 * 3. Wrap the leading "Figure N.X:" of italic figure captions in a
 *    small-caps label span for the same scholarly-press treatment.
 *
 * Runs once at DOMContentLoaded. No dependencies.
 */
(function () {
    function classifyCallouts() {
        var quotes = document.querySelectorAll(".content blockquote");
        for (var i = 0; i < quotes.length; i++) {
            var bq = quotes[i];
            var firstP = bq.querySelector("p");
            if (!firstP) continue;
            var firstStrong = firstP.querySelector("strong");
            if (!firstStrong) continue;
            var label = (firstStrong.textContent || "").trim().toLowerCase();
            if (label.endsWith(":")) label = label.slice(0, -1).trim();

            var cls = null;
            if (label === "note") cls = "callout-note";
            else if (label === "warning" || label === "caution") cls = "callout-warning";
            else if (
                label === "key insight" || label === "insight"
                || label === "key idea" || label === "takeaway"
            ) cls = "callout-insight";
            else if (label === "tip" || label === "pro tip") cls = "callout-tip";
            else if (
                label === "learning objectives" || label === "learning goals"
            ) cls = "callout-objectives";

            if (cls) {
                bq.classList.add("callout", cls);
                firstStrong.classList.add("callout-label");
            }
        }
    }

    /*  Chapter opener.
     *
     *  STYLE_GUIDE.md mandates exactly one H1 per chapter, of the form
     *      "Chapter N: Title — Subtitle"
     *  or sometimes
     *      "Chapter N: Title"
     *
     *  We rebuild that H1 as:
     *      <span class="chapter-eyebrow">Chapter N</span>
     *      <span class="chapter-title">Title</span>
     *      <span class="chapter-subtitle">Subtitle</span>     (if present)
     *  and add a `.has-chapter-eyebrow` class so the CSS can reset
     *  default H1 spacing for this case.
     */
    function styleChapterOpener() {
        var h1 = document.querySelector(".content main h1");
        if (!h1) return;
        // Skip if mdBook has already injected anchor children we'd lose.
        // We preserve any <a class="header"> wrapper by writing inside it.
        var target = h1.querySelector("a.header") || h1;
        var raw = target.textContent || "";
        // Match "Chapter N:" / "Chapter N." / "Chapter N —" / "Appendix X:" etc.
        var m = raw.match(/^\s*(Chapter\s+[A-Za-z0-9]+|Appendix\s+[A-Za-z]+|Part\s+[IVXLC0-9]+)\s*[:\.\u2014\-]\s*(.+?)\s*$/);
        if (!m) return;

        var eyebrow = m[1].trim();
        var rest    = m[2].trim();

        // Split off an em-dash subtitle if present.
        var title = rest, subtitle = "";
        var dashIdx = rest.indexOf(" \u2014 ");
        if (dashIdx === -1) dashIdx = rest.indexOf(" - ");
        if (dashIdx > 0) {
            title    = rest.slice(0, dashIdx).trim();
            subtitle = rest.slice(dashIdx + 3).trim();
        }

        // Preserve the anchor-link icon (mdBook's <a class="header">).
        var anchor = h1.querySelector("a.header") ? h1.querySelector("a.header").cloneNode(false) : null;

        h1.classList.add("has-chapter-eyebrow");
        h1.innerHTML = "";

        var eyeEl = document.createElement("span");
        eyeEl.className = "chapter-eyebrow";
        eyeEl.textContent = eyebrow;
        h1.appendChild(eyeEl);

        var titleEl = document.createElement("span");
        titleEl.className = "chapter-title";
        titleEl.textContent = title;
        h1.appendChild(titleEl);

        if (subtitle) {
            var subEl = document.createElement("span");
            subEl.className = "chapter-subtitle";
            subEl.textContent = subtitle;
            h1.appendChild(subEl);
        }

        if (anchor) {
            // Re-apply the anchor link as a trailing decoration so
            // permalinks still work without disturbing the layout.
            anchor.className = "header chapter-anchor";
            anchor.textContent = "";
            h1.appendChild(anchor);
        }
    }

    /*  Figure captions.
     *
     *  STYLE_GUIDE.md convention is:
     *      ![alt](file.png)
     *      *Figure N.X: Caption text...*
     *
     *  mdBook renders the second line as <p><em>Figure N.X: …</em></p>.
     *  We wrap the "Figure N.X" prefix in a span so the CSS can render
     *  it in small caps oxblood, like a printed-book caption label.
     */
    function styleFigureCaptions() {
        var ems = document.querySelectorAll(".content main p > em:only-child");
        for (var i = 0; i < ems.length; i++) {
            var em = ems[i];
            // Only target captions that follow an image-only paragraph.
            var prev = em.parentNode.previousElementSibling;
            if (!prev || prev.tagName !== "P") continue;
            var img = prev.querySelector(":scope > img:only-child");
            if (!img) continue;

            var raw = em.textContent || "";
            var m = raw.match(/^\s*(Figure|Table|Listing|Equation)\s+([0-9]+(?:\.[0-9]+)?[a-z]?)\s*[:\.]\s*(.+)$/);
            if (!m) continue;

            em.classList.add("figure-caption");
            em.parentNode.classList.add("has-figure-caption");
            em.innerHTML = "";

            var labelEl = document.createElement("span");
            labelEl.className = "figure-caption-label";
            labelEl.textContent = m[1] + " " + m[2];
            em.appendChild(labelEl);

            var sep = document.createTextNode("  ");
            em.appendChild(sep);

            var bodyEl = document.createElement("span");
            bodyEl.className = "figure-caption-body";
            bodyEl.textContent = m[3];
            em.appendChild(bodyEl);
        }
    }

    function run() {
        classifyCallouts();
        styleChapterOpener();
        styleFigureCaptions();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", run);
    } else {
        run();
    }
})();
