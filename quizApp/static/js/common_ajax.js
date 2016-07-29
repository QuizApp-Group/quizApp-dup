$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
      var csrftoken = $('meta[name=csrf-token]').attr('content')
        xhr.setRequestHeader("X-CSRFToken", csrftoken)
    }
  }
})

function form_ajax(selector, done_callback) {
  $(selector).submit(function(event) {
    event.preventDefault();

    if($(this).find("input[type=file]")) {
      $.ajax({
        type: this.getAttribute("method"),
        url: this.getAttribute("action"),
        data: new FormData(this),
        processData: false,
        contentType: false,
        encode: true,
      })
      .done(done_callback);
    } else {
      $.ajax({
        type: this.getAttribute("method"),
        url: this.getAttribute("action"),
        data: $(this).serialize(),
        encode: true,
      })
      .done(done_callback);
    }
  });

}

// Some generic callbacks

function done_redirect(data) {
  console.log(data);
  if(data.success) {
    window.location.href = data["next_url"]
  } else {
    render_errors(data.errors);
  }

}

function done_refresh(data) {
  console.log(data);
  if(data.success) {
    window.location.reload();
  } else {
    render_errors(data.errors, data.prefix);
  }
}

function render_errors(errors, prefix) {
  var cleared_form_ids = [];
  if(!prefix) {
    prefix = ""
  }
  for(var id in errors) {
    if(errors.hasOwnProperty(id)) {
      var form_control = $("#" + prefix + id).parents(".form-group");
      var form = form_control.parents("form");

      if($.inArray(form.attr("id"), cleared_form_ids) == -1) {
        form.find(".help-block").remove();
        form.find(".has-error").removeClass("has-error");
        cleared_form_ids.push(form.attr("id"));
      }

      form_control.addClass("has-error");
      form_control.append(error_to_html(errors[id]));
    }
  }
}

function error_to_html(text) {
  return "<p class='help-block'>" + text + "</p>";
}
