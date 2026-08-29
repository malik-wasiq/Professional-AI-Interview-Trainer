// Small client-side check so users get instant feedback before the page
// even reaches the server (the server still validates this too).
document.addEventListener("DOMContentLoaded", function () {
    var answerForm = document.getElementById("answer-form");
    if (!answerForm) {
        return;
    }

    answerForm.addEventListener("submit", function (event) {
        var answer = document.getElementById("answer");
        if (answer && answer.value.trim() === "") {
            event.preventDefault();
            answer.focus();
        }
    });

    // Live character count, purely cosmetic -- doesn't affect validation.
    var answer = document.getElementById("answer");
    var count = document.getElementById("answer-count");
    if (answer && count) {
        var updateCount = function () {
            count.textContent = answer.value.length;
        };
        answer.addEventListener("input", updateCount);
        updateCount();
    }
});
