// Mapa (amcharts)

var mapa = am4core.create("mapa", am4maps.MapChart);
mapa.geodata = am4geodata_worldLow;
mapa.projection = new am4maps.projections.Miller();
var polygonSeries = mapa.series.push(new am4maps.MapPolygonSeries());
polygonSeries.useGeodata = true;

var polygonTemplate = polygonSeries.mapPolygons.template;
polygonTemplate.events.on("hit", function(ev) {
    mapa.zoomToMapObject(ev.target);
});
polygonSeries.heatRules.push({
    "property": "fill",
    "target": polygonTemplate,
    "min": am4core.color("#ffffff"),
    "max": am4core.color("#AAAA00"),
    "logarithmic": true
});

polygonSeries.data = df_paises; // dataframe passado pelo jinja

polygonTemplate.tooltipText = "{name}: {value}";
polygonTemplate.stroke = am4core.color("#AAAAAA");
polygonTemplate.strokeWidth = 1;

// Atualizando os dados (celery)

var df_pais;
function update_df() {
    var selec=$("select#pais").val();
    $.getJSON("/update_df",{
        pais: selec,
    }, function(data){
        var celery = CeleryJS({
            url: data.Location,
            checkInterval: 3000,
            ajax: {
                cache: false,
                dataType: 'json',
            }
        });
        celery.progress(function(task) {
            // pass
        });
        celery.done(function(task) {
            console.log(task.result);
        });
        celery.always(function(task) {
            // pass
        });
    });
}
