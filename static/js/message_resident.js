let blockMessageOption = document.getElementById('id_block');

blockMessageOption.addEventListener('change', () => {
    let block_id = blockMessageOption.value;
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

let btnNotify = document.getElementById('submitNotification');
btnNotify.disabled = true;
function validateNotificationForm() {
    let apartmentFieldValue = document.getElementById('id_apartment').value;
    let messageFieldValue = document.getElementById('id_message').value;



    if (!apartmentFieldValue || !messageFieldValue) {
        // document.getElementById("lblError").innerHTML = "Entre com um email valido para contato";

        btnNotify.disabled = true;
        return false; // Prevent form submission
    }

    // document.getElementById("lblError").innerHTML = "";
    btnNotify.disabled = false;
    return true; // Allow form submission
}

let apartmentField = document.getElementById('id_apartment');
apartmentField.addEventListener('change', validateNotificationForm);

let messageField = document.getElementById('id_message');
messageField.addEventListener('change', validateNotificationForm);
