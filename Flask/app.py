# TODO: Embelezar o site

from datetime import date, timedelta

from flask import Flask, render_template, request
from flask import flash, session
from flask_session import Session
from tempfile import mkdtemp
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

import os

from graficos import atualizar_dados,\
    atualizar_grafico_aumento, atualizar_grafico_expon, atualizar_grafico_mapa
from bases import atualizar_pubmed, atualizar_springer


# Criando o aplicativo Flask
app = Flask("__name__")

# Configurando o banco de dados
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Colocar o caminho pra database nas variáveis do ambiente (e.g.: DATABASE_URL = /database.db)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db = SQLAlchemy(app)

# Configurando sessão Flask
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def main():
    # TODO: Watson

    springer = atualizar_springer()
    pubmed = atualizar_pubmed()
    return render_template("index.html", route="home", springer=springer,
                           pubmed=pubmed)


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

    paises = df["countriesAndTerritories"].replace("_", " ", regex=True).unique()
    return render_template("casos.html", scripts=scripts, divs=divs, data=data,
                           paises=paises, selecionado=selecionado,
                           route="casos")


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
