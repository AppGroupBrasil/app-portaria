$(document).ready(function () {
    let searchForm = $('#search_form');
    let searchName = $('#search_checklist_name');
    let searchCreated = $('#search_checklist_created');

    $(searchName).on('change', function () {
        searchForm.submit();
    });

    $(searchCreated).on('change', function () {
        searchForm.submit();
    });
});

const addMoreTaskBtn = document.getElementById('add-task');

addMoreTaskBtn.addEventListener('click', () => {
    if (event) {
        event.preventDefault();
    }

    const taskTotalNewForms = document.getElementById('id_task-TOTAL_FORMS')
    const currentTaskForms = document.getElementsByClassName('task');
    let currentTaskCounter = currentTaskForms.length;
    const emptyTaskFormElement = document.getElementById('empty-task-form').cloneNode(true);
    emptyTaskFormElement.setAttribute('class', 'task')
    emptyTaskFormElement.setAttribute('id', `form-${currentTaskCounter}`)
    const regex = new RegExp('__prefix__', 'g');
    emptyTaskFormElement.innerHTML = emptyTaskFormElement.innerHTML.replace(regex, currentTaskCounter);


    taskTotalNewForms.setAttribute('value', currentTaskCounter + 1);

    const formTaskCopyTarget = document.getElementById('task-list');
    formTaskCopyTarget.append(emptyTaskFormElement);
});
