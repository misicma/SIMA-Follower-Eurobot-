# MQTT primer - praćenje položaja objekta

Jednostavan primer komunikacije udaljenih uređaja preko MQTT brokera.

- **RpiApp.py** (Raspberry Pi) — generiše (simulira) podatke sa senzora i
  šalje ih preko MQTT-a na temu `sensor/xy`.
- **mqtt_receiver.py** (Windows) — pretplaćuje se na `sensor/xy` i čuva
  podatke u SQLite bazi `sensor_data.db`.
- **api_server.py** (Windows) — Flask server koji servisira HTML stranicu
  (`templates/index.html`) i podatke iz baze preko API-ja
  (`/api/latest`, `/api/history`).
- **templates/index.html** — prikazuje trenutni položaj i putanju objekta,
  osvežava se svake 2 sekunde.

Sve tri skripte moraju raditi istovremeno, a Raspberry Pi i računar moraju
biti na istoj mreži.

## Na Raspberry Pi-u

```bash
pip install paho-mqtt --break-system-packages
git clone <url-repozitorijuma>
cd "putanja do kloniranog foldera"
python3 RpiApp.py
```

Pre pokretanja, u `RpiApp.py` upisati `BROKER_IP` — IP adresu Windows
računara na kome radi Mosquitto broker.

## Na računaru (Windows)

1. Preuzeti i instalirati Mosquitto: https://mosquitto.org/download/
2. U `mosquitto.conf` (u instalacionom folderu, npr. `C:\Program Files\mosquitto\`)
   dodati:

   ```
   listener 1883 0.0.0.0
   allow_anonymous true
   ```

   > Napomena: radi bolje bezbednosti, kasnije postaviti
   > `allow_anonymous false` i konfigurisati `password_file`.

3. U Windows Defender Firewall → Advanced settings napraviti Inbound Rule
   koje dozvoljava TCP port 1883.
4. Restartovati servis "Mosquitto Broker" u `services.msc`.
5. Pronaći IP adresu računara komandom `ipconfig` i upisati je u
   `RpiApp.py` (na Raspberry Pi-u) i u `mqtt_receiver.py` (BROKER_IP).
6. Instalirati zavisnosti i pokrenuti skripte:

   ```bash
   pip install -r requirements.txt
   python mqtt_receiver.py
   ```

   U novom terminalu:

   ```bash
   python api_server.py
   ```

7. Otvoriti u pretraživaču:

   ```
   http://127.0.0.1:8080
   ```

Stranica treba da prikazuje trenutni položaj objekta na osnovu podataka
koje šalje Raspberry Pi.
