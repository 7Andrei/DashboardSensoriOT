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


def main():
    nodi = getNodi()
    for nodo in nodi:
        print(nodo)

    links= getLinks()
    for link in links:
        print(link)


if __name__ == "__main__":    
    main()