$(document).ready(function () {
    let searchForm = $('#search_form');
    let searchName = $('#search_informative_name');
    let searchCreated = $('#search_informative_created');

    $(searchName).on('change', function () {
        searchForm.submit();
    });

    $(searchCreated).on('change', function () {
        searchForm.submit();
    });
});

function deleteFunctionFromInformative() {

    let functionTotalNewForms = document.getElementById('id_function-TOTAL_FORMS')
    const currentFunctionForms = document.getElementsByClassName('function');
    let currentFunctionCounter = currentFunctionForms.length;

    if (currentFunctionCounter > 0) {
        currentFunctionCounter--;

        const function_id = document.getElementById(`id_function-${currentFunctionCounter}-id`).value;
        const function_title = document.getElementById(`id_function-${currentFunctionCounter}-title`).value;
        if (function_id) {
            $.ajax({
                url: '/remove-function/',
                data: {function_id: function_id},
                success: function (response) {

                    const functionElement = document.getElementById(`function-form-${currentFunctionCounter}`)
                    functionElement.remove();
                    functionTotalNewForms.setAttribute('value', currentFunctionCounter);
                    deleteItemFormByFunctionTitle(function_title)
                }

            });
        } else {
            removeFunctionForm();
        }
    }
}

function deleteItemFromInformative() {

    let functionItemTotalNewForms = document.getElementById('id_item-TOTAL_FORMS')
    let currenItemForms = document.getElementsByClassName('item-function');
    let currentItemCounter = currenItemForms.length;

    if (currentItemCounter > 0) {
        currentItemCounter--;

        const item_id = document.getElementById(`id_item-${currentItemCounter}-id`).value;
        const item_title = document.getElementById(`id_item-${currentItemCounter}-title`).value;
        if (item_id) {
            $.ajax({
                url: '/remove-item/',
                data: {item_id: item_id},
                success: function (response) {

                    const itemElement = document.getElementById(`item-form-${currentItemCounter}`)
                    itemElement.remove();
                    functionItemTotalNewForms.setAttribute('value', currentItemCounter);
                    deleteElementFormByClassAndItemTitle('image-item', item_title, 'image');
                    deleteElementFormByClassAndItemTitle('file-item', item_title, 'file');
                }

            });
        }
    }
}

function deleteImageFromInformative() {

    let imageTotalForms = document.getElementById('id_image-TOTAL_FORMS')
    const currenItemImageForms = document.getElementsByClassName('image-item');
    let currentItemImageCounter = currenItemImageForms.length;

    if (currentItemImageCounter > 0) {
        currentItemImageCounter--;

        const image_id = document.getElementById(`id_image-${currentItemImageCounter}-id`).value;

        if (image_id) {
            $.ajax({
                url: '/remove-image/',
                data: {image_id: image_id},
                success: function (response) {
                    const imageElement = document.getElementById(`image-form-${currentItemImageCounter}`)
                    imageElement.remove();
                    imageTotalForms.setAttribute('value', currentItemImageCounter);
                }
            });
        } else {
            removeImageForm();
        }
    }
}

function deleteFileFromInformative() {

    let fileTotalForms = document.getElementById('id_file-TOTAL_FORMS')
    const currenItemFileForms = document.getElementsByClassName('file-item');
    let currentItemFileCounter = currenItemFileForms.length;

    if (currentItemFileCounter > 0) {
        currentItemFileCounter--;

        const file_id = document.getElementById(`id_file-${currentItemFileCounter}-id`).value;

        if (file_id) {
            $.ajax({
                url: '/remove-file/',
                data: {file_id: file_id},
                success: function (response) {
                    const fileElement = document.getElementById(`item-file-form-${currentItemFileCounter}`)
                    fileElement.remove();
                    fileTotalForms.setAttribute('value', currentItemFileCounter);
                },
                error: function (response) {

                }
            });
        } else {
            removeItemFileForm();
        }
    }
}

function deleteVideoFromInformative() {

    let videoTotalForms = document.getElementById('id_video-TOTAL_FORMS')
    const currenItemVideoForms = document.getElementsByClassName('video-item');
    let currentItemVideoCounter = currenItemVideoForms.length;

    if (currentItemVideoCounter > 0) {
        currentItemVideoCounter--;

        const video_id = document.getElementById(`id_video-${currentItemVideoCounter}-id`).value;

        if (video_id) {
            $.ajax({
                url: '/remove-video/',
                data: {video_id: video_id},
                success: function (response) {
                    const videoElement = document.getElementById(`item-video-form-${currentItemVideoCounter}`)
                    videoElement.remove();
                    videoTotalForms.setAttribute('value', currentItemVideoCounter);
                },
                error: function (response) {

                }
            });
        } else {
            removeItemVideoForm();
        }
    }
}

function deleteElementFormByClassAndItemTitle(className, title, field) {
    const elements = document.getElementsByClassName(className);

    for (let i = elements.length - 1; i >= 0; i--) {
        const itemElement = elements[i];
        const itemTitleElement = itemElement.querySelector(`#div_id_${field}-${i}-item_name input`);
        const itemTitle = itemTitleElement.value;

        if (itemTitle === title) {
            itemElement.remove();
        }
    }
}

function deleteItemFormByFunctionTitle(title) {
    const elements = document.getElementsByClassName('item-function');

    for (let i = elements.length - 1; i >= 0; i--) {
        const itemElement = elements[i];
        const functionTitleElement = itemElement.querySelector(`#div_id_item-${i}-funcao input`);
        const functionTitle = functionTitleElement.value;

        if (functionTitle === title) {

            itemElement.remove();

            let item_title = itemElement.querySelector(`#div_id_item-${i}-title input`).value;
            deleteElementFormByClassAndItemTitle('image-item', item_title, 'image');
            deleteElementFormByClassAndItemTitle('file-item', item_title, 'file');
        }
    }
}
