import { $ } from "/static/jquery/src/jquery.js";
function say_hi(elt) {
    console.log("Welcome to", elt.text());
}

say_hi($("h1"));
let index = 0;

function make_table_sortable($table){
    const $lastHeaderCell = $($table.find("thead th").get(index));
    const $headerCell = $($table.find("thead th"));
    let $rows = $table.find('tbody tr');
    let isAsc = $lastHeaderCell.hasClass('sort-asc');

    $rows = $rows.toArray();
    $lastHeaderCell.removeClass('sort-asc sort-desc').attr("aria-sort", "none");
    $lastHeaderCell.attr("role", "button");

    // Sort descending
    if(isAsc){
        $headerCell.removeClass('sort-asc').removeClass('sort-desc');
        $lastHeaderCell.removeClass('sort-asc').addClass('sort-desc').attr("aria-sort", "descending");
        sortRows($rows, false);
    }
    //Unsort
    else if ($lastHeaderCell.hasClass('sort-desc')){
        $headerCell.removeClass('sort-asc').removeClass('sort-desc');
        $lastHeaderCell.removeClass('sort-desc').attr("aria-sort", "descending");;
        $rows.sort((a, b) => $(a).index() - $(b).index()); 
        $table.find('tbody').append($rows);
    }
    //sort ascending
    else{
        $headerCell.removeClass('sort-asc').removeClass('sort-desc');
        $lastHeaderCell.removeClass('sort-desc').addClass('sort-asc');
        sortRows($rows, index, true);
    }

    function sortRows($rows, ascending){
        $rows.sort(function (a, b){
            const $a = $(a).children().eq(index);
            const $b = $(b).children().eq(index);
            const scoreA = parseFloat($a.data('value'));
            const scoreB = parseFloat($b.data('value'));
            return ascending ? scoreA - scoreB : scoreB - scoreA;
        });
        $table.find('tbody').append($rows);
    }

}

$('.sortable thead tr th').on('click', (e) => {
    let $table = $(e.target).closest('table');
    index = $(e.target).index();
    make_table_sortable($table);

});

const $submissionForm = $(".submission-form");
    if($submissionForm.length){
        make_form_async($submissionForm);
    }

function make_form_async($form){
    if(!$form || !$form.length){
        console.log("There is no form");
        return;
    }
    $form.on("submit", function (e){
        e.preventDefault();
        let data = new FormData(this);
        let url = $form.attr("action");
        let enctype = $form.attr("enctype");

        let $inputs = $form.find("input, button");
        $inputs.prop("disabled", true);

        $.ajax({
            url: url,
            type: "POST",
            data: data,
            processData: false,
            contentType: false,
            mimeType: enctype,
            headers: {
                "X-CSRFToken": csrftoken
            },
            success: function(){
                $form.replaceWith("<p>Upload succeeded</p>");
            },
            error: function (xhr, status, error) {
                console.error("The form didn't submit because of: ", error);
                $inputs.prop("disabled", false);
            }
            
        });
    });
}

make_grade_hypothesized($("#hypoTable"));

function make_grade_hypothesized($table){
    let $hypoButton = $("<button>Hypothesize</button>");
    $("#hypoTable").before($hypoButton);

    $hypoButton.on('click', function(){
        let isHypo = $table.hasClass('hypothesized');

        if(isHypo) {
            $table.removeClass('hypothesized');
            $hypoButton.text('Hypothesize');
            realGrades($table);
        }
        else {
            $table.addClass("hypothesized");
            $hypoButton.text('Actual grades');
            hypoGrades($table);
        }
        calculateHypoGrade($table);

    });
    
    function hypoGrades($table){
        let gradeData = $table.find('tbody tr td:last-child');
        for(let i of gradeData){
            let gradeText = $(i).text().trim();
            if(gradeText === "Not Due" || gradeText === "Ungraded"){
                let $input = $('<input type=\"number\" class=\"hypo-input\" placeholder=\"Enter grade\" data-score=\"'+gradeText+'\" data-weight=\"'+$(i).data('weight')+'\">');
                $(i).replaceWith($input);
                $input.on('keyup', function() {
                    calculateHypoGrade($table);
                })
            }
        };
    }

    function realGrades($table){
        let gradeData = $table.find('tbody tr input');
        for(let i of gradeData){
            $(i).replaceWith("<td data-weight=\""+$(i).data('weight')+"\">"+$(i).data('score')+"</td>");
        }  
    }

    function calculateHypoGrade($table){
        let totalPoints = 0;
        let totalWeight = 0;

        let gradeData = $table.find('tbody tr td:last-child');
        for(let i of gradeData){
            let weight = $(i).data('weight');
            if($(i).text() != "Missing" && $(i).text() != "Ungraded" && $(i).text() != "Not Due"){
                let weight = $(i).data('weight');
                let tdScore = parseFloat($(i).text());

                totalPoints += (tdScore * weight) / 100;
                totalWeight += weight;
            }
            if($(i).text() == "Missing"){
                totalWeight += weight;
            }
        }
        let gradeDataInput = $table.find('tbody tr input');
        for(let i of gradeDataInput){
            if($(i).val()){
                let weight = $(i).data('weight');
                let tdScore = parseFloat($(i).val());
    
                totalPoints += (tdScore * weight) / 100;
                totalWeight += weight;
            } 

        }

        let finalGrade = ((totalPoints / totalWeight) * 100).toFixed(2);
        $table.find('.final-grade').text(finalGrade + '%');
    }
}
