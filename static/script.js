$(function () {
  $(".load-icon-train").hide();
  $(".load-icon-test").hide();
  $(".table-training").hide();
  $(".table-testing").hide();
  $("#grafik").hide();
  console.log("ready!");
});

$("#train-form").on("submit", function (e) {
  e.preventDefault();
  var file_train = new FormData($("#train-form")[0]);
  $(".load-icon-train").show();
  $.ajax({
    data: file_train,
    contentType: false,
    cache: false,
    processData: false,
    // async: false,
    type: "post",
    url: "/training",
  }).done(function (data) {
    $(".load-icon-train").hide();
    $("#cth").html(data.cth);
    $("#cth_lower").html(data.cth_lower);
    $("#cth_punctual").html(data.cth_punctual);
    $("#cth_normalize").html(data.cth_normalize);
    $("#cth_stemmed").html(data.cth_stemmed);
    $("#cth_tokenized").html(data.cth_tokenized);

    $("#loss_train").html(data.loss_train);
    $("#accuracy_train").html(data.accuracy_train);
    $("#loss_val").html(data.loss_val);
    $("#accuracy_val").html(data.accuracy_val);

    $("#train-loss").attr("src", "../static/hasil/loss.png");
    $("#train-accuracy").attr("src", "../static/hasil/accuracy.png");

    $(".table-training").show();
    $("#grafik").show();
    console.log("data", data);
  });
});

$("#test-form").on("submit", function (e) {
  e.preventDefault();
  var file_test = new FormData($("#test-form")[0]);
  $(".load-icon-test").show();
  $.ajax({
    data: file_test,
    contentType: false,
    cache: false,
    processData: false,
    type: "post",
    url: "/testing",
  }).done(function (data) {
    $(".load-icon-test").hide();
    $(".table-testing").show();
    $("#accuracy-testing").html(data.accuracy);
    $("#accuracy-testing-image").attr("src", "../static/hasil/cm.png");

    //Foreach to table
    $.each(data.data_output, function (a, b) {
      $(".tr_narasi").append(
        "<tr><td>" +
          b.id +
          "</td><td>" +
          b.narasi +
          "</td><td>" +
          b.label +
          "</td><td>" +
          b.label_pred +
          "</td></tr>"
      );
    });
    $("#empTable").DataTable();
  });
});
