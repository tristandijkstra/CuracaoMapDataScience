from OSMPythonTools.nominatim import Nominatim
import pandas as pd
import shapely

import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import (
    Dash,
    dcc,
    html,
    Input,
    Output,
    State,
)

from sklearn import cluster

from extractmap import generateGeoJSON, CuracaoID, CuracaoCentre
from extractElection import generateElectionMap
from misc import (
    parties2010,
    parties2012,
    parties2016,
    parties2017,
    parties2021,
    parties2010Colours,
    parties2012Colours,
    parties2016Colours,
    parties2017Colours,
    parties2021Colours,
)


electiondata2021 = r"elekshon2021.xls"
electiondata2017 = r"elekshon2017.xls"
electiondata2016 = r"elekshon2016.xls"
electiondata2012 = r"elekshon2012.xls"
electiondata2010 = r"elekshon2010.xls"

stemlokettendata2021 = r"stemloketten2021.csv"
stemlokettendata2017 = r"stemloketten2017.csv"
stemlokettendata2016 = r"stemloketten2017.csv"
stemlokettendata2012 = r"stemloketten2017.csv"
stemlokettendata2010 = r"stemloketten2017.csv"


electionFiles = {2010: electiondata2010, 2012: electiondata2012, 2016: electiondata2016, 2017: electiondata2017, 2021: electiondata2021}

stemlokettenFiles = {
    2010: stemlokettendata2010,
    2012: stemlokettendata2012,
    2016: stemlokettendata2016,
    2017: stemlokettendata2017,
    2021: stemlokettendata2021,
}
partiesLists = {2010: parties2010, 2012: parties2012, 2016: parties2016, 2017: parties2017, 2021: parties2021}

partiesColoursDict = {
    2010: parties2010Colours,
    2012: parties2012Colours,
    2016: parties2016Colours,
    2017: parties2017Colours,
    2021: parties2021Colours,
}
years = [2010, 2012, 2016, 2017, 2021]

stemlokettenDict, bariosDict, totalsDataDict = generateElectionMap(
    electionFiles, stemlokettenFiles, partiesLists, years
)

# externalscr

app = Dash(__name__, external_scripts=["https://cdn.tailwindcss.com"])

# Layout
app.layout = html.Div(
    children=[
        html.Div(
            id="control",
            children=[
                html.Div(
                    id="dddiv1",
                    style={
                        "display": "inline-block",
                        "width": "10%",
                        "margin-left": "20px",
                    },
                    children=[
                        "Election Year:",
                        dcc.Dropdown(
                            id="yearDD",
                            options=[
                                {"label": "2021", "value": 2021},
                                {"label": "2017", "value": 2017},
                                {"label": "2016 (beta)", "value": 2016},
                                {"label": "2012 (beta)", "value": 2012},
                                {"label": "2010 (beta)", "value": 2010},
                            ],
                            multi=False,
                            value=2021,
                            searchable=False,
                            clearable=False,
                            placeholder="Select a year",
                        ),
                    ],
                ),
                html.Div(
                    id="dddiv2",
                    style={
                        "display": "inline-block",
                        "width": "15%",
                        "margin-left": "20px",
                    },
                    children=[
                        "Comparative Bar Chart:",
                        dcc.Dropdown(
                            id="comparativeCL",
                            options=[
                                {"label": "On", "value": True},
                                {"label": "Off", "value": False},
                            ],
                            multi=False,
                            value=False,
                            searchable=False,
                            clearable=False,
                            placeholder="on/off",
                        ),
                    ],
                ),
                html.Div(
                    id="dddiv3",
                    style={
                        "display": "inline-block",
                        "width": "10%",
                        "margin-left": "20px",
                    },
                    children=[
                        "Clustering:",
                        dcc.Dropdown(
                            id="clustersDD",
                            options=[
                                {"label": "No Clustering", "value": 0},
                                {"label": "3", "value": 3},
                                {"label": "5", "value": 5},
                                {"label": "10", "value": 10},
                            ],
                            placeholder="Select a year",
                            multi=False,
                            searchable=False,
                            clearable=False,
                            value=0,
                        ),
                    ],
                ),
                html.Div(
                    id="dddiv4",
                    style={
                        "display": "inline-block",
                        "width": "15%",
                        "margin-left": "20px",
                    },
                    children=[
                        "Number representation:",
                        dcc.Dropdown(
                            id="NumberStyleDD",
                            options=[
                                {"label": "Number of Voters", "value": "Numbers"},
                                {"label": "Percentage", "value": "Percentage"},
                            ],
                            placeholder="Number representation",
                            multi=False,
                            searchable=False,
                            clearable=False,
                            value="Numbers",
                        ),
                    ],
                ),
                html.Hr(),
            ],
        ),
        html.Div(
            id="graphs",
            children=[
                dcc.Graph(
                    id="map",
                    figure={},
                    style={"display": "inline-block", "width": "68%", "height": "89vh"},
                ),
                html.Div(
                    id="barcontainer",
                    style={"display": "inline-block", "width": "30%", "height": "85vh"},
                    children=[
                        dcc.Graph(
                            id="bar",
                            figure={},
                            style={
                                "display": "inline-block",
                                "width": "100%",
                                "height": "89vh",
                            },
                        )
                    ],
                ),
                # dcc.Graph(id='bar', figure={})
            ],
        ),
    ]
)


@app.callback(
    [
        Output(component_id="map", component_property="figure"),
        Output(component_id="bar", component_property="figure"),
    ],
    [
        Input(component_id="clustersDD", component_property="value"),
        Input(component_id="yearDD", component_property="value"),
        Input(component_id="NumberStyleDD", component_property="value"),
        Input(component_id="comparativeCL", component_property="value"),
        Input(component_id="map", component_property="clickData"),
    ],
)
def update_graph(clustersDD, yearDD, NumberStyleDD, comparativeCL, mapclicks):
    otheryear = years[::]
    otheryear.remove(int(yearDD))
    otheryear = int(otheryear[0])

    bariosDictFinal = {}
    # mapclicks = None
    if clustersDD > 0:
        for key in bariosDict:
            bariosClusterAGG = {
                **{u: "first" for u in ["cluster", "lat"]},
                **{
                    party: "sum"
                    for party in [
                        *partiesLists[key],
                        "totalkiezers",
                        "total",
                        "area",
                        "invarea",
                    ]
                },
                **{"pctKiezers": "mean"},
                # **{pd.Series.mode: "winner"},
            }
            model = cluster.KMeans(clustersDD)
            bariosTemp = bariosDict[key]
            X = bariosTemp[["lat", "lon"]]
            bariosTemp["cluster"] = model.fit_predict(
                X, sample_weight=bariosTemp["invarea"]
            )
            bariosTemp = bariosTemp.dissolve(by="cluster", aggfunc=bariosClusterAGG)
            bariosTemp["winner"] = bariosTemp.loc[:, partiesLists[key]].idxmax(axis=1)
            bariosTemp = bariosTemp.rename_axis(None)

            # This is lazy
            if clustersDD == 3:
                bariosTemp = bariosTemp.sort_values("lat")
                # bar
                bariosTemp.index = ["West", "Centre", "East"]
                bariosTemp = bariosTemp.assign(bario=lambda x: x.index)
            else:
                bariosTemp = bariosTemp.assign(
                    bario=lambda x: "Cluster nr. " + x.index.astype(str)
                ).set_index("bario", drop=False)

            bariosDictFinal[key] = bariosTemp

    else:
        bariosDictFinal = bariosDict

    if (mapclicks is not None) and (len(mapclicks) > 0):
        barlocation = mapclicks["points"][0]["hovertext"]
        if barlocation not in bariosDictFinal[yearDD].index.values:
            mapclicks = None
            barmode = None
            barlocation = "Total"
        elif "location" in mapclicks["points"][0]:
            barmode = "bario"
            bariobar = (
                bariosDictFinal[yearDD]
                .loc[[barlocation], partiesLists[yearDD]]
                .transpose()
                .rename(columns={barlocation: yearDD})
            )
            bariobar[otheryear] = (
                bariosDictFinal[otheryear]
                .loc[[barlocation], partiesLists[otheryear]]
                .transpose()
            )
            bariobar = (
                bariobar.fillna(0)
                .astype(int)
                .assign(party=lambda x: x.index)
                .sort_values(yearDD, ascending=False)
            )
        else:
            barmode = "loket"

            loketbar = (
                stemlokettenDict[yearDD]
                .query("name == @barlocation")
                .loc[:, partiesLists[yearDD]]
                .transpose()
            )
            if barlocation in stemlokettenDict[otheryear].name.values:
                loketbar[otheryear] = (
                    stemlokettenDict[otheryear]
                    .query("name == @barlocation")
                    .loc[:, partiesLists[otheryear]]
                    .iloc[0]
                    .transpose()
                    # .rename(columns=[{barlocation: yearDD}])
                )
            loketbar = (
                loketbar.rename(columns={loketbar.columns[0]: yearDD})
                .fillna(0)
                .astype(int)
                .assign(party=lambda x: x.index)
                .sort_values(yearDD, ascending=False)
            )
    else:
        barmode = None
        barlocation = "Total"

    stemlok = stemlokettenDict[yearDD]

    if NumberStyleDD == "Percentage":
        stemlok.loc[:, partiesLists[yearDD]] = (
            stemlok.loc[:, partiesLists[yearDD]]
            .div(stemlok.totalkiezers, axis=0)
            .multiply(100, axis=0)
            .round(1)
        )
    fig1 = px.scatter_mapbox(
        data_frame=stemlok,
        lat=stemlok.Latitude,
        lon=stemlok.Longitude,
        hover_data=[*partiesLists[yearDD]],
        hover_name="name",
        color="winner",
        color_discrete_map=partiesColoursDict[yearDD],
        mapbox_style="carto-positron",
        zoom=9.8,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=1,
    )
    fig1b = px.scatter_mapbox(
        data_frame=stemlok,
        lat=stemlok.Latitude,
        lon=stemlok.Longitude,
        hover_data=None,
        opacity=1,
    )

    fig1b.update_traces(
        marker=dict(size=14, symbol="circle", color="DarkSlateGrey"),
    )
    fig1.update_traces(
        marker=dict(size=12, symbol="circle"),
    )

    chloro = bariosDictFinal[yearDD].query("totalkiezers > 0")
    if NumberStyleDD == "Percentage":
        chloro.loc[:, partiesLists[yearDD]] = (
            chloro.loc[:, partiesLists[yearDD]]
            .div(chloro.totalkiezers, axis=0)
            .multiply(100, axis=0)
            .round(1)
        )
    fig2 = px.choropleth_mapbox(
        data_frame=chloro,
        geojson=chloro.geometry,
        locations=chloro.index,
        hover_data=partiesLists[yearDD],
        hover_name=chloro.bario,
        color=chloro.winner,
        color_discrete_map=partiesColoursDict[yearDD],
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=0.5,
    )

    totalbar = (
        pd.DataFrame(totalsDataDict[yearDD].sort_values(ascending=False))
        .rename(columns={"Totaal": yearDD})
        .assign(party=lambda x: x.index)
    )
    totalbar[otheryear] = totalsDataDict[otheryear]
    totalbar = totalbar.fillna(0)

    colstemp = totalbar.columns.difference(["party"])

    if barmode == "bario":
        bardf = bariobar
    elif barmode == "loket":
        bardf = loketbar
    else:
        bardf = totalbar

    if NumberStyleDD == "Percentage":
        bardf.loc[:, colstemp] = (
            bardf.loc[:, colstemp]
            .div(bardf[colstemp].sum(), axis=1)
            .multiply(100, axis=1)
            .round(1)
        )
    barlist = [yearDD, otheryear] if otheryear in bardf.columns else [yearDD]

    barcomp = px.bar(
        data_frame=bardf,
        x="party",
        y=barlist,
        barmode="group",
        orientation="v",
        title=barlocation,
    )
    bar = px.bar(
        data_frame=bardf,
        x="party",
        y=int(yearDD),
        color="party",
        orientation="v",
        color_discrete_map=partiesColoursDict[yearDD],
        title=barlocation,
    )

    fig = go.Figure(data=(fig2.data + fig1b.data + fig1.data), layout=fig1.layout)

    barcomp.update_layout(
        legend=dict(title="", yanchor="top", y=0.99, xanchor="right", x=0.99)
    )

    bar.update_layout(showlegend=False)
    if comparativeCL:
        barFinal = barcomp
    else:
        barFinal = bar

    barFinal.update_xaxes(title="")

    if NumberStyleDD == "Percentage":
        barFinal.update_yaxes(title="Voters (%)")
    else:
        barFinal.update_yaxes(title="Voters (-)")

    barFinal.update_traces(marker_line_color="DarkSlateGrey", marker_line_width=0.5)

    return fig, barFinal


if __name__ == "__main__":
    app.run_server(debug=True)
