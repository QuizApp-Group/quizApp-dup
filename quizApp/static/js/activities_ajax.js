$(document).ready(function() {
  form_ajax("#update-activity-form", done_highlight, pre_callback_message);
  form_ajax("#remove-dataset-form", done_refresh);
  form_ajax("#add-dataset-form", done_refresh);
  form_ajax("#confirm-delete-activity-form", doneRemoveRow)
  form_ajax("#create-choice-form", done_add_row)
  form_ajax("#confirm-delete-choice-form", doneRemoveRow)
  form_ajax("#update-choice-form", done_update_row, pre_callback_message)
  form_ajax("#create-activity-form", done_redirect)

  $('#update-choice-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var row = button.parent().parent();
    var label = $(".choice-label", row);
    var action = row.data("update-action");

    var modal = $(this);

    modal.find('#update-choice-form').prop("action", action);
    modal.find('#update-choice-form').data("origin-row", row.attr("id"));
    modal.find('#delete-choice-form').prop("action", action);
    modal.find('.modal-title').text('Update choice ' + label.text());

    var tds = row.children();
    for(var i = 0; i < tds.length; i++) {
      $td = $(tds[i]);
      var input_name = $td.data("field-name");
      var $input = modal.find("input[name='" + input_name + "']");
      if($input.attr("type") == "checkbox") {
        $input.prop("checked", $td.text() == "True");
      } else {
        $input.val($td.text());
      }
    }
  })
  function done_update_row(data) {
    var originRow = $(document).find("#" + $(this).data("origin-row"));
    var inputs = $(this).find("input")
    for(var i = 0; i < inputs.length; i++) {
      var input_value = inputs[i].value;
      if(inputs[i].type == "checkbox") {
        if(input_value == "y") {
          input_value = "True";
        } else {
          input_value = "False";
        }
      }
      var field = originRow.find("[data-field-name='" + $(inputs[i]).attr("name") + "']");
      field.text(input_value);
    }
    done_highlight.call(this, data);
  }
  handleConfirmDeleteModal("activity");
  handleConfirmDeleteModal("choice");


  $("#update-question-datasets-table :checkbox").change(function() {
    var $row = $(this).closest("tr");
    var action = "";
    var method = "";
    var data = {};
    if(this.checked) {
      action = $row.data("create-action");
      method = "post";
      data = {"dataset_id": this.value}
    } else {
      action = $row.data("delete-action");
      method = "delete";
    }
    $.ajax({
      context: this,
      type: method,
      url: action,
      data: data,
      encode: true,
    })
    .done(function(data) {
      if(data.success) {
        var $tr = $(this).closest("tr");
        $tr.addClass("success");
        setTimeout(function() {
          $tr.removeClass("success");
        }, 1000);
      }
    })
  })
})
