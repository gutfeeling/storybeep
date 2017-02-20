$(document).ready(function() {
  $("a").click(function(event) {
    event.preventDefault();

    $("#subscription-area").slideToggle();
    $("#login-area").slideToggle();
  });
});
