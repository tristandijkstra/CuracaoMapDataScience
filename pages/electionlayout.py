import dash
from dash import (
    dcc,
    html,
    register_page
)
from datetime import datetime

register_page(__name__, path='/')


topLayer = html.Div(
    id="toplayer",
    children=[
        html.Div(id="fullscreenloader", children=["Loading Election Map"]),
    ],
)


mainApp = html.Div(
    className="appPage",
    children=[
        html.Div(
            id="control",
            className="controlbar",
            children=[
                html.Div(
                    id="info",
                    className="infobar",
                    children=[
                        # dcc.Loading(id="loadingbar"),
                        # html.Div(className="loaderParent", children=html.Div(className="loader")),
                        dcc.Link("About", id="aboutbutton", className="infobarItem", href="/about"),
                        # dcc.Link("Seats", id="seatsbutton", className="infobarItem", href="/seats"),
                        dcc.Link("How to", id="disclaimerbutton", className="infobarItem", href="/how-to"),
                    ],
                ),
                html.Div(
                    # id="dropdowns",
                    className="dropdowns",
                    children=[
                        html.Div(
                            id="dddiv1",
                            className="dropdown",
                            children=[
                                html.P("Election Year:"),
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
                            className="dropdown",
                            children=[
                                html.P("Bar Chart:"),
                                dcc.Dropdown(
                                    id="comparativeCL",
                                    options=[
                                        {"label": "Off", "value": "off"},
                                        {"label": "Simple", "value": "simple"},
                                        {
                                            "label": "Comparative",
                                            "value": "comparative",
                                        },
                                    ],
                                    multi=False,
                                    value="simple",
                                    searchable=False,
                                    clearable=False,
                                    placeholder="on/off",
                                ),
                            ],
                        ),
                        html.Div(
                            id="dddiv3",
                            className="dropdown",
                            children=[
                                html.P("Clustering:"),
                                dcc.Dropdown(
                                    id="clustersDD",
                                    options=[
                                        {"label": "No Clustering", "value": 0},
                                        {"label": "3 clusters", "value": 3},
                                        {"label": "5 clusters", "value": 5},
                                        {"label": "10 clusters", "value": 10},
                                        {"label": "15 clusters", "value": 15},
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
                            className="dropdown",
                            children=[
                                html.P("Representation:"),
                                dcc.Dropdown(
                                    id="NumberStyleDD",
                                    options=[
                                        {
                                            "label": "Number of Voters",
                                            "value": "Numbers",
                                        },
                                        {"label": "Percentage", "value": "Percentage"},
                                    ],
                                    placeholder="Number representation",
                                    multi=False,
                                    searchable=False,
                                    clearable=False,
                                    value="Percentage",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="graphs",
            className="graphs",
            children=[
                dcc.Graph(
                    id="map",
                    figure={},
                ),
                html.Div(
                    id="barcontainer",
                    children=[
                        dcc.Graph(
                            id="bar",
                            figure={},
                        )
                    ],
                ),
            ],
        ),
        html.Div(f"© {datetime.now().year} Tristan Dijkstra", className="copyrightbar")
    ],
)

layout = html.Div(id="fullapp", children=[topLayer, mainApp])