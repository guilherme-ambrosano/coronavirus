# TODO: Embelezar o site

from datetime import date, timedelta

from flask import Flask, render_template, request
from flask import flash, session
from flask import jsonify, url_for
from flask_session import Session
from tempfile import mkdtemp
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

import os

from graficos import atualizar_dados,\
    atualizar_grafico_aumento, atualizar_grafico_expon, atualizar_grafico_mapa
from bases import atualizar_pubmed, atualizar_springer

from datetime import date, datetime, timedelta

from celery_app import iniciar_celery

# Criando o aplicativo Flask
app = Flask("__name__")

# Configurando o Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = iniciar_celery(app)

@celery.task(name="atualizar_dados_async")
def atualizar_dados_async(pais=None):
    paises, df = atualizar_dados(pais)
    return paises, df

@celery.task(name="atualizar_springer_async", bind=True)
def atualizar_springer_async(self):
    print("Atualizando dados da springer...")
    self.records = atualizar_springer()
    return {'current': 100, 'total': 100, 'status': 'Concluído',
            'result': self.records}

@celery.task(name="atualizar_pubmed_async", bind=True)
def atualizar_pubmed_async(self):
    self.records = atualizar_pubmed()
    return {'current': 100, 'total': 100, 'status': 'Concluído',
            'result': self.records}

# Configurando o banco de dados
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Colocar o caminho pra database nas variáveis do ambiente (e.g.: DATABASE_URL = /database.db)
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
# db = SQLAlchemy(app)

# Configurando sessão Flask
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/update_df")
def update():
    try:
        pais = request.args.get("pais")
        if pais is not None:
            pais = pais.replace(" ", "_")
            _, df = atualizar_dados_async.delay()
            df_pais = df.loc[df["countriesAndTerritories"] == pais].to_dict(orient="list")
            del df_pais["Unnamed: 0"]
            return jsonify(df_pais)
        else:
            return None
    except Exception as e:
        return str(e)


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = atualizar_springer_async.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = { 
            'task': {
                'status': task.state,
                'current': 0,
                'total': 1,
                'state': 'Pending...'
            }
        }
    elif task.state != 'FAILURE':
        response = {
            'task': {
                'status': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'state': task.info.get('status', '')
            }
        }
        if 'result' in task.info:
            response['task']['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'task': {
                'status': task.state,
                'current': 1,
                'total': 1,
                'state': str(task.info),  # this is the exception raised
            }
        }
    return response


@app.route("/atualizar_springer")
def atualizar_springer_flask():
    springer_async = atualizar_springer_async.delay()
    
    print(springer_async.id)
    
    return jsonify({'Location': url_for('taskstatus',
                                                  task_id=springer_async.id)}), 202


@app.route("/atualizar_pubmed")
def atualizar_pubmed_flask():
    pubmed_async = atualizar_pubmed_async.delay()
    
    return jsonify({'Location': url_for('taskstatus',
                                                  task_id=pubmed_async.id)}), 202


@app.route("/")
def main():
    # TODO: Watson

    return render_template("index.html", route="home")


@app.route("/casos")
def casos():
    divs = []
    scripts = []

    pais = request.args.get("pais")
    selecionado = pais
    if pais is not None:
        pais = pais.replace(" ", "_")

    paises, df = atualizar_dados()

    script, div = atualizar_grafico_mapa(paises=paises)
    divs.append(div)
    scripts.append(script)

    script, div = atualizar_grafico_aumento(pais=pais, df=df)
    divs.append(div)
    scripts.append(script)

    script, div = atualizar_grafico_expon(pais=pais, df=df)
    divs.append(div)
    scripts.append(script)

    ultima_atualizacao = date.today() - timedelta(days=1)
    data = ultima_atualizacao.strftime("%d/%m/%Y")

    paises_txt = df["countriesAndTerritories"].replace("_", " ", regex=True).unique()
    return render_template("casos.html", scripts=scripts, divs=divs, data=data,
                           paises=paises_txt, selecionado=selecionado,
                           route="casos", df=df.reset_index().to_dict("list"))


@app.route("/noticias")
def noticias():
    return render_template("noticias.html", route="noticias",
                           noticias=[])


@app.route("/artigos")
def artigos():
    return render_template("artigos.html", route="artigos",
                           artigos=[])


@app.route("/fontes")
def fontes():
    return render_template("fontes.html", route="fontes",
                           nacionais=[], internacionais=[])


@app.route("/contato")
def contato():
    return render_template("contato.html", route="contato")


if __name__ == "__main__":
    app.run()
