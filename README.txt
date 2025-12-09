# 🎸 Arduino Air Guitar (Spatial Audio)

A virtual instrument that uses an MPU6050 accelerometer and Python to simulate "invisible strings" floating in the air. 

## How it Works
1. **Arduino:** Reads the Roll (wrist angle) and Acceleration (strum force) from the MPU6050.
2. **Python:** Receives the data and maps the angle to 6 virtual strings.
3. **Physics Engine:** Uses the Karplus-Strong algorithm (string physics) to synthesize audio in real-time using `numpy` and `sounddevice`.

## Hardware
* Arduino Uno
* MPU6050 Accelerometer
* 4 Jumper Wires

## Wiring
| MPU6050 | Arduino |
|:---:|:---:|
| VCC | 5V |
| GND | GND |
| SCL | A5 |
| SDA | A4 |

## How to Play
1. Upload the code in `arduino_code` to your board.
2. Run `python air_guitar.py`.
3. **Calibrate:** Hold your hand in a neutral position when prompted.
4. **Play:** * Rotate wrist **Left** for Low Notes.
   * Rotate wrist **Right** for High Notes.
   * "Strum" (shake wrist) to trigger sound.
