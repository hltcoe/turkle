
/* Used on edit forms for batches and projects */
$(function () {
  document.addEventListener('dragenter', (e) => {
    e.preventDefault();
  });

  document.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  document.addEventListener('drop', (e) => {
    e.preventDefault();
    copyFileTextToFormField(e.dataTransfer.files[0]);
  });

  $('#id_template_file_upload').change(function (e) {
    copyFileTextToFormField(this.files[0]);

    // Resetting input value allows the user to upload same file twice
    $(this).val('');
  });

  function copyFileTextToFormField(f) {
    var reader = new FileReader();
    reader.onload = (function(theFile) {
      var fileContents = theFile.target.result;
      $('#id_html_template').val(fileContents);
      // force validation of template and temporarily change class to not make display green
      ParsleyConfig['successClass'] = 'invisible-success';
      $('#project_form').parsley().validate({group: 'html_template'});
      delete ParsleyConfig['successClass'];
    });
    reader.readAsText(f);

    // DOM ID created in custom_button_file_widget.html
    $('#id_template_file_upload_custom_text').text(f.name);

    // Update hidden form field
    $('#id_filename').val(f.name);
  }
});
