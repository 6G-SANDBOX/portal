function configureButton(input, trigger, ret)
{
    var fileInput = document.querySelector( input ),
        button = document.querySelector( trigger ),
        the_return = document.querySelector( ret);

    button.addEventListener( "click", function(event) {
        fileInput.focus();
        return false;
    });

    fileInput.addEventListener("change", function( event ) {
        the_return.innerHTML = this.value.split("\\")[2];
    });
}

configureButton(".input-file1", ".input-file-trigger1", ".file-return1");
configureButton(".input-file2", ".input-file-trigger2", ".file-return2");
configureButton(".input-file3", ".input-file-trigger3", ".file-return3");
configureButton(".input-file4", ".input-file-trigger4", ".file-return4");