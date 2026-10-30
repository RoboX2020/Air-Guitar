# ============================================================================
# Air Guitar - play guitar by moving your hand, no guitar needed.
#
# THE FULL SETUP (two halves that talk to each other):
#   1. An Arduino board with an MPU6050 motion sensor is strapped to your
#      wrist. It measures your wrist angle and how hard you flick, and sends
#      those numbers over the USB cable many times per second.
#      (That half lives in arduino_code.ino in this same folder.)
#   2. THIS Python program reads those numbers and plays guitar sounds:
#      tilting your wrist chooses WHICH string, and flicking hard enough
#      "strums" it.
#
# HOW THE SOUND IS MADE: there is no recorded guitar audio here. Each
# string's sound is synthesized (built from scratch) with the Karplus-Strong
# algorithm - see generate_string_sound() below for the friendly version.
#
# BEFORE YOU RUN:
#   - Upload arduino_code.ino to the Arduino first and plug it in.
#   - Fix SERIAL_PORT below so it matches your computer's port name.
#   - Install the libraries: pip install pyserial sounddevice numpy
#
# WHEN DEBUGGING:
#   - "Check Serial Port!": the SERIAL_PORT name is wrong or the board is
#     unplugged. On Windows it looks like "COM3", on Mac/Linux like
#     "/dev/cu.usbmodem1101".
#   - Sounds trigger by themselves: the sensor zero point drifted; restart
#     and hold your hand still during the 3-second calibration.
# ============================================================================

# pyserial: reads the numbers the Arduino sends over USB
import serial
# built-in: small pauses and timers
import time
# arrays/math: the audio is stored and mixed as number arrays
import numpy as np
# plays audio through your speakers in real time
import sounddevice as sd
# built-in: used to print audio warnings to the error output
import sys
# built-in: keeps the sound list safe while audio plays
import threading

# --- CONFIGURATION ---
# UPDATE THIS PORT to match your Arduino (e.g., COM3 or /dev/cu.usbmodem...)
SERIAL_PORT = '/dev/cu.usbmodem1101' 
# how fast the Arduino and computer talk; must match the Arduino's Serial.begin()
BAUD_RATE = 115200
# audio quality: 44,100 measurements per second (CD quality)
SAMPLE_RATE = 44100
# how hard a wrist flick must be to count as a strum; raise it if strings trigger too easily
MIN_STRUM_FORCE = 140 

# --- AUDIO ENGINE ---
# GuitarEngine is the "mixer": it keeps a list of every string sound that is
# still ringing, and every time the speakers need more audio it blends all
# the ringing sounds together.
class GuitarEngine:
    def __init__(self):
        # Each entry is [the sound's samples, how far we have played so far].
        self.active_sounds = [] 
        self.lock = threading.Lock()
        
    # Adds a freshly strummed string to the list of sounds being played.
    # [sound_array, 0] means "this sound, played from the beginning".
    def add_sound(self, sound_array):
        with self.lock:
            self.active_sounds.append([sound_array, 0])

    # sounddevice calls this function about 40 times per second whenever the
    # speakers need the next chunk of audio (a chunk is `frames` samples).
    # It must run fast and never wait, or the audio stutters.
    def callback(self, outdata, frames, time, status):
        if status: print(status, file=sys.stderr)
        # start with silence, then add each ringing string
        mixed_audio = np.zeros(frames)
        with self.lock:
            # Walk the list backwards so removing finished sounds mid-loop
            # does not skip the next one.
            for i in range(len(self.active_sounds) - 1, -1, -1):
                sound, idx = self.active_sounds[i]
                remaining = len(sound) - idx
                if remaining > frames:
                    # This string still has plenty left: add the next chunk.
                    mixed_audio += sound[idx : idx + frames]
                    self.active_sounds[i][1] += frames
                else:
                    # This string ends inside this chunk: add its tail and
                    # drop it from the list.
                    mixed_audio[:remaining] += sound[idx:]
                    self.active_sounds.pop(i)
        
        # Limiter/Distortion
        # tanh squishes any too-loud mix back into range (like a soft
        # guitar-amp overdrive) so several strings at once never clip harshly.
        mixed_audio = np.tanh(mixed_audio) * 0.5
        # hand the finished chunk to the speakers
        outdata[:] = mixed_audio.reshape(-1, 1)

# Builds the sound of one plucked string using the Karplus-Strong algorithm.
# The friendly explanation:
#   1. Start with a tiny burst of random noise (like the messy "snap" of a
#      pick hitting a string).
#   2. Then, over and over: each new value is the average of the last two,
#      shrunk a little. The averaging smooths the noise into a clear musical
#      pitch, and the shrinking makes the note fade out like a real string.
#   The loop length N decides the pitch: short loop = high note.
def generate_string_sound(freq, duration=3.0, decay=0.992):
    # total length of the finished sound
    n_samples = int(duration * SAMPLE_RATE)
    # loop length that produces this pitch
    N = int(SAMPLE_RATE / freq)
    # the initial noise burst
    buf = np.random.randn(N)
    # the finished sound gets built here
    samples = np.zeros(n_samples)
    for i in range(n_samples):
        samples[i] = buf[i % N]
        buf[i % N] = 0.5 * (buf[i % N] + buf[(i + 1) % N]) * decay
    return samples.astype(np.float32)

# --- VIRTUAL STRINGS (Open E Tuning) ---
# The six strings of the air guitar. "angle" is the wrist tilt (in degrees)
# where that string sits: sweep your wrist and you cross the strings one by
# one, like strumming across real strings. The note frequencies (82.41 Hz
# for Low E, etc.) are the standard tuning of a real guitar.
# These sounds are generated once at startup, so the first launch takes a
# few seconds.
VIRTUAL_STRINGS = [
    {"angle": -40, "note": "Low E", "sound": generate_string_sound(82.41)},
    {"angle": -25, "note": "A",     "sound": generate_string_sound(110.00)},
    {"angle": -10, "note": "D",     "sound": generate_string_sound(146.83)},
    {"angle": 5,   "note": "G",     "sound": generate_string_sound(196.00)},
    {"angle": 20,  "note": "B",     "sound": generate_string_sound(246.94)},
    {"angle": 35,  "note": "High E","sound": generate_string_sound(329.63)},
]

# Measures where "wrist neutral" is for this session. Sensor boards are never
# perfectly level, so instead of trusting the raw numbers we watch the wrist
# for 1.5 seconds and treat the average as zero. `ser` is the open USB
# connection to the Arduino. Returns the offset to subtract from readings.
def calibrate_sensor(ser):
    print("\n   HOLD HAND NEUTRAL... Calibrating in 3 seconds...")
    time.sleep(3)
    readings = []
    start = time.time()
    while time.time() - start < 1.5:
        # only read when the Arduino has sent something
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if ":" in line:
                    # messages look like "ANGLE:FORCE"; we only need the angle here
                    r, _ = line.split(":")
                    readings.append(float(r))
            # ignore garbled half-messages and keep listening
            except: pass
    if not readings: return 0.0
    offset = sum(readings) / len(readings)
    print(f"   Done! Zero point: {offset:.1f}\n")
    return offset

# The main program: start the audio, connect to the Arduino, calibrate,
# then loop forever watching for strums.
def main():
    engine = GuitarEngine()
    # Open the speaker stream. From now on, engine.callback runs by itself in
    # the background whenever the speakers need more audio.
    stream = sd.OutputStream(channels=1, samplerate=SAMPLE_RATE, callback=engine.callback)
    stream.start()

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
        # Arduino boards restart when connected; give it a moment
        time.sleep(2)
    except:
        print("Check Serial Port!")
        return

    offset = calibrate_sensor(ser)
    print("🎸 READY! Sweep wrist to play.")
    
    # "no previous reading yet" marker (-999 is impossible for a real angle)
    prev_roll = -999
    
    try:
        while True:
            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if ":" in line:
                        r_str, f_str = line.split(":")
                        # angle relative to your calibrated neutral pose
                        current_roll = float(r_str) - offset
                        force = int(f_str)

                        if force > MIN_STRUM_FORCE:
                            # A strum is happening. A string "plays" when the
                            # wrist CROSSES its angle line between the last
                            # reading and this one, in either direction -
                            # like a pick crossing a real string.
                            for s in VIRTUAL_STRINGS:
                                ang = s["angle"]
                                if prev_roll != -999:
                                    # Check for crossing the virtual string line
                                    down = (prev_roll > ang >= current_roll)
                                    up = (prev_roll < ang <= current_roll)
                                    if down or up:
                                        engine.add_sound(s["sound"])
                                        print(f"🎵 {s['note']}")
                        prev_roll = current_roll
                # ignore garbled half-messages and keep listening
                except: pass
            else:
                # nothing arrived: nap 1 ms so the loop does not spin the CPU at 100%
                time.sleep(0.001)
    except KeyboardInterrupt:
        # Ctrl+C lands here: shut down politely instead of crashing.
        stream.stop()
        ser.close()

# Standard Python entry point: only run main() when this file is started
# directly, not when another file imports it.
if __name__ == "__main__":
    main()
