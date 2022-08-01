from dash import dcc, html, register_page


register_page(__name__, path="/how-to")

nosLink = "https://nos.nl/collectie/13860/artikel/2373037-bekijk-hier-de-uitslagen-van-de-verkiezingen"
win270Link = "https://www.270towin.com/2020-election-results-live/"
kseLink = "http://kse.cw/"
osmLink = "https://www.openstreetmap.org/#map=11/12.2093/-68.9456"

layout = (
    html.Div(
        id="about",
        # style={"display": "inline"},
        children=[
            dcc.Link(
                "Close", className="menuExit infobarItem", href="/"
            ),
            html.Div(
                className="aboutInner",
                children=[
                    html.H1("How to use"),
                    html.P(
                        children=[
                            "Please refer to the ",
                            html.A(
                                children=[
                                    html.Span(className="linkeffect"),
                                    "about page",
                                ],
                                href="/about",
                                className="inlineLink",
                            ),
                            " first for general info and the disclaimer. ",
                        ]
                    ),
                    html.H3("General Use"),
                    html.P(
                        children=[
                            "With the map you can see winners of the various neighborhoods and voting halls on the island. ",
                            "The bar chart shows overall results of the election. ",
                            "Clicking on one of the zones or voting halls opens the local results on the bar chart."
                        ]
                    ),
                    html.H3("Options"),
                    html.P(
                        children=[
                            "The options can be found at the top:",
                            html.Br(),
                            " - Election year: election year to show on the map",
                            html.Br(),
                            " - Bar chart: Simple bar chart shows results for chosen election year, comparative shows multiple years",
                            html.Br(),
                            " - Clustering: Clustering combines multiple barios, showing a representation for a larger region. ",
                            "Note: Because of the nature of clustering, less populated zones might appear to flip parties. This could lead to potentially misleading maps.",
                            html.Br(),
                            " - Representation: show votes as percentage or absolute number of voters",
                            html.Br(),
                        ]
                    ),


                ],
            ),
        ],
    ),
)
