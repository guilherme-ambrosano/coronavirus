console.log(df);

function update_df() {
    var selec=$("select#pais").val();
    $.getJSON("/update_df",{
        pais: selec,
    }, function(data){
        console.log(data);
    });
}