$(document).ready(function() {
  $("span a").click(function(event) {
    event.preventDefault();

    $("#subscription-area").slideToggle();
    $("#login-area").slideToggle();
  });
});
