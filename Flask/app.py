#TODO: Gráfico acumulado
#TODO: Alternar mortes/casos
#TODO: Atualizar gráfico automaticamente
#TODO: Embelezar o site

import pandas as pd
import urllib

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from bokeh.plotting import figure
from bokeh.embed import components
# from bokeh.io import show

from datetime import date, timedelta

from flask import Flask, render_template, request

import os

app = Flask("__name__")

# Configurando o geopy
geolocator = Nominatim(user_agent="corona")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def atualizar_dados():
    ontem = date.today() - timedelta(days=1)
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
        paises = pd.read_excel("paises_" + ontem_str)

    return ontem, paises, df


def atualizar_localizacao(df):
    # Pegando coordenada dos países pelo geopy
    paises = df.groupby("countriesAndTerritories").cases.aggregate(sum)

    paises = pd.DataFrame(paises, columns=["cases"])
    paises.index.name = "countriesAndTerritories"
    paises.reset_index(inplace=True)

    paises["location"] = paises["countriesAndTerritories"].replace("_", " ", regex=True).apply(geocode)
    paises["point"] = paises["location"].apply(lambda loc: tuple(loc.point) if loc else None)
    return paises


def atualizar_grafico(pais=None):
    ontem, paises, df = atualizar_dados()

    p = figure(plot_width=800, plot_height=250, x_axis_type="datetime")
    if pais is None:
        # Dados do mundo inteiro
        # p.circle(df["dateRep"], df["deaths"], color="navy", alpha=0.5)
        pass
    else:
        # Dados do país selecionado
        df_pais = df.loc[df["countriesAndTerritories"] == pais]
        p.circle(df_pais["dateRep"], df_pais["cases"], color="navy", alpha=0.5)

    script, div = components(p)
    return script, div, ontem, paises["countriesAndTerritories"]


@app.route("/")
def main():
    pais = request.args.get("pais")
    selecionado = pais
    if pais is not None:
        pais = pais.replace(" ", "_")
    script, div, ultima_atualizacao, paises = atualizar_grafico(pais=pais)
    paises = paises.replace("_", " ", regex=True)
    data = ultima_atualizacao.strftime("%d/%m/%Y")
    return render_template("index.html", script=script, div=div, data=data, paises=paises, selecionado=selecionado)


if __name__ == "__main__":
    app.run()