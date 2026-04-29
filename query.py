import os
import sqlite3
from datetime import datetime, timedelta

dir = os.path.dirname(__file__)
database = os.path.join(dir, "dashboard2.db")

def connessione():
    return sqlite3.connect(database)

def getNodi():
    conn=connessione()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM Nodi")
    nodi=cursor.fetchall()
    conn.close()
    return nodi

def getLinks():
    conn=connessione()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM Links")
    links=cursor.fetchall()
    conn.close()
    return links

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
    nodi = getNodi()
    for nodo in nodi:
        print(nodo)

    links= getLinks()
    for link in links:
        print(link)


if __name__ == "__main__":    
    main()