

function addBlockedForm() {
    if (event) {
        event.preventDefault();
    }

    let blockedTotalNewForms = document.getElementById('id_blocked-TOTAL_FORMS')
    let currentBlockedForms = document.getElementsByClassName('blocked-day');
    let currentBlockedCounter = currentBlockedForms.length;

    const emptyBlockedElement = document.getElementById('blocked-empty-form').cloneNode(true);
    emptyBlockedElement.setAttribute('class', 'blocked-day')
    emptyBlockedElement.setAttribute('id', `blocked-form-${currentBlockedCounter}`)
    const regex = new RegExp('__prefix__', 'g');
    emptyBlockedElement.innerHTML = emptyBlockedElement.innerHTML.replace(regex, currentBlockedCounter);

    blockedTotalNewForms.setAttribute('value', currentBlockedCounter + 1);

    const formBlockedTarget = document.getElementById('blocked-list');
    formBlockedTarget.append(emptyBlockedElement);
}

function removeBlockedForm() {
    if (event) {
        event.preventDefault();
    }
    let blockedTotalNewForms = document.getElementById('id_blocked-TOTAL_FORMS')
    let currentBlockedForms = document.getElementsByClassName('blocked-day');
    let currentBlockedCounter = currentBlockedForms.length;

    if (currentBlockedCounter > 0) {
        currentBlockedCounter--;
        const blockedElement = document.getElementById(`blocked-form-${currentBlockedCounter}`)
        blockedElement.remove();
        blockedTotalNewForms.setAttribute('value', currentBlockedCounter);
    }
}
