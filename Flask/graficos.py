# TODO: Atualizar gráfico automaticamente
# TODO: Alternar mortes/casos
# TODO: Calcular previsão usando dados de outros países

import math

import json

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

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pycountry


# Configurando o geopy
geolocator = Nominatim(user_agent="corona", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def baixar_dados():
    ontem = date.today() - timedelta(days=1)

    ontem_str = ontem.strftime("%Y-%m-%d") + ".xlsx"
    arquivos_excel = [arq for arq in os.listdir(".") if arq.endswith(".xlsx")]
    if ontem_str not in arquivos_excel or "paises_" + ontem_str not in arquivos_excel:
        # Baixando a planilha da internet e carregando no pandas
        link = "https://www.ecdc.europa.eu/sites/default/files/documents/" \
               "COVID-19-geographic-disbtribution-worldwide-" + ontem_str
        file_name, _ = urllib.request.urlretrieve(link)
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
        
        # Pegando as siglas dos paises
        paises = atualizar_siglas(paises)

        # Salvando
        paises.to_excel("paises_" + ontem_str)


def atualizar_dados_json(pais=None):
    ontem = date.today() - timedelta(days=1)

    ontem_str = ontem.strftime("%Y-%m-%d") + ".xlsx"
    arquivos_excel = [arq for arq in os.listdir(".") if arq.endswith(".xlsx")]
    if ontem_str not in arquivos_excel:
        baixar_dados()

    df = pd.read_excel(ontem_str)
    
    if pais is not None:
        pais = pais.replace("_", " ")
        df = df.loc[df["countriesAndTerritories"] == pais]

    df["dateRep"] = df["dateRep"].apply(lambda x: x.strftime("%Y-%m-%d"))
    df_json = json.dumps(df.reset_index().to_dict())

    return df_json


def atualizar_dados():
    ontem = date.today() - timedelta(days=1)

    ontem_str = ontem.strftime("%Y-%m-%d") + ".xlsx"
    arquivos_excel = [arq for arq in os.listdir(".") if arq.endswith(".xlsx")]
    if ontem_str not in arquivos_excel or "paises_" + ontem_str not in arquivos_excel:
        baixar_dados()

    df = pd.read_excel(ontem_str)
    paises = pd.read_excel("paises_" + ontem_str)
    
    return paises, df


def retornar_sigla(pais):
    sigla = pycountry.countries.get(name=pais)
    if sigla is not None:
        sigla = sigla.alpha_2
    else:
        sigla = pycountry.countries.get(official_name=pais)
        if sigla is not None:
            sigla = sigla.alpha_2
        else:
            geocode_location = geocode(pais)
            if geocode_location is None:
                return sigla
            sigla = pycountry.countries.get(name=geocode_location.address)
            if sigla is not None:
                sigla = sigla.alpha_2
            else:
                sigla = pycountry.countries.get(official_name=geocode_location.address)
                if sigla is not None:
                    sigla = sigla.alpha_2

    return sigla


def atualizar_siglas(paises):
    paises["sigla"] = paises["countriesAndTerritories"]\
    .replace("_", " ", regex=True)\
    .apply(retornar_sigla)
    return paises


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
        _, df = atualizar_dados()

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
