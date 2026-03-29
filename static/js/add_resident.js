let blockAddResident = document.getElementById('id_block');

blockAddResident.addEventListener('change', () => {
    let block_id = blockAddResident.value;
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
                let emailResidentFieldValue = document.getElementById('id_email').value;
                if (emailResidentFieldValue) {
                    submitResidentBtn.disabled = false;
                }
            }
        });
    } else {
        // If no category is selected, disable the apartment select field and clear its options
        $('#id_apartment').prop('disabled', true).empty();
    }
});

const submitResidentBtn = document.getElementById('submitResident');
submitResidentBtn.disabled = true;
function validateResidentForm() {
    let emailResidentFieldValue = document.getElementById('id_email').value;
    let emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(;[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*$/;

    if (!emailPattern.test(emailResidentFieldValue)) {
        document.getElementById("lblError").innerHTML = "Entre com um email valido para contato";

        submitResidentBtn.disabled = true;
        return false; // Prevent form submission
    }

    document.getElementById("lblError").innerHTML = "";
    submitResidentBtn.disabled = false;
    return true; // Allow form submission
}

const emailResidentField = document.getElementById('id_email');
emailResidentField.addEventListener('change', validateResidentForm);
