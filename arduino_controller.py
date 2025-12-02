import json
import time
import serial
import serial.tools.list_ports


def find_arduino_port():
    """
    Tenta descobrir automaticamente a porta do Arduino/ESP.
    Retorna algo como 'COM3' ou None se não encontrar.
    """
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        if "arduino" in desc or "ch340" in desc or "usb-serial" in desc:
            return p.device
    return None


class ArduinoController:
    def __init__(self, port=None, baudrate=9600):
        """
        Controlador básico de porta serial.
        Se port=None, tenta detectar automaticamente.
        """
        self.serial_conn = None
        self.connected = False

        if port is None:
            port = find_arduino_port()

        if not port:
            print("⚠️ Nenhuma porta de Arduino encontrada, seguindo sem conexão.")
            return

        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)
            print(f"✅ Conectado ao Arduino em {port}")
            self.connected = True
        except Exception as e:
            print(f"⚠️ Arduino não conectado ({port}): {e}")
            self.connected = False

    def send_command(self, command, value=None):
        """Envia um comando JSON para o Arduino (se estiver conectado)."""
        if not self.connected or not self.serial_conn or not self.serial_conn.is_open:
            return False

        try:
            msg = {"cmd": command, "value": value}
            self.serial_conn.write((json.dumps(msg) + "\n").encode())
            return True
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")
            self.connected = False
            return False

    def read_response(self):
        """Lê uma linha JSON de resposta (se houver)."""
        if not self.connected or not self.serial_conn or not self.serial_conn.is_open:
            return None

        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode(errors="ignore").strip()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        print(f"Resposta não-JSON do Arduino: {line}")
                        return {"raw": line}
        except Exception as e:
            print(f"Erro ao ler resposta: {e}")
            self.connected = False
        return None

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False


class SmartLabController:
    """
    Camada de alto nível usada pelo JARVIS.
    Se não houver Arduino, os métodos apenas falham de forma amigável.
    """

    def __init__(self, port=None):
        self.arduino = ArduinoController(port=port)

    @property
    def connected(self):
        return bool(self.arduino and self.arduino.connected)

    def ligar_luz(self, sala="geral"):
        if not self.connected:
            return False
        pin = {"geral": 13, "teste": 12}
        return self.arduino.send_command("led_on", pin.get(sala, 13))

    def desligar_luz(self, sala="geral"):
        if not self.connected:
            return False
        pin = {"geral": 13, "teste": 12}
        return self.arduino.send_command("led_off", pin.get(sala, 13))

    def leitura_sensor(self, tipo="temperatura"):
        if not self.connected:
            return None
        self.arduino.send_command("read_sensor", tipo)
        time.sleep(0.5)
        return self.arduino.read_response()

    def close(self):
        if self.arduino:
            self.arduino.close()
