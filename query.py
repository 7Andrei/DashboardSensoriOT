import os
import sqlite3
from datetime import datetime, timedelta
import time
import uuid
import json

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


def getLinks():
    conn=connessione()
    cursor=conn.cursor()

    cursor.execute("" \
    "SELECT " \
    "CASE WHEN ld.src_eui<dst_eui THEN ld.src_eui ELSE ld.dst_eui END as src, " \
    "CASE WHEN ld.src_eui<dst_eui THEN ld.dst_eui ELSE ld.src_eui END as dst, " \
    "AVG(CASE WHEN ld.metric_name='rssi' THEN ld.value_num END) as avg_rssi, " \
    "AVG(CASE WHEN ld.metric_name='link_quality' THEN ld.value_num END) as avg_quality " \
    "FROM link_diagnostic ld " \
    "GROUP BY src, dst;")

    tmpLinks=cursor.fetchall()
    conn.close()
    return tmpLinks

def getRecentReadings(node, interval, type):
    conn=connessione()
    cursor=conn.cursor()
    interval=time.time()-(interval*60)
    readings=[]
    #sensorID, nodeId, sensor type, timestamp, value
    #selects all ""temperature"" readings for each given node in the last interval minutes 
    if type=="temperature" or type=="humidity" or type=="pressure":
        ftype=f"%{type}%"
        cursor.execute("" \
        "SELECT id, eui, ? AS sensor, " \
        "datetime(CAST(timestamp/60 AS INTEGER)*60, 'unixepoch', 'localtime') AS bucket, " \
        "AVG(sr.value) AS value " \
        "FROM sensor_reading sr " \
        "WHERE sr.sensor_name LIKE ? AND sr.timestamp>=? AND sr.eui=? " \
        "GROUP BY sr.eui, bucket", (type, ftype, interval, node,))
        readings=cursor.fetchall()
        conn.close()
    return readings

def getRecentEvents(node, num):
    conn=connessione()
    cursor=conn.cursor()
    events=[]
    cursor.execute("" \
    "SELECT id, eui, event_type, message, timestamp, severity " \
    "FROM event " \
    "WHERE eui=? " \
    "ORDER BY timestamp DESC " \
    "LIMIT ?;", (node, num))    
    events=cursor.fetchall()
    conn.close()
    return events

def updateNodePosition(node, lat, lon):
    payload=json.dumps(
        {
            "eui": node,
            "latitude": lat,
            "longitude": lon
        }
    ).encode("utf-8")
    payloadUUID=str(uuid.uuid4())
    timestamp=time.time()

    conn=connessione()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO data (uuid, timestamp, data) VALUES (?, ?, ?);", (payloadUUID, timestamp, sqlite3.Binary(payload,)))
    dataId=cursor.lastrowid
    cursor.execute("INSERT INTO node_parameter_log (timestamp, eui, parameter_name, value_num, data_id) VALUES (?, ?, ?, ?, ?);", (timestamp, node, "latitude", lat, dataId,))
    cursor.execute("INSERT INTO node_parameter_log (timestamp, eui, parameter_name, value_num, data_id) VALUES (?, ?, ?, ?, ?);", (timestamp, node, "longitude", lon, dataId,))
    conn.commit()
    conn.close()

# def main():
#     nodes=getNodes()
#     links=getLinks()


# if __name__ == "__main__":    
#     main()