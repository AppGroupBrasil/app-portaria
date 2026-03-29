const addMoreBtn = document.getElementById('add-more');
const totalNewForms = document.getElementById('id_form-TOTAL_FORMS')

addMoreBtn.addEventListener('click', () => {
    if (event) {
        event.preventDefault();
    }

    const currentApartmentForms = document.getElementsByClassName('apartment');
    let currentFormCounter = currentApartmentForms.length;
    const emptyFormElement = document.getElementById('empty-form').cloneNode(true);
    emptyFormElement.setAttribute('class', 'apartment')
    emptyFormElement.setAttribute('id', `form-${currentFormCounter}`)
    emptyFormElement.setAttribute('value', document.getElementById('id_block').value);
    const regex = new RegExp('__prefix__', 'g');
    emptyFormElement.innerHTML = emptyFormElement.innerHTML.replace(regex, currentFormCounter);


    totalNewForms.setAttribute('value', currentFormCounter + 1);

    const formCopyTarget = document.getElementById('apartment-list');
    formCopyTarget.append(emptyFormElement);
});


function addFunctionForm() {
    if (event) {
        event.preventDefault();
    }
    const functionTotalNewForms = document.getElementById('id_function-TOTAL_FORMS')
    const currentFunctionForms = document.getElementsByClassName('function');
    let currentFunctionCounter = currentFunctionForms.length;
    const emptyFunctionElement = document.getElementById('function-empty-form').cloneNode(true);
    emptyFunctionElement.setAttribute('class', 'function')
    emptyFunctionElement.setAttribute('id', `function-form-${currentFunctionCounter}`)

    const regex = new RegExp('__prefix__', 'g');
    emptyFunctionElement.innerHTML = emptyFunctionElement.innerHTML.replace(regex, currentFunctionCounter);

    functionTotalNewForms.setAttribute('value', currentFunctionCounter + 1);

    const formFunctionTarget = document.getElementById('function-list');
    formFunctionTarget.append(emptyFunctionElement);

    let functionTitleElement = document.getElementById('id_function-' + currentFunctionCounter + '-title');
    functionTitleElement.addEventListener('input', () => {
        if (event) {
            event.preventDefault();
        }

        let itemSectionElement = document.getElementById('items_section');
        let imageSectionElement = document.getElementById('images_section');
        let fileSectionElement = document.getElementById('files_section');
        let videoSectionElement = document.getElementById('videos_section');
        if (functionTitleElement.value.length > 0) {

            itemSectionElement.setAttribute('class', '');
            imageSectionElement.setAttribute('class', '');
            fileSectionElement.setAttribute('class', '');
            videoSectionElement.setAttribute('class', '');
        } else {
            itemSectionElement.setAttribute('class', 'hidden');

            let itemsForms = document.getElementsByClassName('item-function');
            for (let x = itemsForms.length; x > -1; x--) {
                removeItemForm();
            }

            let imageSectionElement = document.getElementById('images_section');
            imageSectionElement.setAttribute('class', 'hidden');
            let imageForms = document.getElementsByClassName('image-item');
            for (let x = imageForms.length; x > -1; x--) {
                removeImageForm();
            }

            fileSectionElement.setAttribute('class', 'hidden');

            let fileForms = document.getElementsByClassName('file-item');
            for (let x = fileForms.length; x > -1; x--) {
                removeItemFileForm();
            }

            videoSectionElement.setAttribute('class', 'hidden');

            let videoForms = document.getElementsByClassName('video-item');
            for (let x = videoForms.length; x > -1; x--) {
                removeItemVideoForm();
            }
        }
    });
}

function removeFunctionForm() {
    if (event) {
        event.preventDefault();
    }
    const functionTotalNewForms = document.getElementById('id_function-TOTAL_FORMS')
    const currentFunctionForms = document.getElementsByClassName('function');
    let currentFunctionCounter = currentFunctionForms.length;

    if (currentFunctionCounter > 0) {
        currentFunctionCounter--;
        const functionElement = document.getElementById(`function-form-${currentFunctionCounter}`)
        functionElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);

        functionTotalNewForms.setAttribute('value', currentFunctionCounter);
    }
}

function addItemForm() {
    if (event) {
        event.preventDefault();
    }
    let currentFunctionForms = document.getElementsByClassName('function').length;
    if (currentFunctionForms > 0) {
        const functionTotalNewForms = document.getElementById('id_item-TOTAL_FORMS')
        const currentItemForms = document.getElementsByClassName('item-function');
        let currentItemCounter = currentItemForms.length;
        const emptyItemElement = document.getElementById('item-empty-form').cloneNode(true);
        emptyItemElement.setAttribute('class', 'item-function')
        emptyItemElement.setAttribute('id', `item-form-${currentItemCounter}`)
        const regex = new RegExp('__prefix__', 'g');
        emptyItemElement.innerHTML = emptyItemElement.innerHTML.replace(regex, currentItemCounter);

        functionTotalNewForms.setAttribute('value', currentItemCounter + 1);

        const formItemTarget = document.getElementById('items-list');
        formItemTarget.append(emptyItemElement);

        const currentFunctionForms = document.getElementsByClassName('function');
        let currentFunctionCounter = currentFunctionForms.length - 1;
        let fieldId = document.getElementById(`id_function-${currentFunctionCounter}-title`);
        $('#id_item-' + currentItemCounter + '-funcao').val(fieldId.value);

        let itemTitleElement = document.getElementById('id_item-' + currentItemCounter + '-title');
        itemTitleElement.addEventListener('input', () => {
            if (event) {
                event.preventDefault();
            }

            let imageSectionElement = document.getElementById('images_section');
            let fileSectionElement = document.getElementById('files_section');
            let videoSectionElement = document.getElementById('videos_section');

            if (itemTitleElement.value.length > 0) {

                imageSectionElement.setAttribute('class', '');
                fileSectionElement.setAttribute('class', '');
                videoSectionElement.setAttribute('class', '');
            } else {

                imageSectionElement.setAttribute('class', 'hidden');

                let imageForms = document.getElementsByClassName('image-item');
                for (let x = imageForms.length; x > -1; x--) {
                    removeImageForm();
                }

                fileSectionElement.setAttribute('class', 'hidden');

                let fileForms = document.getElementsByClassName('file-item');
                for (let x = fileForms.length; x > -1; x--) {
                    removeItemFileForm();
                }

                videoSectionElement.setAttribute('class', 'hidden');

                let videoForms = document.getElementsByClassName('video-item');
                for (let x = videoForms.length; x > -1; x--) {
                    removeItemVideoForm();
                }
            }
        });

    }
}

function removeItemForm() {
    if (event) {
        event.preventDefault();
    }
    let functionTotalNewForms = document.getElementById('id_item-TOTAL_FORMS')
    let currenItemForms = document.getElementsByClassName('item-function');
    let currentItemCounter = currenItemForms.length;

    if (currentItemCounter > 0) {
        currentItemCounter--;
        const itemElement = document.getElementById(`item-form-${currentItemCounter}`)
        itemElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);
        functionTotalNewForms.setAttribute('value', currentItemCounter);
    }
}

const blockSelect = document.getElementById('id_block');

blockSelect.addEventListener('change', () => {
    var block_id = blockSelect.value;
    console.log(block_id);
    if (block_id) {
        $('#id_apartment').prop('disabled', false).empty();
        $.ajax({
            url: '/get-apartments/',
            data: {block_id: block_id},
            success: function (response) {
                $('#id_apartment').empty();
                $('#id_apartment').append('<option value="">Selecione o apartamento</option>');
                $.each(response, function (key, value) {
                    $('#id_apartment').append('<option value="' + value.id + '">' + value.name + '</option>');
                });
            }
        });
    } else {
        // If no category is selected, disable the apartment select field and clear its options
        $('#id_apartment').prop('disabled', true).empty();
    }
});

const submitBtn = document.getElementById('submit');
submitBtn.disabled = true;

function validateForm() {
    let emailFieldValue = document.getElementById('id_email').value;
    let emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(;[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$/;

    if (!emailPattern.test(emailFieldValue)) {
        document.getElementById("lblError").innerHTML = "Entre com um email valido para contato";

        submitBtn.disabled = true;
        return false; // Prevent form submission
    }

    document.getElementById("lblError").innerHTML = "";
    submitBtn.disabled = false;
    return true; // Allow form submission
}

const emailField = document.getElementById('id_email');
emailField.addEventListener('change', validateForm);

function addImageForm() {
    if (event) {
        event.preventDefault();
    }
    let currentItemFunctionForms = document.getElementsByClassName('item-function').length;
    if (currentItemFunctionForms > 0) {
        const imageTotalNewForms = document.getElementById('id_image-TOTAL_FORMS')
        const currentImageForms = document.getElementsByClassName('image-item');
        let currentImageCounter = currentImageForms.length;
        const emptyImageElement = document.getElementById('image-empty-form').cloneNode(true);
        emptyImageElement.setAttribute('class', 'image-item')
        emptyImageElement.setAttribute('id', `image-form-${currentImageCounter}`)
        const regex = new RegExp('__prefix__', 'g');
        emptyImageElement.innerHTML = emptyImageElement.innerHTML.replace(regex, currentImageCounter);

        imageTotalNewForms.setAttribute('value', currentImageCounter + 1);

        const formImageTarget = document.getElementById('image-list');
        formImageTarget.append(emptyImageElement);

        const currentItemForms = document.getElementsByClassName('item-function');
        let currentItemCounter = currentItemForms.length - 1;
        let fieldId = document.getElementById(`id_item-${currentItemCounter}-title`);
        $('#id_image-' + currentImageCounter + '-item_name').val(fieldId.value);
    }
}

function removeImageForm() {
    if (event) {
        event.preventDefault();
    }
    const imageTotalNewForms = document.getElementById('id_image-TOTAL_FORMS')
    const currenImageForms = document.getElementsByClassName('image-item');
    let currentImageCounter = currenImageForms.length;

    if (currentImageCounter > 0) {
        currentImageCounter--;
        const imageElement = document.getElementById(`image-form-${currentImageCounter}`)
        imageElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);

        imageTotalNewForms.setAttribute('value', currentImageCounter);
    }
}

function addFileForm() {
    if (event) {
        event.preventDefault();
    }
    const filesTotalNewForms = document.getElementById('id_files-TOTAL_FORMS')
    const currentFileForms = document.getElementsByClassName('message-file');
    let currentFilesCounter = currentFileForms.length;
    const emptyFileElement = document.getElementById('file-empty-form').cloneNode(true);
    emptyFileElement.setAttribute('class', 'message-file')
    emptyFileElement.setAttribute('id', `file-form-${currentFilesCounter}`)
    const regex = new RegExp('__prefix__', 'g');
    emptyFileElement.innerHTML = emptyFileElement.innerHTML.replace(regex, currentFilesCounter);

    filesTotalNewForms.setAttribute('value', currentFilesCounter + 1);

    const formFileTarget = document.getElementById('files-list');
    formFileTarget.append(emptyFileElement);
}

function removeFileForm() {
    if (event) {
        event.preventDefault();
    }
    const fileTotalNewForms = document.getElementById('id_files-TOTAL_FORMS')
    const currenFileForms = document.getElementsByClassName('message-file');
    let currentFileCounter = currenFileForms.length;

    if (currentFileCounter > 0) {
        currentFileCounter--;
        const fileElement = document.getElementById(`file-form-${currentFileCounter}`)
        fileElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);

        fileTotalNewForms.setAttribute('value', currentFileCounter);
    }
}

function addItemFileForm() {
    if (event) {
        event.preventDefault();
    }

    let currentItemFunctionForms = document.getElementsByClassName('item-function').length;
    if (currentItemFunctionForms > 0) {
        let itemFilesTotalNewForms = document.getElementById('id_file-TOTAL_FORMS')
        let currentItemFileForms = document.getElementsByClassName('file-item');
        let currentItemFilesCounter = currentItemFileForms.length;
        const emptyItemFileElement = document.getElementById('item-file-empty-form').cloneNode(true);
        emptyItemFileElement.setAttribute('class', 'file-item')
        emptyItemFileElement.setAttribute('id', `item-file-form-${currentItemFilesCounter}`)
        const regex = new RegExp('__prefix__', 'g');
        emptyItemFileElement.innerHTML = emptyItemFileElement.innerHTML.replace(regex, currentItemFilesCounter);

        itemFilesTotalNewForms.setAttribute('value', currentItemFilesCounter + 1);

        const formFileTarget = document.getElementById('file-list');
        formFileTarget.append(emptyItemFileElement);

        const currentItemForms = document.getElementsByClassName('item-function');
        let currentItemCounter = currentItemForms.length - 1;
        let fieldId = document.getElementById(`id_item-${currentItemCounter}-title`);
        $('#id_file-' + currentItemFilesCounter + '-item_name').val(fieldId.value);
    }
}

function removeItemFileForm() {
    if (event) {
        event.preventDefault();
    }
    let fileTotalForms = document.getElementById('id_file-TOTAL_FORMS')
    const currenItemFileForms = document.getElementsByClassName('file-item');
    let currentItemFileCounter = currenItemFileForms.length;

    if (currentItemFileCounter > 0) {
        currentItemFileCounter--;
        const fileElement = document.getElementById(`item-file-form-${currentItemFileCounter}`)
        fileElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);

        fileTotalForms.setAttribute('value', currentItemFileCounter);
    }
}

function addItemVideoForm() {
    if (event) {
        event.preventDefault();
    }

    let currentItemFunctionForms = document.getElementsByClassName('item-function').length;
    if (currentItemFunctionForms > 0) {
        let itemVideosTotalNewForms = document.getElementById('id_video-TOTAL_FORMS')
        let currentItemVideoForms = document.getElementsByClassName('video-item');
        let currentItemVideosCounter = currentItemVideoForms.length;
        const emptyItemVideoElement = document.getElementById('item-video-empty-form').cloneNode(true);
        emptyItemVideoElement.setAttribute('class', 'video-item')
        emptyItemVideoElement.setAttribute('id', `item-video-form-${currentItemVideosCounter}`)
        const regex = new RegExp('__prefix__', 'g');
        emptyItemVideoElement.innerHTML = emptyItemVideoElement.innerHTML.replace(regex, currentItemVideosCounter);

        itemVideosTotalNewForms.setAttribute('value', currentItemVideosCounter + 1);

        const formVideoTarget = document.getElementById('video-list');
        formVideoTarget.append(emptyItemVideoElement);

        const currentItemForms = document.getElementsByClassName('item-function');
        let currentItemCounter = currentItemForms.length - 1;
        let fieldId = document.getElementById(`id_item-${currentItemCounter}-title`);
        $('#id_video-' + currentItemVideosCounter + '-item_name').val(fieldId.value);
    }
}

function removeItemVideoForm() {
    if (event) {
        event.preventDefault();
    }
    let videoTotalForms = document.getElementById('id_video-TOTAL_FORMS')
    const currenItemVideoForms = document.getElementsByClassName('video-item');
    let currentItemVideoCounter = currenItemVideoForms.length;

    if (currentItemVideoCounter > 0) {
        currentItemVideoCounter--;
        const videoElement = document.getElementById(`item-video-form-${currentItemVideoCounter}`)
        videoElement.remove();
        // emptyFunctionElement.setAttribute('value', document.getElementById('id_block').value);

        videoTotalForms.setAttribute('value', currentItemVideoCounter);
    }
}
