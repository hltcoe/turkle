$(function () {
  /* Hide/show group permissions on create/edit forms */
  if (!$('#id_custom_permissions').is(':checked')) {
    $('div.field-worker_permissions').hide();
  }
  $('#id_custom_permissions').change(function() {
    $('div.field-worker_permissions').toggle();
  });
});