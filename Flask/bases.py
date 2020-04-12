# TODO: puxar automaticamente notícias recentes da Nature, PubMed, atualizações do Twitter, etc.
import requests
import locale
from datetime import date, datetime, timedelta


def atualizar_pubmed():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    date_format = "%Y-%m-%d"
    dateto = "onlinedateto:" + date.today().strftime(date_format)
    datefrom = "onlinedatefrom:" + (date.today() - timedelta(days=7)).strftime(date_format)
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
    return records

