function alertTimeout(wait){
    setTimeout(function(){
        $('#alert-placeholder').children('.alert:first-child').remove()
    }, wait);
}
alertTimeout(5000);