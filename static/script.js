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
});
