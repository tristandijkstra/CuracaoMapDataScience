from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
import pandas as pd
import numpy as np
from tqdm import tqdm
import geojson
import os
from glob import glob

import geopandas as gpd

# import pysal as ps
from sklearn import cluster

import plotly.express as px

# nominatim = Nominatim()
# areaId = nominatim.query('curacao').areaId()
CuracaoID = 3602867318
CuracaoCentre = [12.2066695, -68.9351307]  # lat lon


def geojsonToGeopandas(listOfGeojson):
    P = (
        gpd.GeoDataFrame(listOfGeojson, geometry="geometry")
        .set_index("id")
        .assign(randNumCol=lambda x: np.random.randint(1, 6))
        .assign(area=lambda x: x.geometry.area * 10e6)
        .assign(invarea=lambda x: 1 / x.area)
        .assign(lat=lambda x: x.geometry.centroid.x)
        .assign(lon=lambda x: x.geometry.centroid.y)
        .set_geometry(col="geometry")
    )
    return P


def removeOverlap(P, verbose=True):
    P = P.sort_values("area", ascending=False)
    P = P.drop(["Piscadera Baai"])  # i like the alias veeris better
    P = P.drop(["San Juan"])  # does not work automatically goes in pannekoek
    duplicateBarios = []
    for bario, row in P.iterrows():
        for bario2, row2 in P.iterrows():
            # skip if it comes across itself or finds a bigger bario
            if (bario == bario2) or row2.area > row.area:
                continue
            # add alias barios for deletion
            if (row2.area == row.area) and (bario not in duplicateBarios):
                duplicateBarios.append(bario2)
                continue
            # delete smaller barios that are inside bario1
            if row.geometry.contains(row2.geometry):
                if verbose:
                    print(bario, row.area, "<-", bario2, row2.area)
                P = P.drop([bario2])

    # remove aliased barios
    P = P.drop(duplicateBarios)
    return P


def generateGeoJSON(
    areaID,
    forceRegenerate=False,
    save=True,
    saveFolder=r"geojsondata",
    verbose=True
):

    if not os.path.exists(saveFolder) or forceRegenerate:
        print("Generating geojson data")
        if not forceRegenerate:
            os.makedirs(saveFolder)

        overpass = Overpass()
        queryNeighbourhoods = overpassQueryBuilder(
            area=areaID,
            elementType="relation",
            selector='"place"="neighbourhood"',
            # includeCenter=True,
            includeGeometry=True,
        )
        queryAreas = overpassQueryBuilder(
            area=areaID,
            elementType="relation",
            selector='"boundary"="area"',
            # includeCenter=True,
            includeGeometry=True,
        )
        queryCentre = overpassQueryBuilder(
            area=areaID,
            elementType="relation",
            selector='"place"="suburb"',
            # includeCenter=True,
            includeGeometry=True,
        )

        neighbourhoods = overpass.query(queryNeighbourhoods)
        citycentre = overpass.query(queryCentre)
        areas = overpass.query(queryAreas)
        combined = (
            neighbourhoods.relations() + areas.relations() + citycentre.relations()
        )

        barios = []
        for bario in tqdm(combined):
            # Generate JSON
            entry = {
                "id": bario.tag("name"),
                "geometry": bario.geometry(),
            }

            barios.append(entry)

        if save:
            print("Saving geojson data")
            for idx, bario in tqdm(enumerate(barios)):
                filename = str(idx) + (
                    bario["id"]
                    .replace(" ", "")
                    .replace("/", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                with open(f"{saveFolder}/{filename}.json", "w") as file:
                    geojson.dump(bario, file)

        P = geojsonToGeopandas(barios)
        P.index = P.index.str.replace(" \(zone\)", "")#.strip()
        P = removeOverlap(P, verbose=verbose)

        # remove the word zone

        return P

    else:
        print("Loading geojson data")
        listOfFiles = glob(f"{saveFolder}/[!_full]*.json")
        barios = []

        for file in tqdm(listOfFiles):
            with open(file, "r") as file:
                barios.append(geojson.load(file))

        P = geojsonToGeopandas(barios)
        P.index = P.index.str.replace(" \(zone\)", "")#.strip()
        P = removeOverlap(P, verbose=verbose)

        # remove the word zone

        return P


if __name__ == "__main__":
    # Run and plot barios

    barios = generateGeoJSON(CuracaoID, forceRegenerate=False)

    model = cluster.KMeans(20)
    # print("hello")
    # print(type(barios["centroid"].iloc[0]))
    X = barios[["lat", "lon"]]

    barios["cluster"] = model.fit_predict(X)

    fig = px.choropleth_mapbox(
        data_frame=barios,
        geojson=barios.geometry,
        locations=barios.index,
        # featureidkey="properties.name",
        hover_data=["lat", "lon", "randNumCol", "area", "cluster"],
        color="cluster",
        color_continuous_scale="Viridis",
        # range_color=(0, 12),
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=0.5,
    )
    fig.show()

    barios = barios.dissolve(by="cluster", aggfunc="sum")
    fig = px.choropleth_mapbox(
        data_frame=barios,
        geojson=barios.geometry,
        locations=barios.index,
        # featureidkey="properties.name",
        hover_data=["lat", "lon", "randNumCol", "area"],
        color=barios.index,
        color_continuous_scale="Viridis",
        # range_color=(0, 12),
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": CuracaoCentre[0], "lon": CuracaoCentre[1]},
        opacity=0.5,
    )
    fig.show()
