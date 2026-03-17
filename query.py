import os
import sqlite3

dir = os.path.dirname(__file__)
database = os.path.join(dir, "dashboard.db")

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

def getRecentReadings(node, interval):
    conn=connessione()
    cursor=conn.cursor()

    intervalStr=f"-{interval} minutes"
    readings=[]
    #sensorID, nodeId, sensor type, timestamp, value
    #selects all ""temperature"" readings for each given node in the last interval minutes 
    
    cursor.execute("" \
    "SELECT s.id, s.nodo, s.tipo_sensore, ls.timestamp, ls.valore " \
    "FROM letture_sensori ls " \
    "JOIN Sensori s ON(s.id=ls.sensore) " \
    "WHERE s.tipo_sensore='temperature' AND timestamp>=datetime('now', ?) "
    "AND s.nodo=? " \
    "ORDER BY ls.timestamp ASC; ", (intervalStr, node,))
    readings=cursor.fetchall()

    cursor=conn.close
    return readings
    

def main():
    nodi = getNodi()
    for nodo in nodi:
        print(nodo)

    links= getLinks()
    for link in links:
        print(link)


if __name__ == "__main__":    
    main()