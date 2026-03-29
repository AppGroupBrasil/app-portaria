function addEntryForm() {
    if (event) {
        event.preventDefault();
    }

    const entryTotalNewForms = document.getElementById('id_entry-TOTAL_FORMS')
    const currentEntryForms = document.getElementsByClassName('entry-item');
    let currentEntryCounter = currentEntryForms.length;
    const emptyEntryElement = document.getElementById('entry-empty-form').cloneNode(true);
    emptyEntryElement.setAttribute('class', 'entry-item')
    emptyEntryElement.setAttribute('id', `entry-form-${currentEntryCounter}`)
    const regex = new RegExp('__prefix__', 'g');
    emptyEntryElement.innerHTML = emptyEntryElement.innerHTML.replace(regex, currentEntryCounter);

    entryTotalNewForms.setAttribute('value', currentEntryCounter + 1);

    const formEntryTarget = document.getElementById('entry-list');
    formEntryTarget.append(emptyEntryElement);
}

function removeEntryForm() {
    if (event) {
        event.preventDefault();
    }
    const entryTotalNewForms = document.getElementById('id_entry-TOTAL_FORMS')
    const currenEntryForms = document.getElementsByClassName('entry-item');
    let currentEntryCounter = currenEntryForms.length;

    if (currentEntryCounter > 0) {
        currentEntryCounter--;
        const entryElement = document.getElementById(`entry-form-${currentEntryCounter}`)
        entryElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);

        entryTotalNewForms.setAttribute('value', currentEntryCounter);
    }
}
