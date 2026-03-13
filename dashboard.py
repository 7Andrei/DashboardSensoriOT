from dash import Dash, html, dcc, callback, Output, Input, ctx, ALL, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.express as px
import pandas as pd
import database
import query

database.main()

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

COORDINATES = [
    (42.004697, 12.676136), (42.004556, 12.675926), (42.004445, 12.675719),
    (42.004297, 12.675600), (42.004482, 12.676131), (42.004378, 12.675967),
    (42.004322, 12.675866), (42.004375, 12.676197), (42.004243, 12.676047),
    (42.004174, 12.675815)
]
LINKS = [
    (1, 2, 100.00, -45), (1, 5, 90.50, -50), (2, 3, 85.75, -55),
    (2, 6, 80.25, -60), (3, 4, 70.00, -62), (3, 7, 65.50, -65),
    (5, 6, 60.25, -68), (6, 7, 55.00, -70), (6, 9, 50.50, -72),
    (7, 10, 45.50, -75), (8, 9, 40.50, -78), (9, 10, 40.50, -80)
]


lats = [lat for lat, lon in COORDINATES]
lons = [lon for lat, lon in COORDINATES]
centerLat = (min(lats) + max(lats)) / 2
centerLon = (min(lons) + max(lons)) / 2

node_a=[45.5236, -122.6750]
node_b=[37.7749, -122.4194]

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard prova", className='text-center text-primary mb-4'), width=12)]),
    dbc.Row([
        dbc.Col(width=1),
        dbc.Col(
            children=[
                dcc.Store(id="selected-nodes", data=[]),
                dl.Map
                (
                    center=[centerLat, centerLon], 
                    zoom=19,               
                    maxZoom=30,
                    doubleClickZoom=False,            
                    children=[
                        dl.TileLayer(
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                            attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
                            maxNativeZoom=19,
                            maxZoom=30,
                        ),
                    ]+
                    [
                        dl.CircleMarker(
                            id={"type": "node-dot", "index": i},
                            center=COORDINATES[i],
                            fill=True,
                            color='blue',
                            fillOpacity=1,
                            radius=9, 
                        )
                        for i in range(len(COORDINATES))
                    ]+
                    [
                        dl.Polyline(
                            id={"type": "link", "index": i},
                            positions=[COORDINATES[n1-1], COORDINATES[n2-1]],
                            color='red',
                            weight=2,
                            opacity=0.7,
                        )
                        for i, (n1, n2, mbps, rssi) in enumerate(LINKS)
                    ],
                        style={'width': '100%', 'height': '600px'}, className='align-self-center'
                )
            ],
            className='d-flex justify-content-center', width=5,
        ),
        dbc.Col(id="clicked-node", width=5, children=[html.H2("Grafico prova")]),
        dbc.Col(width=1),
    ])
], fluid=True)




@callback(
    Output("selected-nodes", "data"),
    Input({"type": "node-dot", "index": ALL}, "n_clicks"),
    State("selected-nodes", "data"),
    prevent_initial_call=True,
)
def toggle_node(_, selected):
    selected = selected or []
    trig = ctx.triggered_id
    if not trig:
        return selected

    i = trig["index"]
    if i in selected:
        selected.remove(i)   
    else:
        selected.append(i)   
    return selected

@callback(
    Output({"type": "node-dot", "index": ALL}, "color"),
    Output({"type": "node-dot", "index": ALL}, "fillColor"),
    Input("selected-nodes", "data"),
)
def paint_selected(selected):
    selected = set(selected or [])
    colors = ["green" if i in selected else "blue" for i in range(len(COORDINATES))]
    return colors, colors

@callback(
    Output("clicked-node", "children"),
    Input("selected-nodes", "data"),
    Input({"type": "link", "index": ALL}, "n_clicks"),
)
def update_info(selected, _):
    selected = selected or []
    trig = ctx.triggered_id

    if isinstance(trig, dict) and trig.get("type") == "link":
        i = trig["index"]
        n1, n2, mbps, rssi = LINKS[i]
        return f"Arco cliccato da {n1} a {n2} Mbps: {mbps} RSSI: {rssi}"

    return f"Nodi selezionati: {selected}"








if __name__ == '__main__':
    app.run(debug=True)
