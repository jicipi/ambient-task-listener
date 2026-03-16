# Ambient Task Listener - Hardware

## 1) Composants

- ESP32-P4-NANO
- INMP441 microphone I2S
- MAX98357A ampli I2S
- Speaker 4 ohm / 3W
- TFT 2.4" SPI
- Module MicroSD
- PIR sensor HC-SR501
- MPU6050 IMU
- Batterie 18650
- Chargeur TP4056

## 2) Wiring principal

### Microphone INMP441

- VCC -> 3.3V
- GND -> GND
- SCK -> GPIO I2S_SCK
- WS -> GPIO I2S_WS
- SD -> GPIO I2S_SD

### Ampli MAX98357A

- VIN -> 5V
- GND -> GND
- DIN -> GPIO I2S_DATA
- BCLK -> GPIO I2S_SCK
- LRC -> GPIO I2S_WS

### TFT SPI

- VCC -> 3.3V
- GND -> GND
- SCK -> SPI_CLK
- MOSI -> SPI_MOSI
- CS -> GPIO
- DC -> GPIO
- RST -> GPIO

### PIR Sensor

- VCC -> 5V
- GND -> GND
- OUT -> GPIO

### MicroSD

- VCC -> 3.3V
- GND -> GND
- MOSI -> SPI_MOSI
- MISO -> SPI_MISO
- CLK -> SPI_CLK
- CS -> GPIO

## 3) Microphones et capture de piece

### INMP441

Bon pour un MVP et des tests de proximite.

Usage realiste:

- 0.5 a 1 m: bon
- 1 a 2 m: acceptable
- Au-dela: vite limite selon le bruit

### Pour une grande piece

Pistes d'amelioration:

- Utiliser 2 ou 3 micros
- Faire un boitier bien oriente
- Ajouter beamforming plus tard
- Envisager des micros I2S a meilleur SNR

Objectif recommande:

Commencer avec un seul INMP441, valider le pipeline, puis ameliorer la captation ensuite.
