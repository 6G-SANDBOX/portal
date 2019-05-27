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

document.querySelector("html").classList.add('js');

configureButton(".input-file1", ".input-file-trigger1", ".file-return1");
configureButton(".input-file2", ".input-file-trigger2", ".file-return2");
