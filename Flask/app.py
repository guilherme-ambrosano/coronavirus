#TODO: Alternar mortes/casos
#TODO: Atualizar gráfico automaticamente
#TODO: Calcular previsão usando dados de outros países
#TODO: Embelezar o site

#TODO: Implementar a session/login
#TODO: Criar db com notícias/artigos/etc.
#TODO: Área do site para pessoa autenticada postar/moderar as postagens

import pandas as pd
import urllib

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, WheelZoomTool
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
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
# Colocar o caminho pra database nas variáveis do ambiente (e.g.: DATABASE_URL = /database.db)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db = SQLAlchemy(app)

# Configurando sessão Flask
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configurando o geopy
geolocator = Nominatim(user_agent="corona", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


class DataframeMundo:
    def __init__(self):
        pass


class DataframeBrasil:
    def __init__(self):
        pass


def atualizar_dados():
    ontem = date.today() - timedelta(days=1)

    ontem_str = ontem.strftime("%Y-%m-%d") + ".xlsx"
    arquivos_excel = [arq for arq in os.listdir(".") if arq.endswith(".xlsx")]
    if ontem_str not in arquivos_excel or "paises_" + ontem_str not in arquivos_excel:
        # Baixando a planilha da internet e carregando no pandas
        link = "https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-"+\
               ontem_str
        file_name, headers = urllib.request.urlretrieve(link)
        df = pd.read_excel(file_name)

        # Removendo as planilhas antigas
        for arq in arquivos_excel:
            os.remove(os.path.join(".", arq))

        # Criando coluna casesCumulative, com o número cumulativo de casos
        # (começando no primeiro dia, indo até o último)
        df["casesCumulative"] = df.iloc[::-1].groupby("countriesAndTerritories").cases.cumsum()[::-1]

        # Criando a coluna week e a coluna
        # casesDiff, com a diferença entre o número de casos entre as duas semanas
        df["week"] = df.dateRep.dt.week

        # Salvando a planilha nova
        df.to_excel(ontem_str)

        # Pegando as coordenadas dos países
        paises = atualizar_localizacao(df)
        paises.to_excel("paises_" + ontem_str)

    else:
        # Se já tiver planilha, é só ler
        df = pd.read_excel(ontem_str)
        paises = pd.read_excel("paises_" + ontem_str)

    return paises, df


def geocode_print(x):
    print(x)
    try:
        geo = geocode(x)
        print("deu\n")
    except:
        print("não deu\n")
        geo = {"point": (None, None)}
    return geo


def atualizar_localizacao(df):
    # Pegando coordenada dos países pelo geopy
    paises = df.groupby("countriesAndTerritories").cases.aggregate(sum)

    paises = pd.DataFrame(paises, columns=["cases"])
    paises.index.name = "countriesAndTerritories"
    paises.reset_index(inplace=True)

    paises["location"] = paises["countriesAndTerritories"].replace("_", " ", regex=True).apply(geocode_print)
    print(paises.head())
    paises["point"] = paises["location"].apply(lambda loc: tuple(loc.point) if loc else None)
    print(paises.head())
    return paises


def atualizar_grafico_aumento(pais=None, df=None):
    if df is None:
        paises, df = atualizar_dados()

    p = figure(plot_width=800, plot_height=250, x_axis_type="datetime",
               x_axis_label="Data",
               y_axis_label="Casos acumulados")
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    # Criando coluna casesCumulative, com o número cumulativo de casos (começando no primeiro dia, indo até o último)
    df["casesCumulative"] = df.iloc[::-1].groupby("countriesAndTerritories").cases.cumsum()[::-1]
    if pais is None:
        # Dados do mundo inteiro
        p.circle(df["dateRep"], df["casesCumulative"], color="navy", alpha=0.1)
    else:
        # Dados do país selecionado
        df_pais = df.loc[df["countriesAndTerritories"] == pais]
        p.circle(df_pais["dateRep"], df_pais["casesCumulative"], color="navy", alpha=0.5)

    p.xaxis.formatter = DatetimeTickFormatter(days=["%d/%m/%Y"])
    script, div = components(p)
    return script, div


def atualizar_grafico_expon(pais=None, df=None):
    if df is None:
        paises, df = atualizar_dados()

    p = figure(plot_width=800, plot_height=250, y_axis_type="log", x_axis_type="log",
               x_axis_label="Diferença no número de casos da semana anterior",
               y_axis_label="Casos acumulados por semana")
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    df = df.groupby(["week", "countriesAndTerritories"]).sum().reset_index()
    df["casesDiff"] = df.groupby("countriesAndTerritories").casesCumulative.diff()
    if pais is None:
        # Dados do mundo inteiro
        p.line([1, max(df.casesCumulative)], [1, max(df.casesDiff.dropna())], color="red")
        p.line(df["casesCumulative"], df["casesDiff"], color="navy", alpha=0.1)
    else:
        # Dados do país selecionado
        df_pais = df.loc[df["countriesAndTerritories"] == pais]
        p.line([1, max(df_pais.casesCumulative)], [1, max(df_pais.casesDiff.dropna())], color="red")
        p.line(df_pais["casesCumulative"], df_pais["casesDiff"], color="navy", alpha=0.5)

    script, div = components(p)
    return script, div


def atualizar_grafico_mapa(paises=None):
    if paises is None:
        paises, df = atualizar_dados()

    paises["x"] = paises.point.apply(lambda x: x[0])
    paises["y"] = paises.point.apply(lambda x: x[1])
    tile_provider = get_provider(CARTODBPOSITRON)
    p = figure(x_range=(-2000000, 6000000), y_range=(-1000000, 7000000),
               x_axis_type="mercator", y_axis_type="mercator")
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    p.add_tile(tile_provider)
    p.circle(x=paises.x,
             y=paises.y,
             size=paises.cases,
             line_color="navy",
             fill_color="navy",
             fill_alpha=0.05)

    script, div = components(p)
    return script, div

@app.route("/")
def main():
    #TODO: puxar automaticamente notícias recentes da Nature, PubMed, atualizações do Twitter, etc.
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

    script, div = atualizar_grafico_mapa(df=df, paises=paises)
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


if __name__ == "__main__":
    app.run()