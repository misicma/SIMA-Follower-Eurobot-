"""
api_server.py
--------------
Skripta se pokrece na racunaru (Windows), zajedno sa mqtt_receiver.py.
Servisira HTML stranicu (templates/index.html) i izlaze API-je koji
citaju podatke iz sensor_data.db i vracaju ih stranici u JSON formatu,
kako bi se u realnom vremenu pratio polozaj objekta.

Instalacija:
    pip install flask

Pokretanje:
    python api_server.py

Zatim u pretrazivacu otvoriti:
    http://127.0.0.1:8080
"""

import sqlite3

from flask import Flask, jsonify, render_template

app = Flask(__name__)
DB_FILE = "sensor_data.db"


def get_latest_reading():
    conn = sqlite3.connect(DB_FILE) #ostvari konekciju i data ti je baza
    cur = conn.cursor() #napravi kursor
    #uzmi x,y,sensor_timestamp i received_at i to jedan red samo
    #sortiraj ih po id
    cur.execute( 
        "SELECT x, y, sensor_timestamp, received_at "
        "FROM readings ORDER BY id DESC LIMIT 1"
    )
    row = cur.fetchone() #vrati taj jedan red
    conn.close() #zatvori konekciju
    if row:
        return {
            "x": row[0], #jer nije koriscen sqlite3.Row
            "y": row[1],
            "sensor_timestamp": row[2],
            "received_at": row[3],
        }
    return None


def get_history(limit=50): #podaci limitirani na 50 tacaka
    #ostalo je sve isto 
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT x, y, received_at FROM readings ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"x": r[0], "y": r[1], "received_at": r[2]} for r in reversed(rows)]


@app.route("/") #serviranje glavne HTML stranice
def index():
    return render_template("index.html") #citanje sadrzaja index.html, slanje browseru kao odgovor


@app.route("/api/latest") #kada god dodje zahtjev na ovu putanju ova funkcija se izvrsava
def latest():
    data = get_latest_reading() #prihvati poslednje ocitavanje senzora
    if data is None: #ako nema podataka 
        return jsonify({"error": "Jos uvek nema podataka"}), 404
    return jsonify(data) #ako ima prebaci ih u json format


@app.route("/api/history")
def history(): #ako ima sacuvanih novih podataka
    return jsonify(get_history()) #vrati ih kao json fajl


if __name__ == "__main__":
    print("[API] Server pokrenut na http://127.0.0.1:8080")
    app.run(host="127.0.0.1", port=8080, debug=True) 
    #app.run -> pokrece se server i ulazi se u beskonacnu petlju "slusanja"
    #program ne prolazi dalje kroz kod, ispod ove linije, srecom pa nemamo nista ispod
    #nista ispod se ne bi izvrsavalo sve dok se server ne izgasi
    #SERVER OSTAJE BUDAN I CEKA HTTP ZAHTJEVE ZAUVIJEK, SVE DOK GA NE ZAUSTAVIMO
