import pandas as pd
import numpy as np
import geopandas as gpd
import shapely

from misc import parties2017, parties2021, parties2017Colours, parties2021Colours
from extractmap import generateGeoJSON, CuracaoID, CuracaoCentre

import plotly.express as px
import plotly.graph_objects as go


def generateElectionDF(file, parties, year):
    P = pd.DataFrame()
    for party in parties:
        if year == 2017:
            a = pd.read_excel(file, sheet_name=party, header=0).iloc[-3:-2, 2::]
        elif year == 2021:
            a = pd.read_excel(file, sheet_name=party, header=0).iloc[-1::, 2::]
        else:
            raise ValueError("Only 2021 and 2017 elections are available.")
        a.columns = [x.replace("sd: ", "") for x in a.columns]
        a.index = [party]
        a = a.transpose()

        P = pd.concat([P, a], axis=1)

    totaal = P.iloc[0]  # take out total party
    P = P.iloc[1::].assign(
        totalkiezers=lambda x: x[parties].sum(axis=1)
    )  # add total per loket
    P.index = P.index.astype(int)
    return totaal, P


def generateStemloketten(stemlokettenFile, electionFile, parties, year):

    stemlokettenYEAR = (
        pd.read_csv(stemlokettenFile, index_col=0)
        .reset_index(drop=True)
        .fillna("good")
        # doesnt work with lambda for some reason
        # .assign(geometry=lambda x: shapely.geometry.Point(x.Longitude, x.Latitude))
    )

    stemlokettenYEAR.index = stemlokettenYEAR.index + 1

    # shapely doesnt like lambda
    stemlokettenYEAR["geometry"] = [
        shapely.geometry.Point(a, b)
        for a, b in zip(
            stemlokettenYEAR.Longitude.values, stemlokettenYEAR.Latitude.values
        )
    ]

    stemlokettenYEAR = gpd.GeoDataFrame(stemlokettenYEAR, geometry="geometry")

    totalelectionYEAR, electionYEAR = generateElectionDF(electionFile, parties, year)

    # columns to aggregate for agg func
    # groupby to remove duplicate stembureaus
    stemlokettenAgg = {
        **{u: "first" for u in ["Accuracy", "geometry", "Latitude", "Longitude"]},
        **{party: "sum" for party in [*parties, "totalkiezers", "total"]},
        **{"pctKiezers": "mean"},
    }

    stemlokettenYEAR = (
        pd.concat([stemlokettenYEAR, electionYEAR], axis=1)
        .assign(pctKiezers=lambda x: (x.totalkiezers / x.total) * 100)
        .groupby("name", as_index=False)
        .agg(stemlokettenAgg)
    )

    # turn it into gpd again
    stemlokettenYEAR = gpd.GeoDataFrame(stemlokettenYEAR, geometry="geometry")

    # retrieve barios data
    barios = generateGeoJSON(CuracaoID, verbose=False).assign(bario=lambda x: x.index)

    # groupby to remove duplicates
    bariosAGG = {
        **{party: "sum" for party in [*parties, "totalkiezers", "total"]},
        **{u: "first" for u in ["total", "area", "invarea", "lat", "lon"]},
    }
    bariosYEAR = barios.sjoin(stemlokettenYEAR).dissolve("bario", aggfunc=bariosAGG)

    # Add bario data to stemloketten
    stemlokettenYEAR = stemlokettenYEAR.sjoin(barios).drop(
        ["lat", "lon", "index_right"], axis=1
    )

    # Retrieve winning party
    bariosYEAR["winner"] = bariosYEAR.loc[:, parties].idxmax(axis=1)
    stemlokettenYEAR["winner"] = (
        stemlokettenYEAR.loc[:, parties].astype(int).idxmax(axis=1)
    )

    return stemlokettenYEAR, bariosYEAR, totalelectionYEAR


def generateElectionMap(
    electionFiles: dict, StemlokettenFiles: dict, partiesLists: dict, years: list
):
    stemlokettenDict = {}
    bariosDict = {}
    totalsDataDict = {}

    for year in years:
        stemlokettenYEAR, bariosYEAR, totalelectionYEAR = generateStemloketten(
            StemlokettenFiles[year], electionFiles[year], partiesLists[year], year
        )

        stemlokettenDict[year] = stemlokettenYEAR
        bariosDict[year] = bariosYEAR
        totalsDataDict[year] = totalelectionYEAR

    return stemlokettenDict, bariosDict, totalsDataDict


if __name__ == "__main__":

    electiondata2017 = r"elekshon2017.xls"
    stemlokettendata2017 = r"stemloketten2017.csv"
    stemloketten2017, barios2017, totalelection2017 = generateStemloketten(
        stemlokettendata2017, electiondata2017, parties2017, 2017
    )

    electiondata2021 = r"elekshon2021.xls"
    stemlokettendata2021 = r"stemloketten2021.csv"
    stemloketten2021, barios2021, totalelection2021 = generateStemloketten(
        stemlokettendata2021, electiondata2021, parties2021, 2021
    )

    fig1 = px.scatter_mapbox(
        data_frame=stemloketten2017,
        lat=stemloketten2017.Latitude,
        lon=stemloketten2017.Longitude,
        hover_data=[*parties2017],
        hover_name="name",
        color="winner",
        color_discrete_map=parties2017Colours,
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=1,
    )
    fig1b = px.scatter_mapbox(
        data_frame=stemloketten2017,
        lat=stemloketten2017.Latitude,
        lon=stemloketten2017.Longitude,
        hover_data=None,
        opacity=1,
    )

    fig1b.update_traces(
        marker=dict(size=14, symbol="circle", color="DarkSlateGrey"),
    )
    fig1.update_traces(
        marker=dict(size=12, symbol="circle"),
    )
    # fig1.update_traces(
    #     marker=dict(size=12, line=dict(width=2, color="DarkSlateGrey")),
    #     selector=dict(mode="markers"),
    # )

    fig2 = px.choropleth_mapbox(
        data_frame=barios2017,
        geojson=barios2017.geometry,
        locations=barios2017.index,
        # featureidkey="bario",
        hover_data=parties2017,
        hover_name=barios2017.index,
        color=barios2017.winner,
        color_discrete_map=parties2017Colours,
        # color_continuous_scale="Viridis",
        # range_color=(0, 12),
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=0.5,
    )

    fig = go.Figure(data=(fig2.data + fig1b.data + fig1.data), layout=fig1.layout)
    fig.show()

    # 2021

    fig1 = px.scatter_mapbox(
        data_frame=stemloketten2021,
        lat=stemloketten2021.Latitude,
        lon=stemloketten2021.Longitude,
        hover_data=[*parties2021],
        hover_name="name",
        color="winner",
        color_discrete_map=parties2021Colours,
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=1,
    )
    fig1b = px.scatter_mapbox(
        data_frame=stemloketten2021,
        lat=stemloketten2021.Latitude,
        lon=stemloketten2021.Longitude,
        hover_data=None,
        opacity=1,
    )

    fig1b.update_traces(
        marker=dict(size=14, symbol="circle", color="DarkSlateGrey"),
    )
    fig1.update_traces(
        marker=dict(size=12, symbol="circle"),
    )
    # fig1.update_traces(
    #     marker=dict(size=12, line=dict(width=2, color="DarkSlateGrey")),
    #     selector=dict(mode="markers"),
    # )

    fig2 = px.choropleth_mapbox(
        data_frame=barios2021,
        geojson=barios2021.geometry,
        locations=barios2021.index,
        # featureidkey="bario",
        hover_data=parties2021,
        hover_name=barios2021.index,
        color=barios2021.winner,
        color_discrete_map=parties2021Colours,
        # color_continuous_scale="Viridis",
        # range_color=(0, 12),
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=0.5,
    )

    fig = go.Figure(data=(fig2.data + fig1b.data + fig1.data), layout=fig1.layout)
    fig.show()
