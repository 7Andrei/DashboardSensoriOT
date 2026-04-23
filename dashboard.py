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
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
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
                dcc.Store(id="selectedNodes", data=[]),
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
                            id={"type": "nodeDot", "index": id},
                            center=coordinate[i],
                            fill=True,
                            color=nodesColors[ruolo],
                            pathOptions={"fillOpacity": 0.5},
                            opacity=1,
                            # fillOpacity=1,
                            radius=9, 
                        )
                        for i, (id, nome, ip, ruolo, lat, lon) in enumerate(nodes)
                    ],
                        style={'width': '100%', 'height': '700px'}, className='align-self-center rounded-4 shadow'
                ),

                    # html.H3("Statistics", className='text-start text-primary'),
                    html.P("Click on a node or link for more details", className='text-center text-secondary'),
                
            ],
            className='', width=5,
        ),

        #graph col
        dbc.Col([
            dbc.Row([
                dbc.Tabs(
                    id="contentTabs",
                    active_tab="tabStats",
                    children=[
                        dbc.Tab(label="Statistics", tab_id="tabStats"),
                        dbc.Tab(label="Node Info", tab_id="tabNode"),
                        dbc.Tab(label="Settings", tab_id="tabSettings"),
                    ],
                )
            ]),

            dbc.Row(id="avgStats", children=[
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Avarage temperature", className="card-subtitle text-muted"),
                            html.H4(id="avgTemp", children="-- °C", className="card-title text-danger"),
                        ], className=" rounded-4 text-center")
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Avarage humidity", className="card-subtitle text-muted"),
                            html.H4(id="avgHum", children="-- %", className="card-title text-info"),
                        ], className=" rounded-4 text-center")
                    ])
                ], width=6),
            ]),

            dbc.Row(id="clickedNodes", className='mb-4', children=[
                #callback result
            ]),

            #title and instructions
            dbc.Row([
                dbc.Col([
                    dbc.RadioItems(
                        id="sensorType", 
                        options=[
                            {"label": "Temperature", "value": "temperature"}, 
                            {"label": "Humidity", "value": "humidity"}
                        ],
                        value="temperature", 
                        inline=True, 
                        className='btn-group rounded border px-2 py-1 me-3'
                    ),
                    dbc.RadioItems(
                        id="graphTime", 
                        options=[
                            {"label": "1 Month", "value": 44640}, 
                            {"label": "1 Week", "value": 10080}, 
                            {"label": "1 Day", "value": 1440}, 
                        ],
                        value=10080, 
                        inline=True, 
                        className='btn-group rounded border px-2 py-1'
                    ),
                ], width=12,),
            ], id='controlRow'),
        ], width=7, className='rounded-4'),

    ])
], fluid=True, className='')




@callback(
    Output("selectedNodes", "data"),
    Input({"type": "nodeDot", "index": ALL}, "n_clicks"),
    Input({"type": "link", "index": ALL}, "n_clicks"),
    State("selectedNodes", "data"),
    prevent_initial_call=True,
)
def toggleNode(_nodeClick, _linkClick, selected):
    selected = selected or []
    trig = ctx.triggered_id
    if not trig:
        return selected
    if isinstance(trig, dict) and trig.get("type") == "link":
        return []
    i = trig["index"]
    if i in selected:
        selected.remove(i)   
    else:
        selected.append(i)   
    return selected

@callback(
    Output({"type": "nodeDot","index": ALL}, "pathOptions"),
    Input("selectedNodes", "data"),
)
def updateNodeOpacity(selected):
    selected = selected or []
    if not selected:
        return [{"fillOpacity": 1} for _ in nodes]

    return [{"fillOpacity": 1} if node[0] in selected else {"fillOpacity": 0.2} for node in nodes]
    

@callback(
        Output("controlRow", "style"),
        Output("avgStats", "style"),
        Input("contentTabs", "active_tab")
)
def toggleControls(activeTab):
    if activeTab=="tabStats":
        return {"display": "block"}, {"display": "flex"}
    return {"display": "none"}, {"display": "none"}

@callback(
    Output("clickedNodes", "children"),
    Input("selectedNodes", "data"),
    Input({"type": "link", "index": ALL}, "n_clicks"),
    Input("sensorType", "value"),
    Input("graphTime", "value"),
    Input("contentTabs", "active_tab")
)
def updateInfo(selected, _, sensorType, graphTime, activeTab):
    selected = selected or []
    trig = ctx.triggered_id
    linkId=-1
    if isinstance(trig, dict) and trig.get("type") == "link":
        linkId = trig["index"]
    
    if selected:
        nodesToShow=selected
    else:
        nodesToShow=[node[0] for node in nodes]
    
    if activeTab=="tabStats":

        figure=go.Figure()

        for nodeId in nodesToShow:
            results=query.getRecentReadings(nodeId, graphTime, sensorType)
            if results:
                timestamps=[reading[3] for reading in results]
                readings=[reading[4] for reading in results]
                nodeName=next((node[1] for node in nodes if node[0]==nodeId), f"Node {nodeId}")

                figure.add_trace(go.Scatter(x=timestamps, y=readings, mode='lines+markers', name=nodeName))
        
        figure.update_layout(template="plotly_white", title=f"Recent {sensorType}", title_x=0.5, yaxis_title=f"{sensorType}")
        return dcc.Graph(figure=figure)
    elif activeTab=="tabNode":
        if linkId != -1:
            linkData = next((link for link in links if link[0] == linkId), None)
            if not linkData:
                return dbc.Alert("Error retriving link data", color="danger")
            
            _, srcId, dstId, timestamp, mbps, rssi = linkData
            srcNode = next((n for n in nodes if n[0] == srcId), None)
            dstNode = next((n for n in nodes if n[0] == dstId), None)
            
            linkRow=dbc.Row([
                #source node col
                dbc.Col(html.Div([
                    html.H5(srcNode[1], className="text-success mb-0"),
                    html.Small("Source", className="text-muted")
                ], className="text-center p-3 border rounded-4 shadow bg-light"), width=4),

                #data col
                dbc.Col(html.Div([
                    html.Div(f"Speed: {mbps} Mbps", className="text-success fw-bold"),
                    html.Div(f"Strenght: {rssi} dBm", className="text-warning fw-bold")
                ], className="text-center d-flex flex-column justify-content-center h-100"), width=4),

                #destination node col
                dbc.Col(html.Div([
                    html.H5(dstNode[1], className="text-info mb-0"),
                    html.Small("Destinazione", className="text-muted")
                ], className="text-center p-3 border rounded-4 shadow bg-light"), width=4),
            ])
            linkTable=html.Div(
                dbc.Table([
                    html.Tbody([
                        html.Tr([html.Th("Timestamp", className="w-50"), html.Td(timestamp)]),
                        html.Tr([html.Th("Link ID"), html.Td(linkId)]),
                    ])
                ], bordered=False, hover=True, striped=True, className="mb-0"),
                className="mt-3 shadow rounded-4 overflow-hidden border"
            )

            return html.Div([
                html.H4("Dettagli Collegamento", className="text-center text-primary mb-4"),
                linkRow,
                linkTable
            ])
        elif not selected or len(selected)>1:
            return dbc.Alert("No node or too many nodes selected", color="warning", className="text-center")
        else:
            nodeInfo=next((node for node in nodes if node[0]==selected[0]), None)
            if nodeInfo:
                id, name, ip, role, lat, lon = nodeInfo


                nodeTable=dbc.Table([
                    html.Tbody([
                        html.Tr([html.Td("ID"), html.Td(f"{id}")]),
                        html.Tr([html.Td("Name"), html.Td(f"{name}")]),
                        html.Tr([html.Td("IP"), html.Td(f"{ip}")]),
                        html.Tr([html.Td("Role"), html.Td(f"{role}")]),
                        html.Tr([html.Td("Location"), html.Td(f"({lat}, {lon})")]),
                    ])
                ], bordered=True, hover=True, striped=True, className="mt-3 shadow rounded-4")

                recentEvents=query.getRecentEvents(id, 10)
                if recentEvents:
                    events=[
                        html.Tr([
                            html.Td(event[2]),
                            html.Td(event[3]),
                            html.Td(event[4]),
                        ]) for event in recentEvents
                    ]
                    eventTable=dbc.Table([
                        html.Thead(html.Tr([html.Th("Type"), html.Th("Description"), html.Th("Timestamp")])),
                        html.Tbody(events)
                    ], bordered=True, hover=True, striped=True, className="mt-3 shadow border rounded-4")


                return html.Div([
                    html.H4(f"{name} details", className="text-center text-primary"),
                    nodeTable,
                    html.H5("Recent events", className="text-center text-secondary mt-4"),
                    eventTable
                ])
            else:
                return dbc.Alert("Node not found", color="danger", className="text-center")


@callback(
    Output("avgTemp", "children"),
    Output("avgHum", "children"),
    Input("contentTabs", "active_tab"),
    Input("graphTime", "value"),
    Input("selectedNodes", "data")
)
def updateAvgStats(activeTab, graphTime, selected):
    if activeTab=="tabStats":
        selected = selected or []
        if selected:
            nodesToShow=selected
        else:
            nodesToShow=[node[0] for node in nodes]

        allTemps=[]
        allHums=[]

        for nodeId in nodesToShow:
            tempResults=query.getRecentReadings(nodeId, graphTime, "temperature")
            humResults=query.getRecentReadings(nodeId, graphTime, "humidity")

            allTemps.extend([reading[4] for reading in tempResults])
            allHums.extend([reading[4] for reading in humResults])

        avgTemp = round(sum(allTemps) / len(allTemps), 2) if allTemps else "--"
        avgHum = round(sum(allHums) / len(allHums), 2) if allHums else "--"

        return f"{avgTemp} °C", f"{avgHum} %"
    return "-- °C", "-- %"






if __name__ == '__main__':
    app.run(debug=True)
