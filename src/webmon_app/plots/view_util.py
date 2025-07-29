from bs4 import BeautifulSoup


def get_plotly_js(plot_data):
    # The version of the plotly.js library to use
    version = "2.9.0"
    if plot_data:
        soup = BeautifulSoup(plot_data, "html.parser")
        plotly_div = soup.find("div", class_="plotly-graph-div")
        if plotly_div and "data-plotlyjs-version" in plotly_div.attrs:
            version = str(plotly_div["data-plotlyjs-version"])

    # Determine which plotly script to load
    if version.startswith("2."):
        plotly_js = f"https://cdn.plot.ly/plotly-{version}.min.js"
    else:
        plotly_js = "https://cdn.plot.ly/plotly-latest.min.js"

    return plotly_js
