$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
      var csrftoken = $('meta[name=csrf-token]').attr('content')
        xhr.setRequestHeader("X-CSRFToken", csrftoken)
    }
  }
})

function form_ajax(selector, done_callback, pre_callback) {
  $(selector).submit(function(event) {
    if(pre_callback) {
      pre_callback(this);
    }
    event.preventDefault();

    if($(this).find("input[type=file]").length) {
      $.ajax({
        context: this,
        type: this.getAttribute("method"),
        url: this.getAttribute("action"),
        data: new FormData(this),
        processData: false,
        contentType: false,
        encode: true,
      })
      .done(function(data) {
          clear_errors(this);
          done_callback.call(this, data);
      })
    } else {
      $.ajax({
        context: this,
        type: this.getAttribute("method"),
        url: this.getAttribute("action"),
        data: $(this).serialize(),
        encode: true,
      })
      .done(function(data) {
          clear_errors(this);
          done_callback.call(this, data);
      })
    }
  });

}

// Some generic callbacks
function pre_callback_message(form) {
  // Put a message saying that the form is being saved
  var save_message = $(form).find("#submit-message");
  if(save_message.length) {
    save_message.remove();
  }
  var new_message = $("<span>",
      { "class": "text-primary", id: "submit-message" }).text("Saving...");
  $(form).append(new_message)
}

function done_redirect(data) {
  console.log(data);
  if(data.success) {
    window.location.href = data["next_url"]
  } else {
    render_errors(data.errors);
  }

}

function done_add_row(data) {
  console.log(data);
  if(data.success) {
    $(this).find("tbody").append(data.new_row);
  } else {
    render_errors(data.errors, data.prefix);
  }

}

function done_highlight(data) {
  console.log(data);
  var save_message = $(this).find("#submit-message");
  if(data.success) {
    save_message.text("Saved!");
    save_message.removeClass();
    save_message.addClass("text-success").delay(1000).
      fadeOut(500, function() {
        $(this).remove();
      })

    $(this).find(".error-block").remove();

    $(this).find(".form-group").
        removeClass("has-error").
        addClass("has-success").
        delay(1000).
        queue(function(next) {
            $(this).removeClass("has-success");
            next();
    })
  } else {
    save_message.text("Errors ocurred");
    save_message.removeClass();
    save_message.addClass("text-danger");
    render_errors(data.errors, data.prefix);
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

function clear_errors(form) {
    $(form).find(".error-block").remove();
    $(form).find(".has-error").removeClass("has-error");
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
        form.find(".error-block").remove();
        form.find(".has-error").removeClass("has-error");
        cleared_form_ids.push(form.attr("id"));
      }

      form_control.addClass("has-error");
      form_control.append(error_to_html(errors[id]));
    }
  }
}

function error_to_html(text) {
  return "<p class='help-block error-block'>" + text + "</p>";
}
