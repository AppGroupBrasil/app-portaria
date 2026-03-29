let blockAddResident = document.getElementById('id_block');
let apartmentOptions = document.getElementById('apartment-options');

// Function to handle the change event of the "All" checkbox
function handleAllCheckboxChange(event) {
    if (event.target.value === 'ALL') {
        let allChecked = event.target.checked;
        let apartmentCheckboxes = apartmentOptions.querySelectorAll('input[type="checkbox"]');

        apartmentCheckboxes.forEach(function (checkbox) {
            if (checkbox.value !== "ALL") {
                checkbox.checked = allChecked;
                if (allChecked) {
                    checkbox.disabled = true;
                } else {
                    checkbox.disabled = false;
                }

            }

        });
    }

    let submitBtn = document.getElementById('submitReview');
    let apartmentCheckboxes = apartmentOptions.querySelectorAll('input[type="checkbox"][name="apartments"]');
    let atLeastOneChecked = Array.from(apartmentCheckboxes).some(checkbox => checkbox.checked);
    submitBtn.disabled = !atLeastOneChecked;
}

// Add event listener for "All" checkbox outside the AJAX request using event delegation
apartmentOptions.addEventListener('change', handleAllCheckboxChange);

blockAddResident.addEventListener('change', () => {

    let block_id = blockAddResident.value;
    document.getElementById('apartment-options').setAttribute('class', '');
    console.log(block_id);
    if (block_id && block_id != 'ALL') {
        let submitBtn = document.getElementById('submitReview');
        submitBtn.disabled = true;
        $('#id_apartment').prop('disabled', false).empty();
        $.ajax({
            url: '/get-apartments/',
            data: { block_id: block_id },
            success: function (response) {
                apartmentOptions.innerHTML = '';

                apartmentOptions.appendChild(document.createElement('br'));
                let apartmentLabel = document.createElement('label');
                apartmentLabel.textContent = 'APARTAMENTO PARA ENVIAR';

                // Add the "all" option as the first checkbox
                let allCheckbox = document.createElement('input');
                allCheckbox.type = 'checkbox';
                allCheckbox.name = 'apartments'; // Use this name to group selected apartments
                allCheckbox.value = 'ALL';
                allCheckbox.id = 'apartment_all';

                let allLabel = document.createElement('label');
                allLabel.setAttribute('for', 'apartment_all');
                allLabel.textContent = 'Todos';

                apartmentOptions.appendChild(apartmentLabel);
                apartmentOptions.appendChild(document.createElement('br'));
                apartmentOptions.appendChild(document.createElement('br'));
                apartmentOptions.appendChild(allCheckbox);
                apartmentOptions.appendChild(allLabel);
                apartmentOptions.appendChild(document.createElement('br'));

                $.each(response, function (key, value) {
                    let checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.name = 'apartments';
                    checkbox.value = value.id;
                    checkbox.id = 'apartment_' + value.id;

                    let label = document.createElement('label');
                    label.setAttribute('for', 'apartment_' + value.id);
                    label.textContent = value.name;

                    apartmentOptions.appendChild(checkbox);
                    apartmentOptions.appendChild(label);
                    apartmentOptions.appendChild(document.createElement('br'));
                });
            }
        });

    } else {
        // If no category is selected, disable the apartment select field and clear its options
        if (block_id || document.getElementById('id_send_to').value === "FUNCIONÁRIOS") {
            let submitBtn = document.getElementById('submitReview');
            submitBtn.disabled = false;
        }

        apartmentOptions.innerHTML = '';
    }
});