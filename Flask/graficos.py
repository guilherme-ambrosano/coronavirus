import math

import pandas as pd
import numpy as np
import urllib

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, WheelZoomTool
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.io import show

from ast import literal_eval

from datetime import date, timedelta

import os


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
        link = "https://www.ecdc.europa.eu/sites/default/files/documents/" \
               "COVID-19-geographic-disbtribution-worldwide-" + ontem_str
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


def atualizar_localizacao(df):
    # Pegando coordenada dos países pelo geopy
    paises = df.groupby("countriesAndTerritories").cases.aggregate(sum)

    paises = pd.DataFrame(paises, columns=["cases"])
    paises.index.name = "countriesAndTerritories"
    paises.reset_index(inplace=True)

    paises["location"] = paises["countriesAndTerritories"].replace("_", " ", regex=True).apply(geocode)
    paises["point"] = paises["location"].apply(lambda loc: tuple(loc.point) if loc else None)
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


def merc(point):
    if point is np.nan:
        return None, None

    lat, lon, alt = literal_eval(point)

    r_major = 6378137.000
    x = r_major * math.radians(lon)
    scale = x / lon
    y = 180.0 / math.pi * math.log(math.tan(math.pi / 4.0 + lat * (math.pi / 180.0) / 2.0)) * scale

    return x, y


def atualizar_grafico_mapa(paises=None):
    if paises is None:
        paises, df = atualizar_dados()

    paises["x"] = paises.point.apply(lambda x: merc(x)[0])
    paises["y"] = paises.point.apply(lambda x: merc(x)[1])
    tile_provider = get_provider(CARTODBPOSITRON)
    p = figure(plot_width=800, plot_height=500,
               x_range=(-2000000, 6000000), y_range=(-1000000, 7000000),
               x_axis_type="mercator", y_axis_type="mercator")
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    p.add_tile(tile_provider)
    p.circle(x=paises.x,
             y=paises.y,
             size=paises.cases / 5000,
             line_color="navy",
             fill_color="navy",
             fill_alpha=0.05)

    script, div = components(p)
    return script, div

