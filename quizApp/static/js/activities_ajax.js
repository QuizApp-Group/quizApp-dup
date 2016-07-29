$(document).ready(function() {
  form_ajax("#update-activity-form", done_refresh);
  form_ajax("#remove-dataset-form", done_refresh);
  form_ajax("#add-dataset-form", done_refresh);
  form_ajax("#delete-activity-form", done_redirect)
  form_ajax("#create-choice-form", done_refresh)
  form_ajax("#delete-choice-form", done_refresh)
  form_ajax("#update-choice-form", done_refresh)
  form_ajax("#create-activity-form", done_redirect)

  $('#update-choice-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var row = button.parent().parent();
    var label = $(".choice-label", row);
    var choice = $(".choice-choice", row);
    var correct = $(".choice-correct", row).text() == "True";
    var action = row.data("update-action");

    var modal = $(this);

    modal.find('#update-choice-form').prop("action", action);
    modal.find('#delete-choice-form').prop("action", action);
    modal.find('.modal-title').text('Update choice ' + label.text());
    modal.find('#update-label').val(label.text());
    modal.find('#update-choice').val(choice.text());
    modal.find('#update-correct').prop("checked", correct);
  })
})
