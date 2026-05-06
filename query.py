import os
import sqlite3
from datetime import datetime, timedelta

dir = os.path.dirname(__file__)
database = os.path.join(dir, "DBVero/data.db")

def connessione():
    return sqlite3.connect(database)


def getNodes():
    conn=connessione()
    cursor=conn.cursor()
    cursor.execute("" \
    "SELECT n.eui, n.label, " \
    "MAX(CASE WHEN np.parameter_name='latitude' THEN np.value_num END) AS latitude, " \
    "MAX(CASE WHEN np.parameter_name='longitude' THEN np.value_num END) AS longitude, " \
    "MAX(CASE WHEN np.parameter_name='polling_frequency' THEN np.value_num END) AS polling_frequency, " \
    "MAX(CASE WHEN np.parameter_name='sleep_policy' THEN np.value_text END) AS sleep_policy, " \
    "MAX(CASE WHEN ns.state_name='role' THEN ns.value_text END) AS role, " \
    "n.created_at, n.version, n.comment " \
    "FROM node n " \
    "LEFT JOIN node_parameter np ON n.eui=np.eui " \
    "LEFT JOIN node_state ns ON n.eui=ns.eui " \
    "GROUP BY n.eui;")
    tmpNodes=cursor.fetchall()
    conn.close()
    return tmpNodes

# def getNodi():
#     conn=connessione()
#     cursor=conn.cursor()
#     cursor.execute("SELECT * FROM Nodi")
#     nodi=cursor.fetchall()
#     conn.close()
#     return nodi

def getLinks():
    conn=connessione()
    cursor=conn.cursor()
    # cursor.execute("" \
    # "SELECT ld.src_eui, ld.dst_eui, ld.timestamp, " \
    # "MAX(CASE WHEN ld.metric_name = 'link_quality' THEN ld.value_num END) AS link_quality, " \
    # "MAX(CASE WHEN ld.metric_name = 'rssi' THEN ld.value_num END) AS rssi " \
    # "FROM link_diagnostic ld " \
    # "JOIN (" \
    # "SELECT src_eui, dst_eui, MAX(timestamp) as max_timestamp " \
    # "FROM link_diagnostic " \
    # "GROUP BY src_eui, dst_eui) last " \
    # "ON ld.src_eui=last.src_eui " \
    # "AND ld.dst_eui=last.dst_eui " \
    # "AND ld.timestamp=last.max_timestamp " \
    # "GROUP BY ld.src_eui, ld.dst_eui, ld.timestamp ;")

    cursor.execute("" \
    "SELECT ld.src_eui, ld.dst_eui, " \
    "AVG(CASE WHEN ld.metric_name='rssi' THEN ld.value_num END) as avg_rssi," \
    "AVG(CASE WHEN ld.metric_name='link_quality' THEN ld.value_num END) as avg_quality " \
    "FROM link_diagnostic ld " \
    "WHERE ld.timestamp>=(strftime('%s', 'now')-3600) " \
    "GROUP BY ld.src_eui, ld.dst_eui")

    tmpLinks=cursor.fetchall()
    conn.close()
    return tmpLinks

# def getLinks():
#     conn=connessione()
#     cursor=conn.cursor()
#     cursor.execute("SELECT * FROM Links")
#     links=cursor.fetchall()
#     conn.close()
#     return links

def getRecentReadings(node, interval, type):
    conn=connessione()
    cursor=conn.cursor()

    # intervalStr=f"-{interval} minutes"
    intervalStr=(datetime.now()-timedelta(minutes=interval)).isoformat()
    readings=[]
    #sensorID, nodeId, sensor type, timestamp, value
    #selects all ""temperature"" readings for each given node in the last interval minutes 
    
    cursor.execute("" \
    "SELECT s.id, s.nodo, s.tipo_sensore, ls.timestamp, ls.valore " \
    "FROM letture_sensori ls " \
    "JOIN Sensori s ON(s.id=ls.sensore) " \
    "WHERE s.tipo_sensore=? AND timestamp>=? "\
    "AND s.nodo=? " \
    "ORDER BY ls.timestamp ASC; ", (type, intervalStr, node,))
    readings=cursor.fetchall()

    conn.close()
    return readings

def getRecentEvents(node, num):
    conn=connessione()
    cursor=conn.cursor()
    events=[]
    cursor.execute("" \
    "SELECT id, nodo, tipo_evento, descrizione, timestamp, nodo_sorgente " \
    "FROM Eventi " \
    "WHERE nodo=? " \
    "ORDER BY timestamp DESC " \
    "LIMIT ?;", (node, num))    
    events=cursor.fetchall()
    conn.close()
    return events

def updateNodePosition(nodeId, lat, lon):
    conn=connessione()
    cursor=conn.cursor()
    cursor.execute("UPDATE Nodi SET latitudine=?, longitudine=? WHERE id=?;", (lat, lon, nodeId,))
    conn.commit()
    conn.close()

def main():
    # nodi = getNodi()
    # for nodo in nodi:
    #     print(nodo)

    # links= getLinks()
    # for link in links:
    #     print(link)
    nodes=getNodes()
    links=getLinks()

    for node in nodes:
        print(node) 
    # print(nodes)


if __name__ == "__main__":    
    main()