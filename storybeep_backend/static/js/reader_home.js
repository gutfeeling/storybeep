$(document).ready(function() {
  $(':checkbox:checked').prop('checked',false);
  $("input[type='checkbox']").change(function() {
    if ($("input[type='checkbox']:checked").length == 0) {
      $("#delete-icon").hide();
    } else if ($("input[type='checkbox']:checked").length == 1) {
      $("#delete-icon").show();
    }
    if (this.checked) {
      $(this).parents(".story-container").css("background-color", "#FFFFCC");
    } else {
      $(this).parents(".story-container").css("background-color", "#FFFFFF");
    }
  });
  $("#delete-icon").click(function( event ) {
    event.preventDefault();
    $("input[type='checkbox']:checked").each(function() {
      var story_id_string = $(this).attr("id");
        url = "/stop-tracking/" + story_id_string + "/";
        $.ajax({
          async: false,
          type: 'GET',
          url: url,
        });
    });
    location.reload();
  });
});
