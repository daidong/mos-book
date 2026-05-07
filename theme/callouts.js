/*
 * Classify mdBook blockquotes by their leading bold label so the
 * stylesheet can color them differently:
 *   > **Note:** …             -> .callout-note
 *   > **Warning:** …          -> .callout-warning
 *   > **Key insight:** …      -> .callout-insight
 *   > **Tip:** …              -> .callout-tip
 *   > **Learning objectives** -> .callout-objectives
 *
 * Runs once at DOMContentLoaded. No dependencies.
 */
(function () {
    function classify() {
        var quotes = document.querySelectorAll(".content blockquote");
        for (var i = 0; i < quotes.length; i++) {
            var bq = quotes[i];
            var firstP = bq.querySelector("p");
            if (!firstP) continue;
            var firstStrong = firstP.querySelector("strong");
            if (!firstStrong) continue;
            var label = (firstStrong.textContent || "").trim().toLowerCase();
            // Strip a trailing colon if present.
            if (label.endsWith(":")) label = label.slice(0, -1).trim();

            if (label === "note") {
                bq.classList.add("callout-note");
            } else if (label === "warning" || label === "caution") {
                bq.classList.add("callout-warning");
            } else if (
                label === "key insight"
                || label === "insight"
                || label === "key idea"
                || label === "takeaway"
            ) {
                bq.classList.add("callout-insight");
            } else if (label === "tip" || label === "pro tip") {
                bq.classList.add("callout-tip");
            } else if (
                label === "learning objectives"
                || label === "learning goals"
            ) {
                bq.classList.add("callout-objectives");
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", classify);
    } else {
        classify();
    }
})();
