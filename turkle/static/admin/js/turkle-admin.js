$(function () {
  /* Hide/show group permissions on create/edit forms */
  if (!$('#id_custom_permissions').is(':checked')) {
    $('div.field-can_work_on_groups').hide();
    $('div.field-can_work_on_users').hide();
  }
  $('#id_custom_permissions').change(function() {
    $('div.field-can_work_on_groups').toggle();
    $('div.field-can_work_on_users').toggle();
  });
});
