from dash import dcc, html, register_page


register_page(__name__, path="/about")

nosLink = "https://nos.nl/collectie/13860/artikel/2373037-bekijk-hier-de-uitslagen-van-de-verkiezingen"
win270Link = "https://www.270towin.com/2020-election-results-live/"
kseLink = "http://kse.cw/"
osmLink = "https://www.openstreetmap.org/#map=11/12.2093/-68.9456"
emailLink = 'mailto: tristandijkstra@protonmail.com?subject= &body= ""'

layout = (
    html.Div(
        id="about",
        # style={"display": "inline"},
        children=[
            dcc.Link(
                "Close", id="aboutbutton", className="menuExit infobarItem", href="/"
            ),
            html.Div(
                className="aboutInner",
                children=[
                    html.H1("About the project"),
                    html.P(
                        children=[
                            "This tool was made to resemble election maps found in other countries, for example in ",
                            html.A(
                                children=[
                                    html.Span(className="linkeffect"),
                                    "the Netherlands",
                                ],
                                href=nosLink,
                                className="inlineLink",
                            ),
                            " and ",
                            html.A(
                                children=[html.Span(className="linkeffect"), "the US"],
                                href=win270Link,
                                className="inlineLink",
                            ),
                            ". It was created in 2022 as a summer project out of curiosity and as an opportunity to improve my data visualisation skill.",
                        ]
                    ),
                    html.P(
                        "Although not as pronounced as in other countries, \
                             the tool still reveals some historical and regional voter patterns. In general, it also provides \
                                a more intuitive method of understanding and comparing elections, previously unavailable to Curaçao."
                    ),
                    html.H2("Disclaimer"),
                    html.P(
                        children=[
                            "For the official election results, please visit the Konseho Supremo Electoral's (KSE) ",
                            html.A(
                                children=[
                                    html.Span(className="linkeffect"),
                                    "offical website",
                                ],
                                href=kseLink,
                                className="inlineLink",
                            ),
                            ". ",
                        ]
                    ),
                    html.P(
                        children=[
                            "I am in no way affiliated with the KSE nor any party that has participated in any of these elections. ",
                            "Discrepancies between my data and that provided by KSE are honest mistakes and are not intentional nor meant to mislead the user. ",
                            "Please feel free to contact me for corrections. ",
                        ]
                    ),
                    html.P(
                        children=[
                            "The clustering tool provided on this site provides a more generalised view in return for a lower positional accuracy in results. ",
                            "The zones/barios do not provide an exact location of voters. Voters may for example vote outside their barios and not all barios have a voting hall.",
                        ]
                    ),
                    html.P(
                        children=[
                            "I do not have an education in political science nor any related field.\
                                 Any expertise in politics is purely hobbyistic.\
                                     Thus I do not, nor will I ever provide any form of analysis concerning the data provided here. ",
                            "If you do have such expertice or represent a local government agency and would like to collaborate for a research effort, please feel free to contact me.",
                        ]
                    ),
                    html.H2("Contact"),
                    html.P(
                        children=[
                            "You can contact me here: ",
                            html.A(
                                children=[html.Span(className="linkeffect"), "tristandijkstra@protonmail.com"],
                                href=emailLink,
                                className="inlineLink",
                            ),
                        ]
                    ),
                    html.H2("Sources"),
                    html.P(
                        children=[
                            " - Election results and voting Offices: ",
                            html.A(
                                children=[
                                    html.Span(className="linkeffect"),
                                    "Konseho Supremo Electoral",
                                ],
                                href=kseLink,
                                className="inlineLink",
                            ),
                            ".",
                            html.Br(),
                            " - Geographical data including barios/zones: ",
                            html.A(
                                children=[
                                    html.Span(className="linkeffect"),
                                    "Open Street Map",
                                ],
                                href=kseLink,
                                className="inlineLink",
                            ),
                            ".",
                            html.Br(),
                        ]
                    ),
                ],
            ),
        ],
    ),
)
