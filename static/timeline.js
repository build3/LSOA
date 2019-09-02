$(document).ready(function() {
    $("#id_students").select2({
        tokenSeparators: [',', '\n']
    });

    $('#filtering-submit').prop('disabled', true);

    $('#filterForm :input').on('change input', function() {
        $('#filtering-submit').removeAttr('disabled');
    });

    $('#filterForm :input').on('change input', function() {
        $('#filtering-submit').removeAttr('disabled');
    });

    $('#select-all-students').click(function() {
        $('#id_students').find('option').removeAttr('selected');
        $('#id_students').find('option').prop('selected', true);
        $('#id_students').select2();
        $('#filtering-submit').removeAttr('disabled');
    })
})