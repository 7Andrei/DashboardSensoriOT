from dash import Dash, html, dcc, callback, Output, Input, ctx, ALL, State, no_update, clientside_callback, ClientsideFunction
from dash.exceptions import PreventUpdate
from colour import Color
from datetime import datetime, timedelta
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.express as px
import pandas as pd
import database
import query

database.main()
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
#sensorID, nodeId, sensor type, timestamp, value
def setColors(links):
    maxRssi = max(link[3] for link in links)
    minRssi = min(link[3] for link in links)
    rangeRssiOld = maxRssi - minRssi
    Rssi=[]
    for i in range(len(links)):
        oldValue = links[i][3]
        newValue = int(((oldValue - minRssi) * 19) / rangeRssiOld)
        Rssi.append(newValue)
    return Rssi

linksColors= list(Color("red").range_to(Color("green"), 20))
nodesColors={"leader":"red", "leaf": "green", "router": "blue"}

def buildLayout():
    #linkId, scrNode, dstNode, avgRssi, avgQuality
    links=query.getLinks()
    links=[(id, *link) for id, link in enumerate(links)]
    Rssi = setColors(links)

    #nodeEUI, name, lat, lon, polling, sleepPolicy, role, timestamp, version, comment
    nodes=query.getNodes()
    coordinates=[(nodo[2], nodo[3]) for nodo in nodes]
    lats = [lat for lat, lon in coordinates]
    lons = [lon for lat, lon in coordinates]
    nodePositions={node[0]: (node[2], node[3]) for node in nodes}

    return dbc.Container([
    dcc.Store(id="linksData", data=links),
    dcc.Store(id="nodesData", data=nodes),

    #title row
    dbc.Row([
        dbc.Col(html.H1("Dashboard", className='text-center text-primary mb-4'), width=12)]),

    #main row
    dbc.Row([
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
                            id="baseMap",
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
                            weight=8,
                            opacity=0.5,
                        )
                        for i, (id, n1, n2, rssi, mbps) in enumerate(links)
                    ]+
                    [
                        dl.CircleMarker(
                            id={"type": "nodeDot", "index": eui},
                            center=coordinates[i],
                            fill=True,
                            color=nodesColors[role],
                            pathOptions={"fillOpacity": 0.5},
                            opacity=1,
                            radius=9, 
                        )
                        for i, (eui, _label, _lat, _lon, _polling, _sleepPolicy, role, _created, _version, _comment) in enumerate(nodes)
                    ]+
                    [
                        dl.CircleMarker(
                            id="previewNode",
                            center=(0, 0),
                            fill=True,
                            pathOptions={"dashArray": "6, 6"},
                            color="grey",
                            radius=9,
                        )
                    ],
                    style={'width': '100%', 'height': '700px'}, className='align-self-center rounded-4 shadow'
                ),

                    html.Div(
                        style={
                            'position': 'absolute',
                            'bottom': '150px',
                            'left': '15px',
                            'zIndex': '1000',
                        },
                        children=[
                            html.H5("Node roles", className="text-secondary"),\
                            html.Div([
                                html.Div("Leader", className="text-danger"),
                                html.Div("Router", className="text-primary"),
                                html.Div("Leaf", className="text-success"),
                            ],)
                        ],
                        className="bg-light p-2 rounded-4 shadow-sm"
                    ),
                    html.Div(
                        style={
                            'position': 'absolute',
                            'bottom': '150px',
                            'left': '135px',
                            'zIndex': '1000',
                        },
                        children=[
                            html.H5("Link RSSI", className="text-secondary"),\
                            html.Div([
                                html.Div("Weakest", className="text-danger"),
                                html.Div("Strongest", className="text-success"),
                            ],)
                        ],
                        className="bg-light p-2 rounded-4 shadow-sm"
                    ),

                    html.P("Click on a node or link for more details", className='text-center text-secondary'),
                    dbc.Button("Reset Selection", id="reset", color="secondary", className="text-start"),
                    dbc.RadioItems(
                        id="mapStyle",
                        options=[
                            {"label": "Satellite", "value": "satellite"},
                            {"label": "OpenStreetMap", "value": "osm"},
                        ],
                        value="satellite",
                        className='btn-group',
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                    )
                
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
                            html.H4("Average temperature", className="card-subtitle text-muted"),
                            html.H4(id="avgTemp", children="-- °C", className="card-title text-danger"),
                        ], className=" rounded-4 text-center")
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Average humidity", className="card-subtitle text-muted"),
                            html.H4(id="avgHum", children="-- %", className="card-title text-info"),
                        ], className=" rounded-4 text-center")
                    ])
                ], width=6),
            ]),

            dbc.Row(id="clickedNodes", className='mb-4', children=[
                #callback result
            ]),

            dbc.Row(id="settingsRow", children=[
                dbc.Col([
                    html.H4("Node settings", className="card-title text-center mb-3")
                ], width=12),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
            
                            # html.P("Click on a single node, then click the 'Move node' button, then click on the map to move the node to the desired position", className="card-text text-center"),
                            dbc.Input(id="newLat", type="number", placeholder="New latitude", className="mt-3", step=0.001),
                            dbc.Input(id="newLon", type="number", placeholder="New longitude", className="mt-3", step=0.001),
                            dbc.Button("Move node", id="moveNode", color="warning", className="text-end mt-3", n_clicks=0),
                            dbc.Button("Use my location", id="getLocation", color="info", className="text-end mt-3 ms-2", n_clicks=0),
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Input(id="newPollingRate", type="number", min=1, placeholder="New polling rate (s)", className="mt-3"),
                            dbc.Button("Update polling rate", id="updatePolling", color="warning", className="text-end mt-3", n_clicks=0),
                        ])
                    ])
                ], width=6),
            ]),

            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div([
                            dbc.RadioItems(
                                id="sensorType", 
                                options=[
                                    {"label": "Temperature", "value": "temperature"}, 
                                    {"label": "Humidity", "value": "humidity"},
                                    {"label": "Pressure", "value": "pressure"},
                                    {"label": "Gas", "value": "gas"},
                                ],
                                value="temperature", 
                                className='btn-group',
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary",
                                labelCheckedClassName="active",
                            ),
                            dbc.Select(
                                id="gasType",
                                options=[
                                    {"label": "0", "value": 0}, 
                                    {"label": "1", "value": 1},
                                    {"label": "2", "value": 2},
                                    {"label": "3", "value": 3},
                                    {"label": "4", "value": 4},
                                    {"label": "5", "value": 5},
                                    {"label": "6", "value": 6},
                                    {"label": "7", "value": 7},
                                    {"label": "8", "value": 8},
                                    {"label": "9", "value": 9},
                                ],
                                placeholder="Select gas",
                                className="form-select shadow-sm",
                            ),
                            ], className="d-flex align-items-center gap-3"),
                            html.Div([
                                dcc.DatePickerRange(
                                    id='dateRange',
                                    display_format='YYYY-MM-DD',
                                    className="btn-group",
                                ),
                                dbc.RadioItems(
                                    #values in minutes
                                    id="graphTime", 
                                    options=[
                                        # {"label": "1 Month", "value": 60*24*31}, 
                                        {"label": "1 Week", "value": 60*24*7}, 
                                        {"label": "1 Day", "value": 60*24}, 
                                    ],
                                    value=10080, 
                                    # inline=True, 
                                    className='btn-group',
                                    inputClassName="btn-check",
                                    labelClassName="btn btn-outline-primary",
                                    labelCheckedClassName="active",
                                ),
                            ], className="d-flex align-items-center gap-2"),
                            html.Div([
                            dbc.Button(
                                "Download raw data", 
                                id="downloadButton", 
                                color="info", 
                                n_clicks=0,
                                className="shadow-sm ms-auto"),
                            dcc.Download(id="downloadData", data=None),
                        ], className="d-flex align-items-center"),
                    ], className="d-flex flex-wrap w-100 justify-content-between align-items-center p-3 bg-light border rounded-4 shadow-sm")
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
    State("linksData", "data"),
    prevent_initial_call=True,
)
def toggleNode(_nodeClick, _linkClick, _resetClick, selected, linksData):
    selected = selected or []
    trig = ctx.triggered_id
    if not trig:
        return selected
    if trig == "reset":
        return []
    if isinstance(trig, dict) and trig.get("type") == "link":
        linkId = trig["index"]
        link=next((link for link in linksData if link[0] == linkId), None)
        if not link:
            return []
        _, srcId, dstId, _, _ = link
        return [srcId, dstId]
    i = trig["index"]
    if i in selected:
        selected.remove(i)   
    else:
        selected.append(i)   
    return selected

@callback(
    Output({"type": "nodeDot","index": ALL}, "pathOptions"),
    Input("selectedNodes", "data"),
    Input({"type": "link", "index": ALL}, "n_clicks"),
    State("nodesData", "data")
)
def updateNodeOpacity(selected, _linkClicks, nodesData):
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
    Input("dateRange", "start_date"),
    Input("dateRange", "end_date"),
    Input("gasType", "value"),
    Input("contentTabs", "active_tab"),
    Input("nodesData", "data"),
    Input("linksData", "data")
)
def updateInfo(selected, _, sensorType, graphTime, startDate, endDate, gasType, activeTab, nodesData, linksData):
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
            if startDate and endDate:
                startTs=datetime.strptime(startDate, "%Y-%m-%d").timestamp()
                endTs=datetime.strptime(endDate, "%Y-%m-%d").timestamp() + 86399  # Add 23:59:59 to include end date
            elif graphTime:
                endTs=datetime.now().timestamp()
                startTs=endTs-(graphTime*60)
            else:
                endTs=datetime.now().timestamp()
                startTs=endTs-(60*24*7)  # Default to 1 week if no input
            results=query.getRecentReadings(nodeId, startTs, endTs, sensorType, gasType if sensorType=="gas" else None, 0)
            if results:
                timestamps=pd.to_datetime([reading[3] for reading in results])
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
            
            linkId, srcId, dstId, rssi, mbps = linkData
            rssi=round(rssi, 2)
            mbps=round(mbps, 2)
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
                    html.Div(f"Quality: {mbps}", className="text-success fw-bold"),
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
                        html.Tr([html.Th("Link ID"), html.Td(linkId)]),
                    ])
                ], bordered=False, hover=True, striped=True, className="mb-0"),
                className="mt-3 shadow rounded-4 overflow-hidden border"
            )

            return html.Div([
                html.H4("Link details", className="text-center text-primary mb-4"),
                linkRow,
                linkTable
            ])
        elif not selected:
            return dbc.Alert("No node or too many nodes selected", color="warning", className="text-center")
        elif len(selected)>1:
            nodeTable=dbc.Table([
                html.Thead(html.Tr([html.Th("ID"), html.Th("Name"), html.Th("Info"), html.Th("Role"), html.Th("Polling rate"), html.Th("Sleep policy"), html.Th("Created"), html.Th("Firmware"), html.Th("Location")])),
                html.Tbody([
                    html.Tr([
                        html.Td(node[0]), #Node ID
                        html.Td(node[1]), #Node name
                        html.Td(node[9]), #Node info
                        html.Td(node[6]), #Node role
                        html.Td(node[4]), #Node polling rate
                        html.Td(node[5]), #Node sleep policy
                        html.Td(datetime.fromtimestamp(node[7]).strftime("%Y-%m-%d %H:%M:%S")), #Node created at
                        html.Td(node[8]), #Node firmware version
                        html.Td(f"({node[2]}, {node[3]})"), #Node location
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
                eui, label, lat, lon, pollingRate, sleepPolicy, role, created, version, info = nodeInfo


                nodeTable=dbc.Table([
                    html.Tbody([
                        html.Tr([html.Td("EUI"), html.Td(f"{eui}")]),
                        html.Tr([html.Td("Name"), html.Td(f"{label}")]),
                        html.Tr([html.Td("Info"), html.Td(f"{info}")]),
                        html.Tr([html.Td("Role"), html.Td(f"{role}")]),
                        html.Tr([html.Td("Polling rate"), html.Td(f"{pollingRate}")]),
                        html.Tr([html.Td("Sleep policy"), html.Td(f"{sleepPolicy}")]),
                        html.Tr([html.Td("Firmware version"), html.Td(f"{version}")]),
                        html.Tr([html.Td("Created at"), html.Td(datetime.fromtimestamp(created).strftime("%Y-%m-%d %H:%M:%S"))]),
                        html.Tr([html.Td("Location"), html.Td(f"({lat}, {lon})")])       
                    ])
                ], bordered=True, hover=True, striped=True, className="mt-3 shadow rounded-4")

                eventTable=html.Div("No recent events", className="text-center text-muted mt-3")
                recentEvents=query.getRecentEvents(eui, 5)
                if recentEvents:
                    events=[
                        html.Tr([
                            html.Td(event[2]), #Event type
                            html.Td(event[3]), #Event description
                            html.Td(event[4]), #Event timestamp
                        ]) for event in recentEvents
                    ]
                    eventTable=dbc.Table([
                        html.Thead(html.Tr([html.Th("Type"), html.Th("Description"), html.Th("Timestamp")])),
                        html.Tbody(events)
                    ], bordered=True, hover=True, striped=True, className="mt-3 shadow border rounded-4")
                nodeLinks=[]
                for nodeLink in linksData:
                    #TODO Modificare tabella per aggiungere pulsanti verso i nodi
                    if nodeLink[1]==eui or nodeLink[2]==eui:
                        nodeLinks.append(
                            html.Tr([
                                html.Td(nodeLink[0]),
                                html.Td(nodeLink[1] if nodeLink[1]==eui else nodeLink[2]),
                                html.Td(nodeLink[2] if nodeLink[2]!=eui else nodeLink[1]),
                                html.Td(nodeLink[3]),
                                html.Td(nodeLink[4]),
                            ])
                        )
                nodeLinksTable=dbc.Table([
                    html.Thead(html.Tr([html.Th("Link ID"), html.Th("Source node"), html.Th("Destination node"), html.Th("Rssi"), html.Th("Quality")])),
                    html.Tbody(nodeLinks)
                ], bordered=True, hover=True, striped=True, className="mt-3 shadow border rounded-4")

                return html.Div([
                    html.H4(f"{label} details", className="text-primary mt-4"),
                    nodeTable,
                    html.H5("Recent events", className="text-secondary mt-4"),
                    eventTable,
                    html.H5("Related links", className="text-secondary mt-4"),
                    nodeLinksTable
                ])
            else:
                return dbc.Alert("Node not found", color="danger", className="text-center")


@callback(
    Output("avgTemp", "children"),
    Output("avgHum", "children"),
    Input("contentTabs", "active_tab"),
    Input("graphTime", "value"),
    Input("dateRange", "start_date"),
    Input("dateRange", "end_date"),
    Input("selectedNodes", "data"),
    State("nodesData", "data")
)
def updateAvgStats(activeTab, graphTime, startDate, endDate, selected, nodesData):
    if activeTab=="tabStats":
        selected = selected or []
        if selected:
            nodesToShow=selected
        else:
            nodesToShow=[node[0] for node in nodesData]

        allTemps=[]
        allHums=[]

        if startDate and endDate:
            startTs=datetime.strptime(startDate, "%Y-%m-%d").timestamp()
            endTs=datetime.strptime(endDate, "%Y-%m-%d").timestamp() + 86399  # Add 23:59:59 to include end date
        elif graphTime:
            endTs=datetime.now().timestamp()
            startTs=endTs-(graphTime*60)
        else:
            endTs=datetime.now().timestamp()
            startTs=endTs-(60*24*7)  # Default to 1 week if no input

        for nodeId in nodesToShow:
            tempResults=query.getRecentReadings(nodeId, startTs, endTs, "temperature", None, 0)
            humResults=query.getRecentReadings(nodeId, startTs, endTs, "humidity", None, 0)

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
    Input("nodeMap", "clickData"),
    Input("moveNode", "n_clicks"),
    State("nodesData", "data"),
    State("linksData", "data"),
    State("selectedNodes", "data"),
    State("newLat", "value"),
    State("newLon", "value"),
    prevent_initial_call=True,
)
def moveNode(clickData, _moveNode, nodesData, linksData, selectedNodes, newLat, newLon):
    if len(selectedNodes or [])!=1:
        raise PreventUpdate
    
    trig=ctx.triggered_id
    if trig=="moveNode":
        if newLat is None or newLon is None:
            raise PreventUpdate
        lat=newLat
        lon=newLon
        
    nodeId=selectedNodes[0]
    query.updateNodePosition(nodeId, lat, lon)

    newNodes=[list(node) for node in nodesData]
    for node in newNodes:
        if node[0]==nodeId:
            node[2]=lat
            node[3]=lon
            break

    centers=[(node[2], node[3]) for node in newNodes]
    nodePositions={node[0]:[node[2], node[3]] for node in newNodes}
    newLinks=[[nodePositions[link[1]], nodePositions[link[2]]] for link in linksData]

    return newNodes, centers, newLinks

@callback(
        Output("newLat", "value"),
        Output("newLon", "value"),
        Output("newLat", "placeholder"),
        Output("newLon", "placeholder"),
        Input("selectedNodes", "data"),
        Input("nodesData", "data"),
        prevent_initial_call=True,
)
def clearPreview(selectedNodes, nodesData):
    lat=lon=None
    latPlaceholder=lonPlaceholder="New value"
    if len(selectedNodes or [])==1:
        nodeId=selectedNodes[0]
        nodeInfo=next((node for node in nodesData if node[0]==nodeId), None)
        if nodeInfo:
            lat=nodeInfo[2]
            lon=nodeInfo[3]
            latPlaceholder=f"Current: {lat}"
            lonPlaceholder=f"Current: {lon}"
        else:
            latPlaceholder="Node not found"
            lonPlaceholder="Node not found"
    return lat, lon, latPlaceholder, lonPlaceholder

@callback(
        Output("previewNode", "center"),
        Output("previewNode", "pathOptions"),
        Input("newLat", "value"),
        Input("newLon", "value"),
        Input("selectedNodes", "data"),
)
def updatePreviewNode(newLat, newLon, selectedNodes):
    if newLat is None or newLon is None or len(selectedNodes or [])!=1:
        return (0, 0), {"dashArray": "6, 6", "color": "orange"}
    return (newLat, newLon), {"dashArray": "6, 6", "color": "orange"}

@callback(
    Output("selectedNodes", "data", allow_duplicate=True),
    Output("contentTabs", "active_tab"),
    Input({"type": "nodeButton", "index": ALL}, "n_clicks"),
    State("selectedNodes", "data"),
    prevent_initial_call=True,
)
def nodeButtonClick(n_clicks, selectedNodes):
    if not n_clicks or not any(n_clicks):
        raise PreventUpdate 

    trig=ctx.triggered_id
    if not trig or not isinstance(trig, dict):
        raise PreventUpdate
    
    nodeId=trig["index"]
    return [nodeId], "tabNode"

@callback(
    Output("settingsRow", "style"),
    Input("contentTabs", "active_tab"),
    Input("selectedNodes", "data")
)
def toggleSettings(activeTab, selectedNodes):
    if activeTab=="tabSettings" and len(selectedNodes or [])==1:
        return {"display": "flex"}
    return {"display": "none"}

@callback(
    Output("newPollingRate", "value"),
    Input("updatePolling", "n_clicks"),
    State("newPollingRate", "value"),
    State("selectedNodes", "data"),
    prevent_initial_call=True,
)
def updatePollingRate(_update, newPollingRate, selectedNodes):
    if len(selectedNodes or [])!=1:
        raise PreventUpdate
    if newPollingRate is None or newPollingRate<1:
        raise PreventUpdate
    
    nodeId=selectedNodes[0]
    query.updateNodePolling(nodeId, newPollingRate)
    newPollingRate=0
    return newPollingRate

@callback(
    Output("gasType", "style"),
    Input("sensorType", "value")
)
def toggleGasDropdown(sensorType):
    if sensorType=="gas":
        return {"display": "block", "width": "120px"}
    return {"display": "none", "width": "120px"}

@callback(
    Output("downloadData", "data"),
    Input("downloadButton", "n_clicks"),
    State("selectedNodes", "data"),
    State("sensorType", "value"),
    State("graphTime", "value"),
    State("dateRange", "start_date"),
    State("dateRange", "end_date"),
    State("gasType", "value"),
    State("nodesData", "data"),
    prevent_initial_call=True,
)
def downloadData(_download, selectedNodes, sensorType, graphTime, startTs, endTs, gasType, nodesData):
    downloadData=[]
    nodes=selectedNodes or [node[0] for node in nodesData]
    if startTs and endTs:
        startTime=datetime.strptime(startTs, "%Y-%m-%d").timestamp()
        endTime=datetime.strptime(endTs, "%Y-%m-%d").timestamp() + 86399  # Add 23:59:59 to include end date
        startFile=datetime.fromtimestamp(startTime)
        endFile=datetime.fromtimestamp(endTime)
    elif graphTime:
        endTime=datetime.now().timestamp()
        startTime=endTs-(graphTime*60)
        startFile=datetime.fromtimestamp(startTime)
        endFile=datetime.fromtimestamp(endTime)
    else:
        endTime=datetime.now().timestamp()
        startTime=endTime-(60*24*7)  # Default to 1 week if no input
        startFile=datetime.fromtimestamp(startTime)
        endFile=datetime.fromtimestamp(endTime)
    for node in nodes:
        results=query.getRecentReadings(node, startTime, endTime, sensorType, gasType if sensorType=="gas" else None, 1)
        if results:
            downloadData.extend(results)
    if not downloadData:
        raise PreventUpdate
    
    df=pd.DataFrame(downloadData, columns=["id", "eui", "sensor", "timestamp", "value"])
    endTime=datetime.now()
    filename=f"readings_{sensorType}_{startFile.strftime('%Y%m%d%H%M%S')}_{endFile.strftime('%Y%m%d%H%M%S')}.csv"
    return dcc.send_data_frame(df.to_csv, filename, index=False)

@callback(
    Output("baseMap", "url"),
    Output("baseMap", "attribution"),
    Input("mapStyle", "value")
)
def changeMapStyle(mapStyle):
    if mapStyle=="osm":
        return ("https://tile.openstreetmap.org/{z}/{x}/{y}.png", 
                "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors")
    else:
        return ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 
                "Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community")
    
@callback(
    Output("dateRange", "start_date"),
    Output("dateRange", "end_date"),
    Output("graphTime", "value"),
    Input("graphTime", "value"),
    Input("dateRange", "start_date"),
    Input("dateRange", "end_date"),
    prevent_initial_call=True
)
def updateDateRange(graphTime, startDate, endDate):
    trig=ctx.triggered_id
    if trig=="graphTime":
        return None, None, graphTime
    elif trig=="dateRange":
        return no_update, no_update, None
    else:
        return no_update, no_update, no_update

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='getLocation'
    ),
    Output("newLat", "value", allow_duplicate=True),
    Output("newLon", "value", allow_duplicate=True),
    Input("getLocation", "n_clicks"),
    prevent_initial_call=True
)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)