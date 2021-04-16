$(function () {
  /* On Add/Change forms, use value of 'Custom Permissions' checkbox to hide/show
     widgets for selecting Groups and Users that should be assigned 'can_work_on'
     permissions for the model instance being added/changed */
  if (!$('#id_custom_permissions').is(':checked')) {
    $('div.field-can_work_on_groups').hide();
    $('div.field-can_work_on_users').hide();
  }
  $('#id_custom_permissions').change(function() {
    $('div.field-can_work_on_groups').toggle();
    $('div.field-can_work_on_users').toggle();
  });
});
