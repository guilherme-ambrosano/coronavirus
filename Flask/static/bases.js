
$(document).ready(
    function(){
        $.getJSON("/atualizar_springer", {},
        function(data){
            var celery = CeleryJS({
                url: data.Location,
                checkInterval: 3000,  // (default) milliseconds
                ajax: {               // (default) options passed to jQuery.ajax
                    cache: false,
                    dataType: 'json',
                }
            });
            celery.progress(function(task) {
                // pass
            });
            celery.done(function(task) {
                var texto = "";
                var tamanho = Object.keys(task.result).length;
                for (i = 0; i < tamanho; i++) {
                    resultado = task.result[i];
                    texto += '<div class="col-sm conteudo"><div class="row">';
                    texto += String(resultado.onlineDate);
                    texto += '</div><div class="row"><a href="';
                    texto += String(resultado.url[0].value);
                    texto += '" target="_blank">';
                    texto += String(resultado.title);
                    texto += '</a></div><div class="row">';
                    texto += String(resultado.authors);
                    texto += '</div></div><hr>';
                }
                $("div.springer").html(texto);
            });
            celery.always(function(task) {
                // pass
            });
        });
        $.getJSON("/atualizar_pubmed", {},
        function(data){
            var celery = CeleryJS({
                url: data.Location,
                checkInterval: 3000,  // (default) milliseconds
                ajax: {               // (default) options passed to jQuery.ajax
                    cache: false,
                    dataType: 'json',
                }
            });
            celery.progress(function(task) {
                // pass
            });
            celery.done(function(task) {
                var texto = "";
                var tamanho = Object.keys(task.result).length;
                for (i = 0; i < tamanho; i++) {
                    resultado = task.result[i];
                    texto += '<div class="col-sm conteudo"><div class="row">';
                    texto += String(resultado.onlineDate);
                    texto += '</div><div class="row"><a href="';
                    texto += String(resultado.link);
                    texto += '" target="_blank">';
                    texto += String(resultado.title);
                    texto += '</a></div><div class="row">';
                    texto += String(resultado.authors);
                    texto += '</div></div><hr>';
                }
                $("div.pubmed").html(texto);
            });
            celery.always(function(task) {
                // pass
            });
        });
});