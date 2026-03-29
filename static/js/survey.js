let btnSurveySubmit = document.getElementById('surveySubmit');
btnSurveySubmit.disabled = true;
function validateSurveyForm() {
    let currentOptionsForms = document.getElementsByClassName('survey-option');
    let currentOptionsCounter = currentOptionsForms.length;

    if (currentOptionsCounter > 0) {
        btnSurveySubmit.disabled = false;
        return true;
    }

    btnSurveySubmit.disabled = true;
    return false;
}

function addSurveyOptionForm() {
    if (event) {
        event.preventDefault();
    }

    let surveyOptionsTotalNewForms = document.getElementById('id_option-TOTAL_FORMS')
    let currentOptionsForms = document.getElementsByClassName('survey-option');
    let currentOptionsCounter = currentOptionsForms.length;

    const emptyOptionElement = document.getElementById('survey-option-empty-form').cloneNode(true);
    emptyOptionElement.setAttribute('class', 'survey-option')
    emptyOptionElement.setAttribute('id', `survey-option-form-${currentOptionsCounter}`)
    const regex = new RegExp('__prefix__', 'g');
    emptyOptionElement.innerHTML = emptyOptionElement.innerHTML.replace(regex, currentOptionsCounter);

    surveyOptionsTotalNewForms.setAttribute('value', currentOptionsCounter + 1);

    const formOptionTarget = document.getElementById('survey-options-list');
    formOptionTarget.append(emptyOptionElement);
    validateSurveyForm();
}

function removeSurveyOptionForm() {
    if (event) {
        event.preventDefault();
    }
    let surveyOptionsTotalNewForms = document.getElementById('id_option-TOTAL_FORMS')
    let currentOptionsForms = document.getElementsByClassName('survey-option');
    let currentOptionsCounter = currentOptionsForms.length;

    if (currentOptionsCounter > 0) {
        currentOptionsCounter--;
        const optionElement = document.getElementById(`survey-option-form-${currentOptionsCounter}`)
        optionElement.remove();
        surveyOptionsTotalNewForms.setAttribute('value', currentOptionsCounter);
    }
    validateSurveyForm();
}
