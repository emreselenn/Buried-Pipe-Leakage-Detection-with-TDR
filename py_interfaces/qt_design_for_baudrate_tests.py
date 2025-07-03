# -*- coding: utf-8 -*-
"""
STM32 Haberlesme Arayuzu - Thread Tabanli Gercek Zamanli Okuma
"""

import sys
import os
import serial
import serial.tools.list_ports
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QComboBox,
                            QPushButton, QLabel, QTextEdit, QHBoxLayout, 
                            QLineEdit, QCheckBox)
from PyQt5.QtCore import QTimer, QElapsedTimer, QThread, pyqtSignal

class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self._running = True

    def run(self):
        while self._running:
            if self.serial_port and self.serial_port.in_waiting > 0:
                try:
                    data = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        self.data_received.emit(data)
                except Exception:
                    pass
            self.msleep(1)  # CPU'yu yormamak icin

    def stop(self):
        self._running = False

class SerialInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STM32 Haberlesme Arayuzu - Thread'li Surum")
        self.setGeometry(100, 100, 850, 850)

        self.serial_port = None
        self.reader_thread = None
        self.port_lock = False
        self.cycle_count = 0
        self.log_dir = "serial_logs"

        self.total_sent = 0
        self.success_count = 0
        self.error_count = 0
        self.max_messages = 200
        self.start_value = 0
        self.current_value = 0

        self.send_timer_elapsed = QElapsedTimer()
        self.send_duration = 0
        self.is_sending = False

        self.read_interval = 1
        self.test_mode = False
        self.last_read_time = 0

        self.init_ui()
        self.init_timers()
        self.create_log_directory()

    def init_ui(self):
        layout = QVBoxLayout()

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port Sec:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        layout.addLayout(port_layout)

        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baudrate Sec:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["2400","4800", "9600", "19200", "38400", "57600", "115200","128000", "230400", "460800"])
        baud_layout.addWidget(self.baudrate_combo)
        layout.addLayout(baud_layout)

        msg_count_layout = QHBoxLayout()
        msg_count_layout.addWidget(QLabel("Gonderilecek Mesaj Sayisi:"))
        self.msg_count_combo = QComboBox()
        self.msg_count_combo.addItems(["1", "200", "500", "1000", "3000", "10000"])
        self.msg_count_combo.setCurrentIndex(1)
        msg_count_layout.addWidget(self.msg_count_combo)
        layout.addLayout(msg_count_layout)

        read_settings_layout = QHBoxLayout()
        read_settings_layout.addWidget(QLabel("Okuma Periyodu:"))
        self.read_interval_combo = QComboBox()
        self.read_interval_combo.addItems([
            "Her mesajda oku (1:1)", 
            "Her 2 mesajda 1 oku", 
            "Her 5 mesajda 1 oku",
            "Her 10 mesajda 1 oku",
            "Her 50 mesajda 1 oku"
        ])
        read_settings_layout.addWidget(self.read_interval_combo)

        self.test_mode_check = QCheckBox("Test Modu (Zaman Aralikli Okuma)")
        read_settings_layout.addWidget(self.test_mode_check)
        layout.addLayout(read_settings_layout)

        btn_layout = QHBoxLayout()
        self.connect_button = QPushButton("Baglan")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.send_button = QPushButton("Gonder (200 Mesaj)")
        self.send_button.clicked.connect(self.start_auto_send)
        btn_layout.addWidget(self.connect_button)
        btn_layout.addWidget(self.send_button)
        layout.addLayout(btn_layout)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Baslangic Sayisi:"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Ornek: 10")
        start_layout.addWidget(self.start_input)
        layout.addLayout(start_layout)

        layout.addWidget(QLabel("\U0001F4E4 Gonderilen Veriler:"))
        self.sent_display = QTextEdit()
        self.sent_display.setReadOnly(True)
        layout.addWidget(self.sent_display)

        layout.addWidget(QLabel("\U0001F4E5 STM32'den Gelen Veriler:"))
        self.received_display = QTextEdit()
        self.received_display.setReadOnly(True)
        layout.addWidget(self.received_display)

        layout.addWidget(QLabel("\u274C Hatali Gelen Veriler:"))
        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        layout.addWidget(self.error_log)

        status_layout = QVBoxLayout()
        self.total_label = QLabel("Toplam Gonderim: 0")
        self.success_label = QLabel("Basarili Cevap: 0")
        self.error_label = QLabel("Hatali Veri Sayisi: 0")
        self.timer_label = QLabel("Gonderim Suresi: 0.000 saniye")
        self.status_label = QLabel("Durum: Bagli degil")
        status_layout.addWidget(self.total_label)
        status_layout.addWidget(self.success_label)
        status_layout.addWidget(self.error_label)
        status_layout.addWidget(self.timer_label)
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)

        self.setLayout(layout)

    def init_timers(self):
        self.send_timer = QTimer()
        self.send_timer.timeout.connect(self.auto_send_next)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_timer_display)
        self.update_timer.start(20)

    def create_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.close_connection()
        else:
            self.open_connection()

    def open_connection(self):
        port = self.port_combo.currentText()
        baud = int(self.baudrate_combo.currentText())
        try:
            if self.serial_port:
                self.serial_port.close()
            self.serial_port = serial.Serial(port=port, baudrate=baud, timeout=0)
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.connect_button.setText("Baglantiyi Kes")
            self.status_label.setText(f"Durum: Baglandi ({port} @ {baud})")

            self.reader_thread = SerialReaderThread(self.serial_port)
            self.reader_thread.data_received.connect(self.on_serial_data_received)
            self.reader_thread.start()

        except Exception as e:
            self.status_label.setText(f"Hata: {str(e)}")
            if self.serial_port:
                self.serial_port.close()
            self.serial_port = None

    def close_connection(self):
        try:
            if self.reader_thread:
                self.reader_thread.stop()
                self.reader_thread.quit()
                self.reader_thread.wait()
                self.reader_thread = None

            if self.serial_port:
                self.serial_port.close()

            self.connect_button.setText("Baglan")
            self.status_label.setText("Durum: Baglanti kesildi")
        except Exception as e:
            self.status_label.setText(f"Kapatma hatasi: {str(e)}")

    def start_auto_send(self):
        if not (self.serial_port and self.serial_port.is_open):
            self.sent_display.append("Baglanti yok.")
            return

        try:
            self.start_value = int(self.start_input.text())
            self.current_value = self.start_value
            self.total_sent = 0
            self.success_count = 0
            self.error_count = 0
            self.send_duration = 0
            self.max_messages = int(self.msg_count_combo.currentText())
            self.send_button.setText(f"Gonder ({self.max_messages} Mesaj)")

            self.read_interval = self.get_read_interval()
            self.test_mode = self.test_mode_check.isChecked()

            self.clear_displays()
            self.update_counters()
            self.send_timer_elapsed.start()
            self.is_sending = True
            self.send_timer.start(16)

            self.log_message(f"Otomatik gonderim baslatildi... Toplam {self.max_messages} mesaj gonderilecek.")
        except ValueError:
            self.log_message("⚠️ Gecerli bir sayi girin.", error=True)

    def get_read_interval(self):
        selections = {0: 1, 1: 2, 2: 5, 3: 10, 4: 50}
        return selections.get(self.read_interval_combo.currentIndex(), 1)

    def auto_send_next(self):
        if self.total_sent >= self.max_messages:
            self.send_timer.stop()
            self.is_sending = False
            self.send_duration = self.send_timer_elapsed.elapsed() / 1000.0
            self.timer_label.setText(f"Gonderim Suresi: {self.send_duration:.3f} saniye")
            self.log_message(f"✅ {self.max_messages} mesaj gonderildi.")
            self.cycle_count += 1
            return

        try:
            message = str(self.current_value) + '\n'
            self.serial_port.write(message.encode('utf-8'))
            self.log_message(f"Gonderilen: {self.current_value}")

            self.total_sent += 1
            self.current_value += 1
            self.update_counters()
        except Exception as e:
            self.log_message(f"Hata gonderirken: {e}", error=True)
            self.send_timer.stop()
            self.is_sending = False

    def on_serial_data_received(self, data):
        expected = str(self.current_value if self.test_mode else self.current_value - 1)

        if self.test_mode:
            if data == expected:
                self.success_count += 1
                self.log_message(f"[Test Modu] Gelen: {data} (Dogru)", receive=True)
            else:
                self.error_count += 1
                self.log_message(f"[Test Modu][Hata#{self.error_count}] Beklenen: {expected}, Alinan: {data}", error=True)
        else:
            if data == expected:
                self.success_count += 1
                self.log_message(f"Gelen: {data} (Dogru)", receive=True)
            else:
                self.error_count += 1
                self.log_message(f"[Hata#{self.error_count}] Beklenen: {expected}, Alinan: {data}", error=True)

        self.update_counters()

    def update_timer_display(self):
        if self.is_sending:
            elapsed = self.send_timer_elapsed.elapsed() / 1000.0
            self.timer_label.setText(f"Gonderim Suresi: {elapsed:.3f} saniye")

    def clear_displays(self):
        self.sent_display.clear()
        self.received_display.clear()
        self.error_log.clear()

    def update_counters(self):
        self.total_label.setText(f"Toplam Gonderim: {self.total_sent}")
        self.success_label.setText(f"Basarili Cevap: {self.success_count}")
        self.error_label.setText(f"Hatali Veri Sayisi: {self.error_count}")

    def log_message(self, message, error=False, receive=False):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_msg = f"[{timestamp}] {message}"
        if error:
            self.error_log.append(formatted_msg)
        elif receive:
            self.received_display.append(formatted_msg)
        else:
            self.sent_display.append(formatted_msg)

    def closeEvent(self, event):
        self.close_connection()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialInterface()
    window.show()
    sys.exit(app.exec_())
