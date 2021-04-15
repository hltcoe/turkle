$(function () {
  /* Hide/show group permissions on create/edit forms */
  if (!$('#id_custom_permissions').is(':checked')) {
    $('div.field-can_work_on_groups').hide();
  }
  $('#id_custom_permissions').change(function() {
    $('div.field-can_work_on_groups').toggle();
  });
});
