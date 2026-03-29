let btnNotify = document.getElementById('submitAllNotification');
btnNotify.disabled = true;
function validateNotificationAllForm() {
    let messageFieldValue = document.getElementById('id_message').value;

    if (!messageFieldValue) {
        // document.getElementById("lblError").innerHTML = "Entre com um email valido para contato";

        btnNotify.disabled = true;
        return false; // Prevent form submission
    }

    // document.getElementById("lblError").innerHTML = "";
    btnNotify.disabled = false;
    return true; // Allow form submission
}

let messageField = document.getElementById('id_message');
messageField.addEventListener('change', validateNotificationAllForm);
