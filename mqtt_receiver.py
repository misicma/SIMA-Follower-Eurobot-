"""
mqtt_receiver.py
----------------
Skripta se pokrece na racunaru (Windows). Pretplacuje se na MQTT temu
"sensor/xy", prima podatke koje salje RpiApp.py sa Raspberry Pi-a i cuva
ih u lokalnu SQLite bazu podataka (sensor_data.db), odakle ih kasnije
cita api_server.py.

Instalacija:
    pip install paho-mqtt

Pokretanje:
    python mqtt_receiver.py
"""

import json
import sqlite3
from datetime import datetime

import paho.mqtt.client as mqtt

# ==== PODESAVANJA ====
# Mosquitto broker po pravilu radi na ovom istom racunaru, pa je
# podrazumevano "localhost". Ovo vazi i kad se testira sve na jednom
# racunaru (RpiApp.py + mqtt_receiver.py + broker na istoj masini) i
# kad je receiver na racunaru na kome je i broker instaliran (a
# RpiApp.py salje podatke sa udaljenog Raspberry Pi-a preko mreze -
# u tom slucaju IP receiver-a/brokera treba da bude upisan u
# RpiApp.py kao BROKER_IP, dok ovde receiver ostaje na "localhost").
BROKER_IP = "localhost"
BROKER_PORT = 1883
TOPIC = "sensor/xy"

DB_FILE = "sensor_data.db"


def init_db(): #prvo se ovo ostvaruje
    conn = sqlite3.connect(DB_FILE) #ostvari komunikaciju
    cur = conn.cursor() #napravi kursor
    cur.execute( #kreiraj tabelu sa njenim poljima ukoliko vec ne postoji
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x REAL NOT NULL,
            y REAL NOT NULL,
            sensor_timestamp REAL,
            received_at TEXT NOT NULL
        )
        """
    )
    conn.commit() #dodaj te promjene u bazu, kao commit kod git-a
    conn.close() #zatvori komunikaciju
    print(f"[Receiver] Baza podataka spremna: {DB_FILE}")


def on_connect(client, userdata, flags, rc):
    if rc == 0: #ako smo uspjeli povezati klijenta i servera
        print(f"[Receiver] Povezan na MQTT broker {BROKER_IP}:{BROKER_PORT}")
        client.subscribe(TOPIC) #slusanje sa nekog TOPICs-a
        print(f"[Receiver] Pretplacen na temu '{TOPIC}'")
    else:
        print(f"[Receiver] Greska pri povezivanju, kod: {rc}") #nije ostvarena komunikacija


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8")) #ucitavanje json fajla
        #dobij podatke koji ti trebaju
        x = data.get("x")
        y = data.get("y")
        sensor_ts = data.get("timestamp")

        conn = sqlite3.connect(DB_FILE) #ostvari komunikaciju po drugi put
        cur = conn.cursor() #napravi kursor
        cur.execute( #dodaj te podatke u bazu podataka
            "INSERT INTO readings (x, y, sensor_timestamp, received_at) "
            "VALUES (?, ?, ?, ?)",
            (x, y, sensor_ts, datetime.now().isoformat()),
        )
        #received_at smo stavili cisto da vidimo koliko kasni komunikacija izmedju servera i klijenta
        conn.commit() #dodaj te promjene
        conn.close() #zatvori komunikaciju

        print(f"[Receiver] Sacuvano: x={x}, y={y}") 
    except Exception as e:
        print(f"[Receiver] Greska pri obradi poruke: {e}")


def main():
    init_db()

    client = mqtt.Client() #kreiraaj klijenta
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Receiver] Povezivanje na broker {BROKER_IP}:{BROKER_PORT} ...")
    client.connect(BROKER_IP, BROKER_PORT, keepalive=60)

    try:
        client.loop_forever() #blokira glavni tok programa, izvrsava se i slusanje i slanje unutar
    except KeyboardInterrupt:
        print("\n[Receiver] Zaustavljeno od strane korisnika.")
        client.disconnect() #izgasi komunikaciju


if __name__ == "__main__":
    main()