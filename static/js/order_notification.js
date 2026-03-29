let blockOption = document.getElementById('id_block');
let aptOption = document.getElementById('id_apartment');

blockOption.addEventListener('change', () => {
    let block_id = blockOption.value;

    if (block_id === 'all' || !block_id) {
        $('#id_apartment').prop('disabled', true).empty();
        if (ALLOW_ALL_OPTION) {
            $('#id_apartment').append('<option value="all">TODOS</option>');
        } else {
            $('#id_apartment').append('<option value="">Selecione o apartamento</option>');
        }
        $('#id_addressee').prop('disabled', true).empty()
            .append('<option value="all">TODOS</option>');
    } else {
        $('#id_apartment').prop('disabled', false).empty();
        $.ajax({
            url: '/get-apartments/',
            data: {block_id: block_id},
            success: function (response) {
                $('#id_apartment').empty();
                $('#id_apartment').append('<option value="">Selecione o apartamento</option>');
                if (ALLOW_ALL_OPTION) {
                    $('#id_apartment').append('<option value="all">TODOS</option>');
                }
                $.each(response, function (key, value) {
                    $('#id_apartment').append('<option value="' + value.id + '">' + value.name + '</option>');
                });
            }
        });
    }
});

aptOption.addEventListener('change', () => {
    let apartment_id = aptOption.value;

    if (apartment_id === 'all' || !apartment_id) {
        $('#id_addressee').prop('disabled', true).empty()
            .append('<option value="all">TODOS</option>');
    } else {
        $('#id_addressee').prop('disabled', false).empty();
        $.ajax({
            url: '/get-residents/',
            data: {apartment_id: apartment_id},
            success: function (response) {
                $('#id_addressee').empty();
                $('#id_addressee').append('<option value="">Selecione o morador</option>');
                $('#id_addressee').append('<option value="all">TODOS</option>');
                $.each(response, function (key, value) {
                    $('#id_addressee').append('<option value="' + value.id + '">' + value.name + '</option>');
                });
            }
        });
    }
});

$(document).ready(function() {
    if (blockOption.value === 'all' || !blockOption.value) {
        $('#id_apartment').prop('disabled', true).empty()
            .append('<option value="all">TODOS</option>');
        $('#id_addressee').prop('disabled', true).empty()
            .append('<option value="all">TODOS</option>');
    }

    if (aptOption.value === 'all' || !aptOption.value) {
        $('#id_addressee').prop('disabled', true).empty()
            .append('<option value="all">TODOS</option>');
    }
});
