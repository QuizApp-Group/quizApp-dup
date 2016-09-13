$(document).ready(function() {
  form_ajax("#import-data-form", done_import_form, pre_callback_message);

  function done_import_form(data) {
      var save_message = $(this).find("#submit-message");
      var $error_container = $("#error-container");
      clear_errors(this);
      if(data.success) {
          $error_container.addClass("hidden")
          save_message.text("Data uploaded successfully!");
          save_message.removeClass();
          save_message.addClass("text-success");
          $(this).find(".error-block").remove();
      } else {
          $error_container.removeClass("hidden")
          $error_container.html("Errors ocurred: <br>" + data.errors);
          save_message.remove()
      }
  }
});
