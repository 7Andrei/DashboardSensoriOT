from dash import Dash, html, dcc, callback, Output, Input, ctx, ALL, State, no_update
from dash.exceptions import PreventUpdate
from colour import Color
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.express as px
import pandas as pd
import database
import query
import time #non necessario

database.main()
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
#linkId, node1, node2, timestamp, mbps, rssi
links=query.getLinks()

timestamp=int(time.time())
links=[(id, src, dst, timestamp, avgRssi, avgQuality) for id, (src, dst, avgRssi, avgQuality) in enumerate(links)]

#nodeID, name, ip, role, lat, long
# nodes=query.getNodi()
nodes=query.getNodes()
ip='192.168.1.1'
nodes=[(id, name, ip, role, lat, lon) for (id, name, lat, lon, _polling, _sleepPolicy,  role, _timestamp, _version, _comment) in nodes]

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
nodesColors={"leader":"red", "leaf": "green", "router": "blue"}

coordinate=[(nodo[4], nodo[5]) for nodo in nodes]
lats = [lat for lat, lon in coordinate]
lons = [lon for lat, lon in coordinate]


def buildLayout():
    # links=query.getLinks()
    # nodes=query.getNodi()
    # nodes=query.getNodes()

    coordinates=[(nodo[4], nodo[5]) for nodo in nodes]
    lats = [lat for lat, lon in coordinates]
    lons = [lon for lat, lon in coordinates]
    nodePositions={node[0]: (node[4], node[5]) for node in nodes}

    return dbc.Container([
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
                dcc.Store(id="allowMove", data=False),
                dl.Map
                (
                    id="nodeMap",
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
                            positions=[nodePositions[n1], nodePositions[n2]],
                            color=str(linksColors[Rssi[i]]),
                            weight=Mbps[i],
                            opacity=0.5,
                        )
                        for i, (id, n1, n2, data, mbps, rssi) in enumerate(links)
                    ]+
                    [
                        dl.CircleMarker(
                            id={"type": "nodeDot", "index": id},
                            center=coordinates[i],
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

                    html.P("Click on a node or link for more details", className='text-center text-secondary'),
                    dbc.Button("Reset Selection", id="reset", color="secondary", className="text-start"),
                    dbc.Button("Move node", id="moveNode", color="warning", className="text-end ms-3", n_clicks=0)
                
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

app.layout = buildLayout



@callback(
    Output("selectedNodes", "data"),
    Input({"type": "nodeDot", "index": ALL}, "n_clicks"),
    Input({"type": "link", "index": ALL}, "n_clicks"),
    Input("reset", "n_clicks"),
    State("selectedNodes", "data"),
    prevent_initial_call=True,
)
def toggleNode(_nodeClick, _linkClick, _resetClick, selected):
    selected = selected or []
    trig = ctx.triggered_id
    if not trig:
        return selected
    if trig == "reset":
        return []
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
    State("nodesData", "data")
)
def updateNodeOpacity(selected, nodesData):
    selected = selected or []
    if not selected:
        return [{"fillOpacity": 1} for _ in nodesData]

    return [{"fillOpacity": 1} if node[0] in selected else {"fillOpacity": 0.2} for node in nodesData]
    

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
    Input("contentTabs", "active_tab"),
    Input("nodesData", "data"),
    Input("linksData", "data")
)
def updateInfo(selected, _, sensorType, graphTime, activeTab, nodesData, linksData):
    selected = selected or []
    trig = ctx.triggered_id
    linkId=-1
    if isinstance(trig, dict) and trig.get("type") == "link":
        linkId = trig["index"]
    
    if selected:
        nodesToShow=selected
    else:
        nodesToShow=[node[0] for node in nodesData]
    
    if activeTab=="tabStats":

        figure=go.Figure()

        for nodeId in nodesToShow:
            results=query.getRecentReadings(nodeId, graphTime, sensorType)
            if results:
                timestamps=[reading[3] for reading in results]
                readings=[reading[4] for reading in results]
                nodeName=next((node[1] for node in nodesData if node[0]==nodeId), f"Node {nodeId}")

                figure.add_trace(go.Scatter(x=timestamps, y=readings, mode='lines+markers', name=nodeName))
        
        figure.update_layout(template="plotly_white", title=f"Recent {sensorType}", title_x=0.5, yaxis_title=f"{sensorType}")
        return dcc.Graph(figure=figure)
    elif activeTab=="tabNode":
        if linkId != -1:
            linkData = next((link for link in linksData if link[0] == linkId), None)
            if not linkData:
                return dbc.Alert("Error retriving link data", color="danger")
            
            _, srcId, dstId, timestamp, mbps, rssi = linkData
            srcNode = next((n for n in nodesData if n[0] == srcId), None)
            dstNode = next((n for n in nodesData if n[0] == dstId), None)
            
            linkRow=dbc.Row([
                #source node col
                dbc.Col(html.Div([
                    dbc.Button(srcNode[1], id={"type": "nodeButton", "index": srcId}, color="success", className="mb-0 text-center d-inline-block"),
                    html.Small("Source", className="text-muted d-block")
                ], className="text-center p-3 border rounded-4 shadow bg-light"), width=4),

                #data col
                dbc.Col(html.Div([
                    html.Div(f"Speed: {mbps} Mbps", className="text-success fw-bold"),
                    html.Div(f"Strenght: {rssi} dBm", className="text-warning fw-bold")
                ], className="text-center d-flex flex-column justify-content-center h-100"), width=4),

                #destination node col
                dbc.Col(html.Div([
                    dbc.Button(dstNode[1], id={"type": "nodeButton", "index": dstId}, color="info", className="mb-0 text-center d-inline-block"),
                    html.Small("Destination", className="text-muted d-block")
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
        elif not selected:
            return dbc.Alert("No node or too many nodes selected", color="warning", className="text-center")
        elif len(selected)>1:
            nodeTable=dbc.Table([
                html.Thead(html.Tr([html.Th("ID"), html.Th("Name"), html.Th("IP"), html.Th("Role"), html.Th("Location")])),
                html.Tbody([
                    html.Tr([
                        html.Td(node[0]),
                        html.Td(node[1]),
                        html.Td(node[2]),
                        html.Td(node[3]),
                        html.Td(f"({node[4]}, {node[5]})"),
                    ]) for node in nodesData if node[0] in selected
                ])
            ], bordered=True, hover=True, striped=True, className="mt-3 rounded-4")
            return html.Div([
                html.H4("Selected nodes", className="text-center text-primary mt-4"),
                nodeTable
            ])
        else:
            nodeInfo=next((node for node in nodesData if node[0]==selected[0]), None)
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

                eventTable=html.Div("No recent events", className="text-center text-muted mt-3")
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
                nodeLinks=[]
                for nodeLink in linksData:
                    # TODO Modificare tabella per aggiungere pulsanti verso i nodi
                    if nodeLink[1]==id or nodeLink[2]==id:
                        nodeLinks.append(
                            html.Tr([
                                html.Td(nodeLink[0]),
                                html.Td(nodeLink[1] if nodeLink[1]==id else nodeLink[2]),
                                html.Td(nodeLink[2] if nodeLink[2]!=id else nodeLink[1]),
                                html.Td(nodeLink[3]),
                                html.Td(nodeLink[4]),
                                html.Td(nodeLink[5]),
                            ])
                        )
                nodeLinksTable=dbc.Table([
                    html.Thead(html.Tr([html.Th("Link ID"), html.Th("Source node"), html.Th("Destination node"), html.Th("Timestamp"), html.Th("Mbps"), html.Th("Rssi")])),
                    html.Tbody(nodeLinks)
                ], bordered=True, hover=True, striped=True, className="mt-3 shadow border rounded-4")

                return html.Div([
                    html.H4(f"{name} details", className="text-center text-primary mt-4"),
                    nodeTable,
                    html.H5("Recent events", className="text-center text-secondary mt-4"),
                    eventTable,
                    html.H5("Related links", className="text-center text-secondary mt-4"),
                    nodeLinksTable
                ])
            else:
                return dbc.Alert("Node not found", color="danger", className="text-center")


@callback(
    Output("avgTemp", "children"),
    Output("avgHum", "children"),
    Input("contentTabs", "active_tab"),
    Input("graphTime", "value"),
    Input("selectedNodes", "data"),
    State("nodesData", "data")
)
def updateAvgStats(activeTab, graphTime, selected, nodesData):
    if activeTab=="tabStats":
        selected = selected or []
        if selected:
            nodesToShow=selected
        else:
            nodesToShow=[node[0] for node in nodesData]

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

@callback(
    Output("nodesData", "data"),
    Output({"type": "nodeDot", "index": ALL}, "center"),
    Output({"type": "link", "index": ALL}, "positions"),
    Output("allowMove", "data"),
    Input("nodeMap", "clickData"),
    State("nodesData", "data"),
    State("linksData", "data"),
    State("selectedNodes", "data"),
    State("allowMove", "data"),
    prevent_initial_call=True,
)
def moveNode(clickData, nodesData, linksData, selectedNodes, allowMove):
    if not allowMove or not clickData or len(selectedNodes or [])!=1:
        raise PreventUpdate
    
    nodeId=selectedNodes[0]
    lat=clickData["latlng"]["lat"]
    lon=clickData["latlng"]["lng"]

    query.updateNodePosition(nodeId, lat, lon)

    newNodes=[list(node) for node in nodesData]
    for node in newNodes:
        if node[0]==nodeId:
            node[4]=lat
            node[5]=lon
            break

    centers=[(node[4], node[5]) for node in newNodes]
    nodePositions={node[0]:[node[4], node[5]] for node in newNodes}
    newLinks=[[nodePositions[link[1]], nodePositions[link[2]]] for link in linksData]

    return newNodes, centers, newLinks, False

@callback(
    Output("allowMove", "data", allow_duplicate=True),
    Input("moveNode", "n_clicks"),
    Input("reset", "n_clicks"),
    State("selectedNodes", "data"),
    prevent_initial_call=True,
)
def allowMoveNode(_allow, _reset, selectedNodes):
    trig=ctx.triggered_id
    if trig=="reset":
        return False
    if len(selectedNodes or [])!=1:
        return False
    return True

@callback(
    Output("moveNode", "disabled"),
    Input("selectedNodes", "data")
)
def disableMove(selectedNodes):
    if len(selectedNodes or [])!=1:
        return True
    return False

# @callback(
#     # fix duplicate
#     Output("selectedNodes", "data", allow_duplicate=True),
#     Output("contentTabs", "active_tab"),
#     Input({"type": "nodeButton", "index": ALL}, "n_clicks"),
#     State("selectedNodes", "data"),
#     prevent_initial_call=True,
# )
# def nodeButtonClick(n_clicks, selectedNodes):
#     trig=ctx.triggered_id
#     if not trig or not isinstance(trig, dict):
#         raise PreventUpdate
    
#     nodeId=trig["index"]
#     return [nodeId], "tabNode"


if __name__ == '__main__':
    app.run(debug=True)
