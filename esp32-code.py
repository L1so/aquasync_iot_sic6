from machine import Pin, SoftI2C, time_pulse_us
import urequests
import ssd1306
import time
import network
import math

# Ganti dengan kredensial WiFi kamu
WIFI_SSID = 'Rahasia'
WIFI_PASSWORD = 'rahasiadong'

# Define pins
solenoid_pin = Pin(26, Pin.OUT)
flow_sensor_pin = Pin(35, Pin.IN)
trig_pin = Pin(19, Pin.OUT)
echo_pin = Pin(18, Pin.IN)

# I2C setup untuk OLED
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Variabel aliran
flow_count = 0
total_volume_ml = 0
flow_rate_start_time = None

# Flow sensor interrupt
def flow_sensor_callback(pin):
    global flow_count
    flow_count += 1

flow_sensor_pin.irq(trigger=Pin.IRQ_RISING, handler=flow_sensor_callback)

# Fungsi ultrasonic
def measure_distance():
    trig_pin.value(1)
    time.sleep_us(10)
    trig_pin.value(0)
    duration = time_pulse_us(echo_pin, 1, 30000)
    if duration < 0:
        return None
    distance = (duration * 0.0343) / 2
    return distance

# Hitung volume air
def calculate_volume():
    global flow_count, total_volume_ml
    liters = flow_count / 450
    volume_ml = liters * 1000
    total_volume_ml += volume_ml
    flow_count = 0
    return total_volume_ml

# OLED display
def display_measurement(current_volume, faucet_status, warning_text=None):
    oled.fill(0)
    oled.text('Total Volume:', 0, 0)
    oled.text('{} mL'.format(round(current_volume, 1)), 0, 20)
    oled.text('Faucet: {}'.format(faucet_status), 0, 40)
    if warning_text:
        oled.text(warning_text, 0, 54)
    oled.show()

# WiFi connect
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print('Connecting to WiFi...')
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to WiFi:', wlan.ifconfig())

# Kirim ke Flask API
def send_data_to_api(volume):
    url = 'http://210.16.65.137:5000/send-data'
    headers = {'Content-Type': 'application/json'}
    data = {
        "volume": round(volume, 1)
    }
    response = urequests.post(url, json=data, headers=headers)
    print("API Response:", response.text)
    response.close()

# Kontrol keran otomatis
def control_solenoid(target_volume_ml):
    global total_volume_ml, flow_rate_start_time
    while True:
        distance = measure_distance()
        if distance is not None:
            print("Distance: {:.2f} cm".format(distance))

            if distance < 5:
                solenoid_pin.value(0)
                print("Faucet is OFF karena jarak < 5cm")

                # ⬇️ Blinking OLED Warning makin cepat
                blink_durations = [0.5, 0.3, 0.1]
                for delay in blink_durations:
                    display_measurement(total_volume_ml, "OFF", "Wadah nyaris penuh!")
                    time.sleep(delay)
                    display_measurement(total_volume_ml, "OFF", "")
                    time.sleep(delay)

                # ⬇️ Tampilkan warning statis
                display_measurement(total_volume_ml, "OFF", "Wadah nyaris penuh!")

                if flow_rate_start_time:
                    flow_duration = time.ticks_diff(time.ticks_ms(), flow_rate_start_time) / 1000
                    print(f"Flow Duration: {flow_duration} seconds")
                    send_data_to_api(total_volume_ml)
                total_volume_ml = 0
                flow_rate_start_time = None

            elif distance >= 5 and distance <= 30:
                if flow_rate_start_time is None:
                    flow_rate_start_time = time.ticks_ms()
                solenoid_pin.value(1)
                print("Faucet is ON")
                current_volume = calculate_volume()
                display_measurement(current_volume, "ON")

            else:
                solenoid_pin.value(0)
                print("No object detected dalam 20cm, Faucet OFF")
                display_measurement(total_volume_ml, "OFF")

        time.sleep(1)

# Main loop
try:
    connect_wifi()
    target_volume = 1000
    control_solenoid(target_volume)

except KeyboardInterrupt:
    print("Program stopped.")
    solenoid_pin.value(0)
    oled.fill(0)
    oled.text('Program Stopped', 0, 0)
    oled.show()
