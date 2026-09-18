"""
RpiApp.py
---------
Skripta se pokreće na Raspberry Pi-u. Generise (simulira) podatke sa senzora
(x, y koordinate) i salje ih preko MQTT-a na temu "sensor/xy", odakle ih
mqtt_receiver.py (na racunaru) preuzima i cuva u bazu.

Instalacija:
    pip install paho-mqtt --break-system-packages

Pokretanje:
    python3 RpiApp.py
"""

import json
import math
import random
import time

import paho.mqtt.client as mqtt

# ==== PODESAVANJA ====
# IP adresa racunara na kome je pokrenut MQTT broker (Mosquitto).
# Dobija se komandom "hostname -I" (Linux) ili "ipconfig" (Windows).
#
# Podrazumevano je "localhost" - to radi ako RpiApp.py, mqtt_receiver.py
# i broker pokrecete na ISTOM racunaru (npr. za testiranje bez pravog
# Raspberry Pi uredjaja). Ako RpiApp.py pokrecete na stvarnom Raspberry
# Pi-u, ovde upisite IP adresu racunara na kome je broker (npr. 192.168.1.100).
BROKER_IP = "localhost"
BROKER_PORT = 1883
TOPIC = "sensor/xy"

# Interval slanja podataka (sekunde)
SEND_INTERVAL = 2

# Granice unutar kojih se generisu simulirane koordinate (u milimetrima),
# uskladjene sa dimenzijama Eurobot polja: 3000mm x 2000mm.
# Ostavljena je mala margina od ivica polja (radi robota koji ima svoju sirinu).
MARGIN = 150
X_MIN, X_MAX = MARGIN, 3000.0 - MARGIN
Y_MIN, Y_MAX = MARGIN, 2000.0 - MARGIN

# Koliko se robot pomeri po jednom ocitavanju (mm) - "brzina" simulacije
STEP = 250

# Stanje simulacije: trenutna pozicija i tacka ka kojoj se robot krece.
# Robot ide pravolinijski ka meti; kad je dostigne, bira se nova nasumicna
# meta - tako robot vremenom obidje celo polje, a ne samo jedan ugao.
_state = {"x": None, "y": None, "target": None}


def _random_point(): #generisanje random x i y koordinata
    return (
        round(random.uniform(X_MIN, X_MAX), 1),
        round(random.uniform(Y_MIN, Y_MAX), 1),
    )


def generate_sensor_data():
    """
    Simulira ocitavanje senzora. Robot se krece pravolinijski ka trenutnoj
    "meti" na terenu; kada je dostigne (ili pri prvom pozivu), bira se nova
    nasumicna meta unutar granica polja. Ovako simulacija realisticnije
    "obilazi" ceo teren, umjesto da ostane zaglavljena u jednom uglu.

    Kod pravog senzora, ovde bi umjesto ovoga stajao kod za citanje stvarne
    pozicije robota (npr. iz odometrije).
    """
    if _state["x"] is None:
        _state["x"], _state["y"] = _random_point() #random x i y pocetne koordinate
        _state["target"] = _random_point() #generisanje "mete" dokle idemo sa robotom

    tx, ty = _state["target"]
    x, y = _state["x"], _state["y"]

    dx, dy = tx - x, ty - y
    dist = math.hypot(dx, dy) #generisanje te distance koju pravimo

    if dist < STEP:
        # Meta dostignuta - odaberi novu
        x, y = tx, ty
        _state["target"] = _random_point()
    else: #ako jos uvijek nismo stigli do "mete"
        x += dx / dist * STEP
        y += dy / dist * STEP

    _state["x"], _state["y"] = round(x, 1), round(y, 1) #zaokruzi koordinate na 1 decimalu

    return { #vrati te podatke
        "x": _state["x"],
        "y": _state["y"],
        "timestamp": time.time(),
    }


def on_connect(client, userdata, flags, rc):
    if rc == 0: #ako je uspjelo ostvarivanje komunikacije
        print(f"[RpiApp] Povezan na MQTT broker {BROKER_IP}:{BROKER_PORT}")
    else: #ako nije
        print(f"[RpiApp] Greska pri povezivanju, kod: {rc}")


def main():
    client = mqtt.Client() #kreiraj klijenta
    client.on_connect = on_connect #da li je komunikacija bila uspjesna ili ne

    print(f"[RpiApp] Povezivanje na broker {BROKER_IP}:{BROKER_PORT} ...")
    client.connect(BROKER_IP, BROKER_PORT, keepalive=60) #povezi
    client.loop_start() #pocni ove procese u pozadini kao neki Thread, ne uzima glavni tok programa

    try:
        while True: #vrti te procese
            data = generate_sensor_data() #cuvaj te podatke generisane od strane "senzora"

            payload = json.dumps(data) #pretvori ih u json format
            client.publish(TOPIC, payload) #salji te podatke na topics - "sensor/xy"
            print(f"[RpiApp] Poslato na '{TOPIC}': {payload}")

            time.sleep(SEND_INTERVAL)
    except KeyboardInterrupt:
        print("\n[RpiApp] Zaustavljeno od strane korisnika.")
    finally:
        client.loop_stop() #zaustavi ocitavanje
        client.disconnect() #prekini komunikaciju


if __name__ == "__main__":
    main()