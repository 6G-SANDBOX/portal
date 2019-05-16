document.querySelector("html").classList.add('js');

var fileInput1  = document.querySelector( ".input-file1" ),
    button1     = document.querySelector( ".input-file-trigger1" ),
    the_return1 = document.querySelector( ".file-return1" );

button1.addEventListener( "click", function( event ) {
   fileInput1.focus();
   return false;
});

fileInput1.addEventListener( "change", function( event ) {
    the_return1.innerHTML = this.value.split("\\")[2];
});

///////////////

var fileInput2  = document.querySelector( ".input-file2" ),
    button2     = document.querySelector( ".input-file-trigger2" ),
    the_return2 = document.querySelector( ".file-return2" );

button2.addEventListener( "click", function( event ) {
   fileInput2.focus();
   return false;
});

fileInput2.addEventListener( "change", function( event ) {
    the_return2.innerHTML = this.value.split("\\")[2];
});

///////////////

var fileInput3  = document.querySelector( ".input-file3" ),
    button3     = document.querySelector( ".input-file-trigger3" ),
    the_return3 = document.querySelector( ".file-return3" );

button3.addEventListener( "click", function( event ) {
   fileInput3.focus();
   return false;
});

fileInput3.addEventListener( "change", function( event ) {
    the_return3.innerHTML = this.value.split("\\")[2];
});

///////////////

var fileInput4  = document.querySelector( ".input-file4" ),
    button4     = document.querySelector( ".input-file-trigger4" ),
    the_return4 = document.querySelector( ".file-return4" );

button4.addEventListener( "click", function( event ) {
   fileInput4.focus();
   return false;
});

fileInput4.addEventListener( "change", function( event ) {
    the_return4.innerHTML = this.value.split("\\")[2];
});