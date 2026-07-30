import sys #Python'un windowsla iletişimi için
import paho.mqtt.client as mqtt #MQTT haberleşme kütüphanesi 
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLineEdit, QHBoxLayout, QLabel, QComboBox)
#Sekmede tıklamaları vs işletim sistemine iletir(motor), sekmenin dış hattı için, butonları oluşturmamızı sağlar,YAZI KUTUSU
#Butonları otomatik alt alta dizme, (boş kanvas) butonları kutucuk içine yerleştirmemizi sağlar, YAN YANA DİZME

# Arayüzümüzü OOP standartlarına uygun olarak bir Class olarak tasarlıyoruz.

class DroneControlGUI(QMainWindow): #DroneControlGUI adında bir şablon ve QMainWindows sayesinde hazır bir pencere oluşturuyoruz
    def __init__(self): #Object'i kullanıma hazır hale getirmek için class özelliklerini object'in kendisine aktarır. constructor
        super().__init__() #Miras alınan üst sınıftan(super onu temsil eder) yani QMainWindow ile bir taslak pencere hazırla.
        
        # 1. Pencerenin temel özellikleri
        self.setWindowTitle("Drone Kontrol Arayüzü")
        self.setGeometry(100, 100, 350, 600) #(ekranın solundan x kadar boşluk bırak, y ,genişlik,yükseklik - butonlar sığsın diye yüksekliği artırdık)
        
        # MQTT AYARLARI VE THREADING
        self.broker_address = "broker.hivemq.com" # Test için ücretsiz genel MQTT sunucusu
        self.topic = "cezeri/drone/komut" # Mesajlarımızı bırakacağımız özel başlık (Hangi odaya/kanala mesaj atacağımız)
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Kendimize bir postacı nesnesi üretiyoruz. 
        self.client.connect(self.broker_address, 1883) # İstemciyi broker'a  bağlıyoruz. 1883 dünya standart portudur.
        
        self.client.loop_start() # THREADING: MQTT dinleme/gönderme işini ana arayüzden ayırıp ayrı thread'de çalıştırır.

        # 2. Ana widget ve Layout (Düzen) oluşturma
        central_widget = QWidget() #central_widget adında boş bir kanvas(QWidget) oluştur
        self.setCentralWidget(central_widget) #merkezine bu kanvası koy. kanvasın üzerine butonlar koyulur.
        
        layout = QVBoxLayout() 
        
        # ========================================================
        # SÜRÜ KONTROLÜ (ALL) BÖLÜMÜ
        # ========================================================
        self.lbl_suru = QLabel("SÜRÜ KONTROLÜ")
        layout.addWidget(self.lbl_suru)

        # 3. İstenen temel komut butonlarını oluşturma ve düzene ekleme
        self.btn_suru_arm = QPushButton("ARM") 
        layout.addWidget(self.btn_suru_arm) 
        
        self.btn_suru_takeoff = QPushButton("TAKEOFF")
        layout.addWidget(self.btn_suru_takeoff)
        
        # MESAFE GİRİŞ KUTUCUKLARI (SÜRÜ İÇİN)
        suru_input_layout = QHBoxLayout() # X, Y, Z kutucuklarını yan yana koymak için
        
        self.suru_input_x = QLineEdit("0") 
        self.suru_input_x.setPlaceholderText("X (m)")
        self.suru_input_y = QLineEdit("0")
        self.suru_input_y.setPlaceholderText("Y (m)")
        self.suru_input_z = QLineEdit("0")
        self.suru_input_z.setPlaceholderText("Z (m)")
        
        suru_input_layout.addWidget(self.suru_input_x)
        suru_input_layout.addWidget(self.suru_input_y)
        suru_input_layout.addWidget(self.suru_input_z)
        layout.addLayout(suru_input_layout) 

        self.btn_suru_move = QPushButton("MOVE")
        layout.addWidget(self.btn_suru_move)
        
        self.btn_suru_land = QPushButton("LAND")
        layout.addWidget(self.btn_suru_land)
        
        self.btn_suru_disarm = QPushButton("DISARM")
        layout.addWidget(self.btn_suru_disarm)

        self.btn_suru_force_disarm = QPushButton("FORCE DISARM")
        self.btn_suru_force_disarm.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        layout.addWidget(self.btn_suru_force_disarm)

        # Boşluk bırakmak için sahte bir etiket (Görsellik için)
        layout.addWidget(QLabel(" "))

        # ========================================================
        # TEKİL DRONE KONTROLÜ BÖLÜMÜ
        # ========================================================
        self.lbl_tekil = QLabel("TEKİL DRONE KONTROLÜ")
        layout.addWidget(self.lbl_tekil)

        # Seçim Ekranı
        self.drone_secici = QComboBox()
        self.drone_secici.addItems(["Drone 1 (D1)", "Drone 2 (D2)", "Drone 3 (D3)"])
        layout.addWidget(self.drone_secici)

        self.btn_tekil_arm = QPushButton("ARM")
        layout.addWidget(self.btn_tekil_arm)

        self.btn_tekil_takeoff = QPushButton("TAKEOFF")
        layout.addWidget(self.btn_tekil_takeoff)

        # MESAFE GİRİŞ KUTUCUKLARI (TEKİL İÇİN)
        tekil_input_layout = QHBoxLayout()
        
        self.tekil_input_x = QLineEdit("0")
        self.tekil_input_x.setPlaceholderText("X (m)")
        self.tekil_input_y = QLineEdit("0")
        self.tekil_input_y.setPlaceholderText("Y (m)")
        self.tekil_input_z = QLineEdit("0")
        self.tekil_input_z.setPlaceholderText("Z (m)")
        
        tekil_input_layout.addWidget(self.tekil_input_x)
        tekil_input_layout.addWidget(self.tekil_input_y)
        tekil_input_layout.addWidget(self.tekil_input_z)
        layout.addLayout(tekil_input_layout)

        self.btn_tekil_move = QPushButton("MOVE")
        layout.addWidget(self.btn_tekil_move)

        self.btn_tekil_land = QPushButton("LAND")
        layout.addWidget(self.btn_tekil_land)

        self.btn_tekil_disarm = QPushButton("DISARM")
        layout.addWidget(self.btn_tekil_disarm)

        self.btn_tekil_force_disarm = QPushButton("FORCE DISARM")
        self.btn_tekil_force_disarm.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        layout.addWidget(self.btn_tekil_force_disarm)

        # 4. Hazırladığımız bu yukarıdan aşağı düzeni ana pencereye yerleştiriyoruz.
        central_widget.setLayout(layout) 

        # BUTONLARI FONKSİYONLARA BAĞLAMA 
        self.btn_suru_arm.clicked.connect(self.send_suru_arm)
        self.btn_suru_takeoff.clicked.connect(self.send_suru_takeoff)
        self.btn_suru_move.clicked.connect(self.send_suru_move)
        self.btn_suru_land.clicked.connect(self.send_suru_land)
        self.btn_suru_disarm.clicked.connect(self.send_suru_disarm)
        self.btn_suru_force_disarm.clicked.connect(self.send_suru_force_disarm)

        self.btn_tekil_arm.clicked.connect(self.send_tekil_arm)
        self.btn_tekil_takeoff.clicked.connect(self.send_tekil_takeoff)
        self.btn_tekil_move.clicked.connect(self.send_tekil_move)
        self.btn_tekil_land.clicked.connect(self.send_tekil_land)
        self.btn_tekil_disarm.clicked.connect(self.send_tekil_disarm)
        self.btn_tekil_force_disarm.clicked.connect(self.send_tekil_force_disarm)


    # ========================================================
    # MQTT PUBLISH METOTLARI (SÜRÜ İÇİN - "ALL:" ÖNEKLİ)
    # ========================================================
    def send_suru_arm(self):
        self.client.publish(self.topic, "ALL:ARM") 
        print("Sisteme gönderildi: ALL:ARM") 

    def send_suru_takeoff(self):
        self.client.publish(self.topic, "ALL:TAKEOFF")
        print("Sisteme gönderildi: ALL:TAKEOFF")

    def send_suru_move(self):
        x = self.suru_input_x.text().strip()
        y = self.suru_input_y.text().strip()
        z = self.suru_input_z.text().strip()
        
        if not x: x = "0"
        if not y: y = "0"
        if not z: z = "0"
        
        mesaj = f"ALL:MOVE:{x},{y},{z}"
        self.client.publish(self.topic, mesaj)
        print(f"Gonderilen: {mesaj}")

    def send_suru_land(self):
        self.client.publish(self.topic, "ALL:LAND")
        print("Sisteme gönderildi: ALL:LAND")

    def send_suru_disarm(self):
        self.client.publish(self.topic, "ALL:DISARM")
        print("Sisteme gönderildi: ALL:DISARM")

    def send_suru_force_disarm(self):
        self.client.publish(self.topic, "ALL:FORCE_DISARM")
        print("Sisteme gönderildi: ALL:FORCE_DISARM ")    
    
    # MQTT PUBLISH METOTLARI (TEKİL İÇİN )
    def get_selected_drone_id(self):
        # ComboBox'taki yazının içinden sadece D1, D2 kısmını çeker
        secili_metin = self.drone_secici.currentText()
        hedef_id = secili_metin.split("(")[1].replace(")", "")
        return hedef_id

    def send_tekil_arm(self):
        hedef = self.get_selected_drone_id()
        mesaj = f"{hedef}:ARM"
        self.client.publish(self.topic, mesaj) 
        print(f"Sisteme gönderildi: {mesaj}") 

    def send_tekil_takeoff(self):
        hedef = self.get_selected_drone_id()
        mesaj = f"{hedef}:TAKEOFF"
        self.client.publish(self.topic, mesaj)
        print(f"Sisteme gönderildi: {mesaj}")

    def send_tekil_move(self):
        hedef = self.get_selected_drone_id()
        x = self.tekil_input_x.text().strip()
        y = self.tekil_input_y.text().strip()
        z = self.tekil_input_z.text().strip()
        
        if not x: x = "0"
        if not y: y = "0"
        if not z: z = "0"
        
        mesaj = f"{hedef}:MOVE:{x},{y},{z}"
        self.client.publish(self.topic, mesaj)
        print(f"Gonderilen: {mesaj}")

    def send_tekil_land(self):
        hedef = self.get_selected_drone_id()
        mesaj = f"{hedef}:LAND"
        self.client.publish(self.topic, mesaj)
        print(f"Sisteme gönderildi: {mesaj}")

    def send_tekil_disarm(self):
        hedef = self.get_selected_drone_id()
        mesaj = f"{hedef}:DISARM"
        self.client.publish(self.topic, mesaj)
        print(f"Sisteme gönderildi: {mesaj}")

    def send_tekil_force_disarm(self):
        hedef = self.get_selected_drone_id()
        mesaj = f"{hedef}:FORCE_DISARM"
        self.client.publish(self.topic, mesaj)
        print(f"Sisteme gönderildi: {mesaj}")


# Uygulamanın çalıştırıldığı ana tetikleyici blok
if __name__ == "__main__": # Güvenlik
    app = QApplication(sys.argv) 
    window = DroneControlGUI() 
    window.show() 
    sys.exit(app.exec())