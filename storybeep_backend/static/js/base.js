$(function(){
    var navbar = $('.navbar-default');
    $(window).scroll(function(){
        if($(window).scrollTop() <= 40){
       		navbar.css('box-shadow', 'none');
          navbar.css('border', 'none');
        } else {
          navbar.css('box-shadow', '0 1px 5px rgba(0,0,0,0.1)');
          navbar.css('border-bottom', '1px solid rgb(220, 224, 224)');
        }
    });
})
