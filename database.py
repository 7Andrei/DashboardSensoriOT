import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "dashboard.db")

# Coordinate nodi
COORDINATES = [
    (42.004697, 12.676136), (42.004556, 12.675926), (42.004445, 12.675719),
    (42.004297, 12.675600), (42.004482, 12.676131), (42.004378, 12.675967),
    (42.004322, 12.675866), (42.004375, 12.676197), (42.004243, 12.676047),
    (42.004174, 12.675815)
]

def setupDatabase(cursor):

    # NODI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Nodi (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nome            VARCHAR(100) NOT NULL,
            ip              VARCHAR(45) UNIQUE NOT NULL,
            ruolo           TEXT NOT NULL CHECK (ruolo IN ('Router', 'Parent', 'Child')),
            latitudine      REAL,
            longitudine     REAL
        );
    ''')

    # LINKS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Links (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo1                   INTEGER NOT NULL,
            nodo2                   INTEGER NOT NULL,
            timestamp_connessione   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mbps                    REAL,
            rssi_segnale            INTEGER,
                   
            FOREIGN KEY (nodo1) REFERENCES Nodi(id) ON DELETE CASCADE,
            FOREIGN KEY (nodo2) REFERENCES Nodi(id) ON DELETE CASCADE,
                   
            UNIQUE (nodo1, nodo2)
        );
    ''')
    
    # EVENTI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Eventi (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            nodo            INTEGER NOT NULL,
            tipo_evento     TEXT NOT NULL CHECK (tipo_evento IN ('PACKET_RX', 'PACKET_TX', 'BATTERY_LOW', 'DEVICE_OFF', 'DISCONNECTED', 'CONNECTED')),
            descrizione     TEXT, 
            nodo_sorgente   INTEGER,
                   
            FOREIGN KEY (nodo) REFERENCES Nodi(id) ON DELETE CASCADE,
            FOREIGN KEY (nodo_sorgente) REFERENCES Nodi(id) ON DELETE SET NULL
        );
    ''')

    # SENSORI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sensori (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo                INTEGER NOT NULL,
            tipo_sensore        VARCHAR(50) NOT NULL,
            frequenza_polling   INTEGER,
                   
            FOREIGN KEY (nodo) REFERENCES Nodi(id) ON DELETE CASCADE,
                   
            UNIQUE(nodo, tipo_sensore)
        );
    ''')
    
    # LETTURE SENSORI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS letture_sensori (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sensore     INTEGER NOT NULL,
            timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valore      REAL NOT NULL,
                   
            FOREIGN KEY (sensore) REFERENCES Sensori(id) ON DELETE CASCADE
        );
    ''')

    
    # print("database creato con successo")


def populateDatabase(cursor):
    # print("Riempimento database...")
    
    # Inserimento Nodi
    nodes_data = [
        ('Router1', '192.168.1.1', 'Router', *COORDINATES[0]),
        ('Parent1', '192.168.1.2', 'Parent', *COORDINATES[1]),
        ('Parent2', '192.168.1.3', 'Parent', *COORDINATES[2]),
        ('Child1', '192.168.1.4', 'Child', *COORDINATES[3]),
        ('Parent3', '192.168.1.5', 'Parent', *COORDINATES[4]),
        ('Parent4', '192.168.1.6', 'Parent', *COORDINATES[5]),
        ('Parent5', '192.168.1.7', 'Parent', *COORDINATES[6]),
        ('Child2', '192.168.1.8', 'Child', *COORDINATES[7]),
        ('Parent6', '192.168.1.9', 'Parent', *COORDINATES[8]),
        ('Child3', '192.168.1.10', 'Child', *COORDINATES[9])
    ]
    cursor.executemany('''
        INSERT INTO Nodi (nome, ip, ruolo, latitudine, longitudine) VALUES (?, ?, ?, ?, ?);
    ''', nodes_data)

    # Inserimento Links
    links_data = [
        (1, 2, 100.00, -45), (1, 5, 90.50, -50), (2, 3, 85.75, -55),
        (2, 6, 80.25, -60), (3, 4, 70.00, -62), (3, 7, 65.50, -65),
        (5, 6, 60.25, -68), (6, 7, 55.00, -70), (6, 9, 50.50, -72),
        (7, 10, 45.50, -75), (8, 9, 40.50, -78), (9, 10, 40.50, -80)
    ]
    cursor.executemany('''
        INSERT INTO Links (nodo1, nodo2, mbps, rssi_segnale) VALUES (?, ?, ?, ?);
    ''', links_data)

    # Inserimento Eventi
    events_data = [
        # (node_id, event_type, description, source_node_id)
        (2, 'PACKET_RX', 'Payload: TEMP_READING', 1),
        (1, 'PACKET_TX', 'Comando: GET_STATUS', 1),
        (10, 'BATTERY_LOW', 'Batteria al 15%', None),
        (4, 'CONNECTED', 'Connesso al parent 3', 3),
        (8, 'DISCONNECTED', 'Segnale perso', None),
        (5, 'PACKET_RX', 'Payload: ACK', 1)
    ]
    cursor.executemany('''
        INSERT INTO Eventi (nodo, tipo_evento, descrizione, nodo_sorgente) VALUES (?, ?, ?, ?); 
    ''', events_data)

    # Inserimento sensori e tempo letture
    sensors_data = [(1, 'temperature', 1800), (1, 'humidity', 3600), (1, 'battery', 3600),
                    (2, 'temperature', 1800), (2, 'humidity', 3600), (2, 'battery', 3600),
                    (3, 'temperature', 1800), (3, 'humidity', 3600), (3, 'battery', 3600), 
                    (4, 'temperature', 1800), (4, 'humidity', 3600), (4, 'battery', 3600),
                    (5, 'temperature', 1800), (5, 'humidity', 3600), (5, 'battery', 3600),
                    (6, 'temperature', 1800), (6, 'humidity', 3600), (6, 'battery', 3600),
                    (7, 'temperature', 1800), (7, 'humidity', 3600), (7, 'battery', 3600),
                    (8, 'temperature', 1800), (8, 'humidity', 3600), (8, 'battery', 3600),
                    (9, 'temperature', 1800), (9, 'humidity', 3600), (9, 'battery', 3600),
                    (10, 'temperature', 1800), (10, 'humidity', 3600), (10, 'battery', 3600),
                    ]
    cursor.executemany('''
        INSERT INTO Sensori (nodo, tipo_sensore, frequenza_polling) VALUES (?, ?, ?);
    ''', sensors_data)
    
    # print("database riempito")


def main():

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        # print(f"Database '{DB_FILE}' precedente rimosso.")

    conn = None
    try:
        # Connessione al database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Esecuzione delle funzioni
        setupDatabase(cursor)
        populateDatabase(cursor)

        # Commit delle modifiche
        conn.commit()
        # print("Database creato e riempito")

    except sqlite3.Error as e:
        print(f"Errore del database: {e}")
    finally:
        # Chiusura della connessione
        if conn:
            conn.close()
            # print("Connessione al database chiusa.")


if __name__ == '__main__':
    main()