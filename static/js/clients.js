$(document).ready(function () {
    let searchForm = $('#search_form');
    let searchName = $('#search_condominium_name');
    let searchRef = $('#search_condominium_ref');
    let searchEmail = $('#search_condominium_email');
    let searchStatus = $('#search_status_filter');

    $(searchName).on('change', function () {
        searchForm.submit();
    });

    $(searchRef).on('change', function () {
        searchForm.submit();
    });

    $(searchEmail).on('change', function () {
        searchForm.submit();
    });

    $(searchStatus).on('change', function () {
        searchForm.submit();
    });
});
