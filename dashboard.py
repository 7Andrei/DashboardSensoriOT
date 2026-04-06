from dash import Dash, html, dcc, callback, Output, Input, ctx, ALL, State
from colour import Color
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.express as px
import pandas as pd
import database
import query

database.main()
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

#linkId, node1, node2, timestamp, mbps, rssi
links=query.getLinks()

#nodeID, name, ip, role, lat, long
nodes=query.getNodi()

#sensorID, nodeId, sensor type, timestamp, value
#60=1h, 1440=1day, 44640=31days
# for node in nodes: 
#     readings=query.getRecentReadings(node[0], 44640, "temperature")
#     # print(readings)
#     print("-----------------------------")




maxMbps = max(link[4] for link in links)
minMbps = min(link[4] for link in links)
rangeMbpsOld = maxMbps - minMbps
Mbps=[]
for i in range(len(links)):
    oldValue = links[i][4]
    newValue = int((((oldValue - minMbps) * 10) / rangeMbpsOld) + 2)
    Mbps.append(newValue)

maxRssi = max(link[5] for link in links)
minRssi = min(link[5] for link in links)
rangeRssiOld = maxRssi - minRssi
Rssi=[]
for i in range(len(links)):
    oldValue = links[i][5]
    newValue = int(((oldValue - minRssi) * 19) / rangeRssiOld)
    Rssi.append(newValue)

linksColors= list(Color("red").range_to(Color("green"), 20))
nodesColors={"Router":"red", "Child": "green", "Parent": "blue"}

coordinate=[(nodo[4], nodo[5]) for nodo in nodes]
lats = [lat for lat, lon in coordinate]
lons = [lon for lat, lon in coordinate]

app.layout = dbc.Container([
    dcc.Store(id="linksData", data=links),
    dcc.Store(id="nodesData", data=nodes),

    #title row
    dbc.Row([
        dbc.Col(html.H1("Dashboard prova", className='text-center text-primary mb-4'), width=12)]),

    #main row
    dbc.Row([

        # #spacer col
        # dbc.Col(width=1),

        #map col
        dbc.Col(
            children=[
                dcc.Store(id="selected-nodes", data=[]),
                dl.Map
                (
                    bounds=[[min(lats), min(lons)], [max(lats), max(lons)]],
                    boundsOptions={"padding": [40, 40]},
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
                        dl.Polyline(
                            id={"type": "link", "index": id},
                            positions=[coordinate[n1-1], coordinate[n2-1]],
                            color=str(linksColors[Rssi[i]]),
                            weight=Mbps[i],
                            opacity=0.5,
                        )
                        for i, (id, n1, n2, data, mbps, rssi) in enumerate(links)
                    ]+
                    [
                        dl.CircleMarker(
                            id={"type": "node-dot", "index": id},
                            center=coordinate[i],
                            fill=True,
                            color=nodesColors[ruolo],
                            fillOpacity=1,
                            radius=9, 
                        )
                        for i, (id, nome, ip, ruolo, lat, lon) in enumerate(nodes)
                    ],
                        style={'width': '100%', 'height': '700px'}, className='align-self-center rounded-4'
                )
            ],
            className='d-flex justify-content-center shadow-sm ms-4', width=5,
        ),

        #graph col
        dbc.Col(width=5, children=[

            #title and instructions
            dbc.Row([

                dbc.Col([
                    html.H3("Statistics", className='text-start text-primary'),
                    html.P("Click on a node or link for more details", className='text-start text-secondary'),
                ], width=6),

                dbc.Col([
                    dbc.RadioItems(
                        id="sensorType", 
                        options=[
                            {"label": "Temperature", "value": "temperature"}, 
                            {"label": "Humidity", "value": "humidity"}
                        ],
                        value="temperature", 
                        inline=True, 
                        className='btn-group-vertical'
                    ),
                ], width=3, className='d-flex justify-content-end'),

                dbc.Col([
                    dbc.RadioItems(
                        id="graphTime", 
                        options=[
                            {"label": "1 Month", "value": 44640}, 
                            {"label": "1 Week", "value": 10080}, 
                            {"label": "1 Day", "value": 1440}, 
                        ],
                        value=10080, 
                        inline=True, 
                        className='btn-group-vertical'
                    ),
                ], width=3, className='d-flex justify-content-end'),

            ], className='mb-4'),

            #graph row
            dbc.Row(id="clickedNodes", className='mb-4', children=[
                
            ]),
        ]),

        #spacer col
        dbc.Col([
            html.H5("aaaaa")
        ],width=1, className='bg-white d-flex'),
    ])
], fluid=True, className='bg-dark text-white min-vh-100')




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
    Output("clickedNodes", "children"),
    Input("selected-nodes", "data"),
    Input({"type": "link", "index": ALL}, "n_clicks"),
    Input("sensorType", "value"),
    Input("graphTime", "value")
)
def update_info(selected, _, sensorType, graphTime):
    selected = selected or []
    trig = ctx.triggered_id

    if isinstance(trig, dict) and trig.get("type") == "link":
        i = trig["index"]
        _, n1, n2, data, mbps, rssi = links[i]
        return f"Arco cliccato da {n1} a {n2} Mbps: {mbps} RSSI: {rssi}"
    
    if selected:
        nodesToShow=selected
    else:
        nodesToShow=[node[0] for node in nodes]
    
    figure=go.Figure()

    for nodeId in nodesToShow:
        results=query.getRecentReadings(nodeId, graphTime, sensorType)
        if results:
            timestamps=[reading[3] for reading in results]
            readings=[reading[4] for reading in results]
            nodeName=next((node[1] for node in nodes if node[0]==nodeId), f"Node {nodeId}")

            figure.add_trace(go.Scatter(x=timestamps, y=readings, mode='lines+markers', name=nodeName))
    
    figure.update_layout(template="plotly_dark", title=f"Recent {sensorType}", title_x=0.5, yaxis_title=f"{sensorType}")
    return dcc.Graph(figure=figure)








if __name__ == '__main__':
    app.run(debug=True)
