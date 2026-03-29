let btnNotify = document.getElementById('submitBlockNotification');
btnNotify.disabled = true;
function validateNotificationBlockForm() {
    let blockFieldValue = document.getElementById('id_block').value;
    let messageFieldValue = document.getElementById('id_message').value;

    if (!blockFieldValue || !messageFieldValue) {
        // document.getElementById("lblError").innerHTML = "Entre com um email valido para contato";

        btnNotify.disabled = true;
        return false; // Prevent form submission
    }

    // document.getElementById("lblError").innerHTML = "";
    btnNotify.disabled = false;
    return true; // Allow form submission
}

let blockField = document.getElementById('id_block');
blockField.addEventListener('change', validateNotificationBlockForm);

let messageField = document.getElementById('id_message');
messageField.addEventListener('change', validateNotificationBlockForm);
