# DroneKit'in Python 3.10+ surumlerindeki hatasini cozen yama
import collections
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

from dronekit import connect, VehicleMode
from pymavlink import mavutil
import paho.mqtt.client as mqtt
import time
import threading
import sys # EKLENDI: Terminalden parametre (D1, D2) alabilmek icin

# MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "cezeri/drone/komut"

BAUD_RATE = 57600 

# TEKİL DRONE SINIFI (Değişiklik yapılmadı)
class SingleDrone:
    def __init__(self, connection_string, drone_id):
        self.id = drone_id
        print(f"[Drone {self.id}] Baglaniliyor: {connection_string}")
        self.vehicle = connect(connection_string, wait_ready=True, baud=BAUD_RATE)
        print(f"[Drone {self.id}] Baglanti basarili.")
        
    def set_mode(self, mode):
        self.vehicle.mode = VehicleMode(mode)
        
    def arm(self):
        if not self.vehicle.is_armable:
            print(f"[Drone {self.id}] HATA: Arm reddedildi! Pre-arm kontrolleri gecilemedi.")
            return
        
        print(f"[Drone {self.id}] GUIDED moduna geciliyor ve Arm ediliyor")
        self.set_mode("GUIDED")
        time.sleep(1) # Modun oturması için kısa bekleme
        self.vehicle.armed = True

    def disarm(self):
        if self.vehicle.location.global_relative_frame.alt > 0.5:
            print(f"[Drone {self.id}] HATA: Disarm reddedildi! Drone su an havada.")
            return

        print(f"[Drone {self.id}] Disarm ediliyor")
        self.vehicle.armed = False

    def force_disarm(self):
        print(f"[Drone {self.id}] FORCE DISARM komutu gonderildi!")
        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            0,     # param 1 (0: disarm)
            21196, # param 2 (force)
            0, 0, 0, 0, 0)
        self.vehicle.send_mavlink(msg)

    def takeoff(self, target_altitude):
        if not self.vehicle.armed:
            print(f"[Drone {self.id}] HATA: Kalkis reddedildi! Motorlar ARM degil.")
            return
        print(f"[Drone {self.id}] Kalkis yapiliyor. Hedef: {target_altitude}m")
        self.vehicle.simple_takeoff(target_altitude)

    def land(self):
        print(f"[Drone {self.id}] Inis yapiliyor")
        self.set_mode("LAND")

    def move_local(self, x, y, z):
        if not self.vehicle.armed:
            print(f"[Drone {self.id}] HATA: MOVE reddedildi! Motorlar ARM degil.")
            return

        if self.vehicle.location.global_relative_frame.alt < 0.5:
            print(f"[Drone {self.id}] HATA: MOVE reddedildi! Drone yerde.")
            return
        
        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0, 0, 0,
            mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
            0b0000111111111000,
            x, y, -z,
            0, 0, 0, 0, 0, 0, 0, 0)
        self.vehicle.send_mavlink(msg)
        print(f"[Drone {self.id}] MOVE uygulandi: X:{x}, Y:{y}, Z:{z}")


# SÜRÜ KONTROL SINIFI (Dağıtık mimariye göre güncellendi)
class SwarmController:
    def __init__(self, connection_string, my_id):
        self.my_id = my_id
        print(f"[{self.my_id}] SİSTEMİ BAŞLATILIYOR")
        
        # Her Pi sadece kendi altındaki uçuş kartına bağlanır
        self.drone = SingleDrone(connection_string, drone_id=self.my_id) 
        print(f"[{self.my_id}] BAĞLANTI KURULDU")
        
        # MQTT İstemcisi
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
    def on_connect(self, client, userdata, flags, rc):
        print("MQTT Broker'a baglanildi. Arayuzden (GUI) komut bekleniyor")
        client.subscribe(MQTT_TOPIC)

    def on_message(self, client, userdata, msg):
        gelen_mesaj = msg.payload.decode("utf-8")
        
        parcalar = gelen_mesaj.split(":")
        hedef = parcalar[0]
        komut = parcalar[1]
        
        # EKLENDİ: Gelen komut bana ait değilse veya herkese (ALL) atılmadıysa hiç işlem yapma!
        if hedef != self.my_id and hedef != "ALL":
            return
            
        print(f"[MQTT ALINDI] {gelen_mesaj}")
        
        # Hedeflenen komutları sadece kendi drone'umuza uyguluyoruz
        drone = self.drone
        
        if komut == "ARM":
            drone.arm() 
            print(f"{drone.id} için ARM tetiklendi.")
            
        elif komut == "TAKEOFF":
            drone.takeoff(10) # Kalkış irtifası 10 metre
            print(f"{drone.id} için TAKEOFF tetiklendi.")
            
        elif komut == "LAND":
            drone.land()
            print(f"{drone.id} için LAND tetiklendi.")
            
        elif komut == "DISARM":
            drone.disarm() 
            print(f"{drone.id} için DISARM tetiklendi.")
            
        elif komut == "FORCE_DISARM":
            drone.force_disarm() 
            print(f"{drone.id} için FORCE_DISARM tetiklendi.")
            
        elif komut == "MOVE":
            if len(parcalar) == 3:
                koordinatlar = parcalar[2].split(",")
                x = float(koordinatlar[0])
                y = float(koordinatlar[1])
                z = float(koordinatlar[2])
                
                drone.move_local(x, y, z)
                print(f"{drone.id} MOVE -> X:{x} Y:{y} Z:{z}")

    def baslat(self):
        try:
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            print("\nSistem manuel olarak kapatildi.")


# ANA ÇALIŞTIRMA BLOĞU (Güncellendi)
if __name__ == "__main__": 
    # Terminalden girilen ID'yi alıyoruz (Örn: python3 swarm_controller.py D1)
    if len(sys.argv) > 1:
        cihaz_kimligi = sys.argv[1].upper() # D1, d1 girilse bile büyütür
    else:
        cihaz_kimligi = "D1" # Unutulursa varsayılan D1

    # Her cihazda tek bağlantı noktası var
    kullanilacak_port = '/dev/ttyACM0'
    
    # 1. Sistemi belirtilen kimlik ile kur
    swarm = SwarmController(kullanilacak_port, my_id=cihaz_kimligi)
    
    # 2. Sistemi başlat ve dinlemeye geç
    swarm.baslat()