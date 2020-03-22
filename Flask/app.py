import pandas as pd
import urllib

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.io import show

from flask import Flask, render_template


link = "https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-2020-03" \
       "-21.xlsx"
file_name, headers = urllib.request.urlretrieve(link)
df = pd.read_excel(file_name)

p = figure(plot_width=800, plot_height=250, x_axis_type="datetime")
p.circle(df["DateRep"], df["Deaths"], color="navy", alpha=0.5)
# show(p)

script, div = components(p)

app = Flask("__name__")


@app.route("/")
def main():
    return render_template("index.html", script=script, div=div)


if __name__ == "__main__":
    app.run()