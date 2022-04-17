
/* Submit letter */

$('#letter-form').submit(function(e) {
  var data = $("#letter-form").serialize();
  
  /* Empty input */
  $('#letter-form input').val('');
  
  $.ajax({
    type: "POST",
    url: '',
    data: data,
    success: function(data) {
      /* Refresh if finished */
      if (data.finished) {
        location.reload();
      }
      else {
        /* Update current */
        $('#current').text(data.current);
        
        /* Update errors */
        $('#real_errors').html(
          'Errors (' + data.real_errors.length + '/6): ' +

          '<span class="text-danger spaced">' + data.real_errors + '</span>');
          
        /* Update drawing */
        updateDrawing(data.real_errors);
      }
    }
  });
  e.preventDefault();
});


function updateDrawing(real_errors) {
  $('#hangman-drawing').children().slice(0, real_errors.length).show();
}













