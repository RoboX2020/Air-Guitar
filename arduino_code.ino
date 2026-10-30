// ============================================================================
// arduino_code.ino - the wrist sensor half of Air Guitar.
//
// WHAT THIS PROGRAM DOES (it runs ON the Arduino board, not your computer):
//   An MPU6050 motion sensor chip reports how the wrist is tilted and how
//   hard it is moving. This program reads those numbers about 60 times per
//   second and sends them over the USB cable as simple text lines like
//   "12.5:163" (meaning: wrist angle 12.5 degrees, strum force 163).
//   The Python program air_guitar.py on the computer reads those lines and
//   turns them into guitar sounds.
//
// THE WIRING: the MPU6050 talks over a two-wire connection called I2C
//   (SDA + SCL pins, plus power). The Arduino's Wire library handles it.
//
// WHEN DEBUGGING:
//   - All readings are 0 or nonsense: check the SDA/SCL wiring.
//   - Python prints nothing: make sure the baud rate here (115200) matches
//     BAUD_RATE in air_guitar.py, and that no other program (like the
//     Arduino Serial Monitor) is holding the port open.
// ============================================================================

// Arduino's built-in library for I2C (the sensor's language)
#include <Wire.h>

// the MPU6050's fixed I2C "house number" on the wire
const int MPU_ADDR = 0x68;
// latest raw acceleration on the three axes (x, y, z)
int16_t acX, acY, acZ;

// setup() runs once, every time the board powers on or resets.
void setup() {
  // open the USB text channel at 115200 baud (must match the Python side)
  Serial.begin(115200);
  // join the I2C bus as the boss ("controller")
  Wire.begin();
  
  // Wake up MPU6050
  // The chip starts in sleep mode. Writing 0 to its power register (0x6B)
  // wakes it up so it starts measuring.
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
}

// loop() runs over and over, forever, as fast as we let it.
void loop() {
  // Read Accelerometer
  // Ask the chip for the 6 bytes starting at register 0x3B: that is where
  // it keeps the newest X, Y and Z acceleration, two bytes per axis.
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6, true);

  // Each axis arrives as two separate bytes; "<<8|" glues them back into one
  // 16-bit number (high byte shifted up, low byte added below).
  acX = Wire.read()<<8|Wire.read();
  acY = Wire.read()<<8|Wire.read();
  acZ = Wire.read()<<8|Wire.read();

  // Calculate ROLL (Wrist Angle)
  // When flat, it's 0. Tilted left is negative, right is positive.
  // atan2(acY, acZ) turns the gravity pull on the Y and Z axes into a tilt
  // angle in radians; "* 180.0 / PI" converts radians to degrees.
  float roll = atan2(acY, acZ) * 180.0 / PI;

  // Calculate FORCE (Strumming magnitude)
  // Total acceleration strength in any direction: the length of the
  // (x, y, z) vector, i.e. sqrt(x^2 + y^2 + z^2), divided by 100 to get a
  // small friendly number. A sharp wrist flick makes this jump.
  long force = sqrt((long)acX*acX + (long)acY*acY + (long)acZ*acZ) / 100;

  // Send to Python: "ROLL:FORCE"
  // One text line per reading, e.g. "-4.2:163". println adds the newline
  // that the Python side uses to tell messages apart.
  Serial.print(roll);
  Serial.print(":");
  Serial.println(force);

  delay(15); // ~60Hz sample rate
}
