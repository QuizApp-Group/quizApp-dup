$(document).ready(function() {
  form_ajax("#create-dataset-form", done_refresh);
  form_ajax("#update-dataset-form", done_refresh);
  form_ajax("#delete-dataset-form", done_redirect);
  form_ajax("#delete-media-item-form", done_refresh);
  form_ajax("#create-media-item-form", done_refresh);

  $('#preview-media-item-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var row = button.parent().parent();
    var name = $(".media-item-name", row).text()
    var filename = $(".media-item-filename", row).text()
    var read_url = $(button).data("read-url");
    var delete_url = $(button).data("delete-url");

    var modal = $(this);
    modal.find('.modal-title').text('Preview media item ' + name);
    modal.find('#delete-media-item-form').attr("action", delete_url)

    $.ajax({
      type: "get",
      url: read_url,
      encode: true,
    })
    .done(function(data) {
      console.log(data);
      $('#preview-media-item-modal .modal-body').html(data);
    });

  })
})
