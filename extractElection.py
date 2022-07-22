import pandas as pd
import numpy as np
import geopandas as gpd
import shapely
import os
from shapely import wkt

from misc import parties2017, parties2021, parties2017Colours, parties2021Colours
from extractmap import generateGeoJSON, CuracaoID, CuracaoCentre

import plotly.express as px
import plotly.graph_objects as go


def generateElectionDF(file: str, parties: list, year: int):
    """generate election dataframes from KSE xls data

    Args:
        file (str): path to xls file from KSE.
        parties (list): list of parties participating in election.
        year (int): year of election.

    Raises:
        ValueError: Years other than 2017 or 2021 not implemented.

    Returns:
        total: short DF with the total votes for each party.
        election data: DF with voting hall (stemloket) on y and parties on x.
    """
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


def generateStemloketten(
    stemlokettenFile: str, electionFile: str, parties: list, year: int
):
    """enerate stemloketten DF file

    Args:
        stemlokettenFile (str): file path to stemloketten file.
        electionFile (str): file path to election file from KSE.
        parties (list): list of parties names participating in election.
        year (int): year of election.

    Returns:
        pd.Dataframe: Dataframe with stemlokketten data, election results, and district(bario) data.
        pd.Dataframe: Dataframe with barios data with election results.
        pd.Dataframe: Dataframe with party total votes for year.
    """
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
        **{"pctKiezers": "mean"},
    }
    bariosYEAR = (
        barios.sjoin(stemlokettenYEAR)
        .dissolve("bario", aggfunc=bariosAGG)
        .drop_duplicates()
    )

    # Add back barios without stemloketten.
    remainingBarios = [
        x for x in barios.index.values if x not in bariosYEAR.index.values
    ]
    remainingBarios = list(set(remainingBarios))

    bariosYEAR = pd.concat(
        [
            bariosYEAR,
            barios.loc[remainingBarios, ["area", "invarea", "geometry", "lat", "lon"]]
            .assign(bario=lambda x: x.index)
            .dissolve("bario"),
        ],
        axis=0,
    ).fillna(0)

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
    electionFiles: dict,
    stemlokettenFiles: dict,
    partiesLists: dict,
    years: list,
    forceRegen=False,
    saveFolder="processed",
):
    """Generate election data for multiple years in dict format

    Args:
        electionFiles (dict): dictionary with file paths to election xls' from KSE
        stemlokettenFiles (dict): dictionary with file paths to stemloketten data
        partiesLists (dict): list of lists of parties participating in elections

        years (list): list of int years

    Returns:
        dict: Dictionary with Dataframes with stemlokketten data, election results, and district(bario) data.
        dict: Dictionary with Dataframes with barios data with election results.
        dict: Dictionary with Dataframes with party total votes for year.
    """
    stemlokettenDict = {}
    bariosDict = {}
    totalsDataDict = {}
    if not os.path.exists(saveFolder) or forceRegen:
        os.makedirs(saveFolder)
        for year in years:
            stemlokettenYEAR, bariosYEAR, totalelectionYEAR = generateStemloketten(
                stemlokettenFiles[year], electionFiles[year], partiesLists[year], year
            )
            stemlokettenYEAR = stemlokettenYEAR[
                ~stemlokettenYEAR.index.duplicated(keep="first")
            ]

            bariosYEAR = bariosYEAR.rename_axis(None)
            bariosYEAR = bariosYEAR.assign(bario= lambda x: x.index)

            stemlokettenDict[year] = stemlokettenYEAR
            bariosDict[year] = bariosYEAR
            totalsDataDict[year] = totalelectionYEAR

            stemlokettenYEAR.to_csv(f"{saveFolder}/stemloketten_{year}.csv")
            bariosYEAR.to_csv(f"{saveFolder}/barios_{year}.csv")
            totalelectionYEAR.to_csv(f"{saveFolder}/totalelection_{year}.csv")
    else:
        for year in years:
            a = pd.read_csv(f"{saveFolder}/stemloketten_{year}.csv", index_col=0)
            a.geometry = a.geometry.apply(wkt.loads)
            b = pd.read_csv(f"{saveFolder}/barios_{year}.csv", index_col=0)
            b.geometry = b.geometry.apply(wkt.loads)
            c = pd.read_csv(
                f"{saveFolder}/totalelection_{year}.csv", index_col=0, squeeze=True
            )
            stemlokettenDict[year] = gpd.GeoDataFrame(a, geometry="geometry")
            bariosDict[year] = gpd.GeoDataFrame(b, geometry="geometry")
            totalsDataDict[year] = c

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
