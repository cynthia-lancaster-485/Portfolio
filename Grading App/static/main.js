import { $ } from "/static/vendor/jquery.module.min.js";

/* ---------- Sortable tables ---------- */

// Clicking a sortable column header cycles: ascending -> descending -> original order
function make_table_sortable($table) {
    const $headers = $table.find("thead th.sort-column");

    // Tell screen readers and keyboard users these headers are clickable
    $headers.attr({ role: "button", tabindex: 0, "aria-sort": "none" });

    $headers.on("click", function () {
        sortByColumn($table, $(this));
    });
    $headers.on("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            sortByColumn($table, $(this));
        }
    });
}

function sortByColumn($table, $header) {
    const index = $header.index();
    const $tbody = $table.find("tbody");
    const rows = $tbody.find("tr").toArray();
    let state;

    if ($header.hasClass("sort-asc")) {
        state = "descending";
    } else if ($header.hasClass("sort-desc")) {
        state = "none";
    } else {
        state = "ascending";
    }

    // Only one column is sorted at a time
    $table.find("thead th.sort-column").removeClass("sort-asc sort-desc").attr("aria-sort", "none");

    if (state === "none") {
        // Restore the original order using each row's data-index
        rows.sort((a, b) => $(a).data("index") - $(b).data("index"));
    } else {
        $header.addClass(state === "ascending" ? "sort-asc" : "sort-desc").attr("aria-sort", state);
        const direction = state === "ascending" ? 1 : -1;
        rows.sort((a, b) => direction * (cellValue(a, index) - cellValue(b, index)));
    }

    $(rows).appendTo($tbody);
}

// Numeric value of a cell, from data-value if present. Cells with no number sort last.
function cellValue(row, index) {
    const $cell = $(row).children().eq(index);
    const raw = $cell.data("value");
    const value = parseFloat(raw !== undefined && raw !== "" ? raw : $cell.text());
    return Number.isNaN(value) ? -Infinity : value;
}

$("table.sortable").each(function () {
    make_table_sortable($(this));
});

/* ---------- Asynchronous file upload ---------- */

function make_form_async($form) {
    $form.on("submit", function (e) {
        e.preventDefault();
        const data = new FormData(this);
        const csrftoken = $form.find("input[name=csrfmiddlewaretoken]").val();
        const $inputs = $form.find("input, button");

        $form.find("output.error-msg").remove();

        $.ajax({
            url: $form.attr("action"),
            type: "POST",
            data: data,
            processData: false,
            contentType: false,
            mimeType: $form.attr("enctype"),
            headers: { "X-CSRFToken": csrftoken },
            success: function () {
                $form.replaceWith("<p>Upload succeeded</p>");
            },
            error: function (xhr) {
                // The server re-renders the page with the error message; show that message here
                const message = $(xhr.responseText).find("output.error-msg").text() || "Upload failed. Please try again.";
                console.error("Upload failed:", message);
                $form.prepend($("<output class='error-msg'>").text(message));
                $inputs.prop("disabled", false);
            },
        });

        // Disable after FormData is built, so the file is still included
        $inputs.prop("disabled", true);
    });
}

const $submissionForm = $("form.submission-form");
if ($submissionForm.length) {
    make_form_async($submissionForm);
}

/* ---------- "What if" grade calculator ---------- */

function make_grade_hypothesized($table) {
    const $hypoButton = $("<button type='button'>Hypothesize</button>");
    $table.before($hypoButton);

    $hypoButton.on("click", function () {
        if ($table.hasClass("hypothesized")) {
            $table.removeClass("hypothesized");
            $hypoButton.text("Hypothesize");
            realGrades($table);
        } else {
            $table.addClass("hypothesized");
            $hypoButton.text("Actual grades");
            hypoGrades($table);
        }
        calculateHypoGrade($table);
    });
}

// Replace "Not Due" and "Ungraded" with number inputs, remembering the original text
function hypoGrades($table) {
    $table.find("tbody tr td:last-child").each(function () {
        const $cell = $(this);
        const text = $cell.text().trim();
        if (text === "Not Due" || text === "Ungraded") {
            $cell.data("original", text);
            const $input = $("<input type='number' class='hypo-input' min='0' max='100' step='any' placeholder='%'>")
                .attr("aria-label", "Hypothetical grade in percent");
            $input.on("input keyup", () => calculateHypoGrade($table));
            $cell.empty().append($input);
        }
    });
}

function realGrades($table) {
    $table.find("tbody tr td:last-child").each(function () {
        const $cell = $(this);
        if ($cell.data("original")) {
            $cell.text($cell.data("original"));
            $cell.removeData("original");
        }
    });
}

// Same rules as the server: graded and missing count, ungraded and not due are ignored
function calculateHypoGrade($table) {
    let earned = 0;
    let available = 0;

    $table.find("tbody tr td:last-child").each(function () {
        const $cell = $(this);
        const weight = parseFloat($cell.data("weight"));
        const $input = $cell.find("input");
        const text = $cell.text().trim();
        let percent = null;

        if ($input.length) {
            if ($input.val() !== "") percent = parseFloat($input.val());
        } else if (text === "Missing") {
            percent = 0;
        } else if (text !== "Ungraded" && text !== "Not Due") {
            // data-value holds the unrounded percentage, so this matches the server's math
            percent = parseFloat($cell.data("value"));
        }

        if (percent !== null && !Number.isNaN(percent)) {
            earned += (percent / 100) * weight;
            available += weight;
        }
    });

    const finalGrade = available > 0 ? (earned / available) * 100 : 100;
    $table.find(".final-grade").text(finalGrade.toFixed(2) + "%");
}

const $hypoTable = $("#hypoTable");
if ($hypoTable.length) {
    make_grade_hypothesized($hypoTable);
}
