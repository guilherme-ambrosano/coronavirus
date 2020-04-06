#TODO: Alternar mortes/casos
#TODO: Atualizar gráfico automaticamente
#TODO: Calcular previsão usando dados de outros países
#TODO: Fazer mapas dos casos nos países/estados
#TODO: Embelezar o site

import pandas as pd
import urllib

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.io import show

from datetime import date, timedelta

from flask import Flask, render_template, request
from flask import flash, session
from flask_session import Session
from tempfile import mkdtemp
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

import os

# Criando o aplicativo Flask
app = Flask("__name__")

# Configurando o banco de dados
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db = SQLAlchemy(app)

# Configurando sessão Flask
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configurando o geopy
geolocator = Nominatim(user_agent="corona")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


class DataframeMundo:
    def __init__(self):
        pass


class DataframeBrasil:
    def __init__(self):
        pass


def atualizar_dados():
    ontem = date.today() - timedelta(days=1)

    ontem_str_br = ontem.strftime("%Y%m%d") + ".csv"
    arquivos_csv = [arq for arq in os.listdir(".") if arq.endswith(".csv")]
    if ontem_str_br not in arquivos_csv:
        pass
        # Baixando a planilha da internet e carregando no pandas
        # FIXME: o https://covid.saude.gov.br/ dificultou o acesso aos dados, vai ter que dar um jeito de entrar manualmente
        # file_name, headers = urllib.request.urlretrieve(link)
        # df_br = pd.read_csv(file_name, sep=";", decimal=",")
        # df_br["data"] = pd.to_datetime(df_br["data"], format="%Y-%m-%d")

        # Removendo os arquivos antigos
        # for arq in arquivos_csv:
        #     os.remove(os.path.join(".", arq))

        # Salvando a planilha nova
        # df_br.to_csv(ontem_str_br, sep=";", decimal=",", index=False)

    ontem_str = ontem.strftime("%Y-%m-%d") + ".xlsx"
    arquivos_excel = [arq for arq in os.listdir(".") if arq.endswith(".xlsx")]
    if ontem_str not in arquivos_excel:
        # Baixando a planilha da internet e carregando no pandas
        link = "https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-" + \
               ontem_str
        file_name, headers = urllib.request.urlretrieve(link)
        df = pd.read_excel(file_name)

        # Removendo as planilhas antigas
        for arq in arquivos_excel:
            os.remove(os.path.join(".", arq))

        # Salvando a planilha nova
        df.to_excel(ontem_str)

        # Pegando as coordenadas dos países
        paises = atualizar_localizacao(df)
        paises.to_excel("paises_" + ontem_str)

    else:
        # Se já tiver planilha, é só ler
        df = pd.read_excel(ontem_str)
        df_br = pd.read_csv(ontem_str_br, sep=";", decimal=",")
        df_br["data"] = pd.to_datetime(df_br["data"], format="%Y-%m-%d")
        paises = pd.read_excel("paises_" + ontem_str)

    return paises, df, df_br


def atualizar_localizacao(df):
    # Pegando coordenada dos países pelo geopy
    paises = df.groupby("countriesAndTerritories").cases.aggregate(sum)

    paises = pd.DataFrame(paises, columns=["cases"])
    paises.index.name = "countriesAndTerritories"
    paises.reset_index(inplace=True)

    paises["location"] = paises["countriesAndTerritories"].replace("_", " ", regex=True).apply(geocode)
    paises["point"] = paises["location"].apply(lambda loc: tuple(loc.point) if loc else None)
    return paises



def atualizar_grafico_brasil(estado=None, df_br=None):
    if df_br is None:
        paises, df, df_br = atualizar_dados()

    p = figure(plot_width=800, plot_height=250, x_axis_type="datetime")
    if estado is None:
        # Dados do Brasil inteiro
        p.circle(df_br["data"], df_br["casosAcumulados"], color="navy", alpha=0.5)
    else:
        # Dados do estado selecionado
        df_estado = df_br.loc[df_br["estado"] == estado]
        p.circle(df_estado["data"], df_estado["casosAcumulados"], color="navy", alpha=0.5)

    script, div = components(p)
    return script, div


@app.route("/")
def main():
    divs = []
    scripts = []

    estado = request.args.get("estado")

    paises, df, df_br = atualizar_dados()
    paises = paises["countriesAndTerritories"].replace("_", " ", regex=True)
    estados = df_br["estado"].unique()

    script, div = atualizar_grafico_brasil(estado=estado, df_br=df_br)
    divs.append(div)
    scripts.append(script)

    ultima_atualizacao = date.today() - timedelta(days=1)
    data = ultima_atualizacao.strftime("%d/%m/%Y")

    return render_template("index.html", scripts=scripts, divs=divs, data=data,
                           estados=estados, estado=estado)


if __name__ == "__main__":
    app.run()