
# AquaSync : Sistem Pengisian Air Otomatis dengan Sensor Ultrasonik

## Component Used
| Component    | Type | Used for|
| -------- | ------- | ------- |
| Ultrasonic Sensor HY-SRF05  | Sensor    | Mengukur jarak air untuk nyala matikan valve otomatis    |
| Waterflow sensor YF-B1 | Sensor     | Mengukur debit air    |
| Solenoid Valve    | Non-sensor    | Buka tutup aliran air    |


## Pitch idea
AquaSync adalah sistem pengisian air otomatis yang menggunakan sensor ultrasonik untuk mendeteksi ketinggian air dan secara otomatis menghentikan aliran saat wadah penuh. Sistem ini dilengkapi dengan konektivitas IoT untuk memantau dan mengontrol pengisian air melalui website.

## How does IOT and AI correlate in this project?
IoT: Sistem akan terhubung ke platform IoT yang memungkinkan pemantauan real-time terhadap penggunaan air dan kondisi perangkat. ESP32 membaca data sensor ultrasonik dan mengontrol solenoid valve. Data tingkat air dikirim ke website yang memungkinkan pemantauan real-time dan kontrol jarak jauh.

AI: Algoritma AI dapat digunakan untuk menganalisis pola penggunaan air, memberikan rekomendasi pengisian optimal, serta mendeteksi anomali seperti kebocoran atau penggunaan berlebihan yang tidak wajar.

## Why this is useful?
**Lebih efisien dan higienis**, keran dari aquasync tidak perlu diputar secara manual karena keran akan secara otomatis berhenti jika sudah penuh, sehingga dapat menghindari kontaminasi dan boros air.

**Lebih akurat**, deteksi tingkat air berbasis sensor ultrasonik dibandingkan sensor mekanis, sehingga lebih akurat dan tahan lama.

**Integrasi IoT untuk pemantauan real-time melalui website**, aquasync dapat dikontrol menggunakan website, sehingga pengguna tahu berapa banyak air yang sudah digunakan.

**Dilengkapi AI** yang dapat menganalisis pola penggunaan dan memberikan peringatan dini jika terjadi pemborosan atau malfungsi.
