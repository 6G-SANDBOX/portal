function disableSliceList() {
  var checkBox = document.getElementById('slice_none');
  var sliceList = document.getElementById('sliceList');

  if (checkBox.checked == true){
    sliceList.removeAttribute("disabled");
  } else {
    sliceList.setAttribute("disabled", true);
  }
};

(function() {
    document.getElementById('navbar-createExperiment').classList.add('menuSelected');
    document.getElementById('navbar-home').classList.remove('menuSelected');
    document.getElementById('navbar-vnf').classList.remove('menuSelected');
})();

$(document).ready(
    function () {
        $('#checkBtn').click(function() {
            checked = $("input[name=test_cases]:checked").length;
            if(!checked) {
                alert("Please, select at least one Test Case");
                return false;
            }
        });
    }
);
