(function() {
  document.getElementById('navbar-createExperiment').classList.add('menuSelected');
  document.getElementById('navbar-home').classList.remove('menuSelected');
  document.getElementById('navbar-vnf').classList.remove('menuSelected');
})();

$(document).ready(
  function() {
    $('#checkBtn').click(function() {
      checked = $("input[name=testCases]:checked").length;
      if (!checked) {
        alert("Please, select at least one Test Case");
        return false;
      }
    });
  }
);

function addVNFs(actual, target, vnfs, vnfsId) {
  for (i = actual + 1; i <= target; i++) {
    newItemHTML = '<tr><td class="table-cell-divisor-right"><center>' + i + '</center></td><td class="table-cell-divisor-right"><select class="vnf InputBox form-control" name="VNF' + i + '">'
    for (j = 0; j < vnfs.length; j++) {
      newItemHTML = newItemHTML + '<option value="' + vnfsId[j] + '">' + vnfs[j] + '</option>';
    }
    newItemHTML = newItemHTML + '</select></td><td><select class="form-control" name="location' + i + '"><option value="Data Network" selected>Data Network</option><option value="Edge">Edge</option></select></td></tr>'
    $("table#vnf tr").last().after(newItemHTML);
  }
}

function removeVNFs(target) {
  if (target >= 0) {
    $('.vnf').slice(target).parent().parent().remove();
  }
}

function disableSliceList() {
  var checkBox = document.getElementById('sliceNone');
  var sliceList = document.getElementById('sliceList');

  if (checkBox.checked == true) {
    sliceList.removeAttribute("disabled");
  } else {
    sliceList.setAttribute("disabled", true);
  }
};