// Return a helper with preserved width of cells
var fixHelper = function(e, ui) {
  ui.children().each(function() {
    $(this).width($(this).width());
  }); 
  return ui; 
};

$(".sortable-table").sortable({ 
  connectWith: ".connected-sortable",
  helper: fixHelper, 
  handle: '.handle',
  items: "> tbody > tr", 
  receive: function(ev, ui) {
    ui.item.parent().find('tbody').append(ui.item);
    var table = ui.item.parent().parent();
    var action = table.data("action");
    var method = table.data("method");
    $.ajax({
      context: ui.item,
      type: method,
      url: action,
      data: "dataset_id=" + ui.item.data("dataset-id"),
      encode: true,
    })
    .done(function(data) {
      var rowClass = "success";
      if(!data.success) {
        rowClass = "danger";
      }
      this.addClass(rowClass).delay(1000).queue(function() {
        $(this).removeClass(rowClass).dequeue();
      })
    });
  }
})
