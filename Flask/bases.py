
# TODO: Atualizações do Twitter (@CoronavirusBra1, @Coronavirusboas...)
# TODO: Nossas próprias bases (Google Drive)

import requests
import locale
from datetime import date, datetime, timedelta

import os

from ast import literal_eval


def atualizar_springer():
    ontem = date.today() - timedelta(days=1)
    ontem_str = "springer_" + ontem.strftime("%Y-%m-%d") + ".txt"

    arquivos_texto = [arq for arq in os.listdir(".") if arq.endswith(".txt")]

    if ontem_str in arquivos_texto:
        with open(ontem_str) as file:
            records = literal_eval(file.read())
    else:
        locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

        date_format = "%Y-%m-%d"
        dateto = "onlinedateto:" + ontem.strftime(date_format)
        datefrom = "onlinedatefrom:" + (ontem - timedelta(days=7)).strftime(date_format)
        openaccess = "openaccess:true"
        title = "(title:covid-19 OR title:covid19)"
        sort = "sort:date"
        user_key = "api_key=d3ad1f83983be500c6aeb4a03b2e7e1a"
        endereco = "https://api.springernature.com/meta/v2/json?q=" + \
                   datefrom + " " + dateto + " " + openaccess + " " + title + " " + sort + "&" + user_key
        response = requests.get(endereco)
        records = response.json()["records"]
        for record in records:
            record["authorlist"] = []
            for creator in record["creators"]:
                record["authorlist"].append(creator["creator"])
            record["authors"] = "; ".join(record["authorlist"])
            record["onlineDate"] = datetime.strptime(record["onlineDate"], date_format).strftime("%d/%b/%Y")

        for arq in arquivos_texto:
            if arq.startswith("springer_"):
                os.remove(os.path.join(".", arq))

        with open(ontem_str, "w+") as file:
            file.write(str(records))

    return records


def atualizar_pubmed():
    ontem = date.today() - timedelta(days=1)
    ontem_str = "pubmed_" + ontem.strftime("%Y-%m-%d") + ".txt"

    arquivos_texto = [arq for arq in os.listdir(".") if arq.endswith(".txt")]
    if ontem_str in arquivos_texto:
        with open(ontem_str) as file:
            records = literal_eval(file.read())
    else:
        locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
        db = "db=pubmed"
        term = "term=covid-19"
        reldate = "reldate=1"
        datetype = "datetype=pdat"
        retmode = "retmode=json"
        params = [db, term, reldate, datetype, retmode]
        endereco = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + "&".join(params)
        response = requests.get(endereco)
        ids = response.json()["esearchresult"]["idlist"]
        records = []
        for id in ids:
            record = {"onlineDate": None,
                      "title": None,
                      "authors": None,
                      "link": None}
            endereco = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=" + id +\
                "&retmode=json"
            response = requests.get(endereco).json()["result"][id]
            for articleid in response["articleids"]:
                if articleid["idtype"] == "doi":
                    record["link"] = "https://doi.org/" + articleid["value"]
            authors = []
            for author in response["authors"]:
                nome = author["name"].split(" ")
                nome = " ".join(nome[:-1]) + ", " + ". ".join(list(nome[-1])) + "."
                authors.append(nome)
            record["authors"] = "; ".join(authors)
            record["title"] = response["title"]
            record["onlineDate"] = datetime.strptime(response["sortpubdate"], "%Y/%m/%d %H:%M").strftime("%d/%b/%Y")
            records.append(record)

        for arq in arquivos_texto:
            if arq.startswith("pubmed_"):
                os.remove(os.path.join(".", arq))

        with open(ontem_str, "w+") as file:
            file.write(str(records))

    return records