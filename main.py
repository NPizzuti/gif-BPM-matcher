import pyaudio
import numpy as np
import librosa
from obswebsocket import obsws, requests, exceptions


# Connect to OBS WebSocket
host = "192.168.1.88"
port = 4455  # Change if necessary
password = "<put your OBS web socket password here>"  # Set in OBS WebSocket settings


ws = obsws(host, port, password)
print('Created WS')
ws.connect()
print('Connected to WS')

# Test connection by requesting OBS version
scenes = ws.call(requests.GetSceneList())
current_scene = ws.call(requests.GetCurrentProgramScene())
for s in scenes.getScenes():
    print(s)
print('Current scene is', current_scene)



# Name of the media source in OBS
source_name = "MyGIFSource"


# Audio stream configuration
CHUNK = 4096  # Number of audio frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit audio format
CHANNELS = 1  # Stereo audio
RATE = 44100  # Standard sample rate


# Initialize PyAudio
p = pyaudio.PyAudio()

# Open stream to capture system audio output (adjust input_device_index as needed)
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, )

def get_bpm(audio_buffer, sr=RATE):
    """Detect BPM from an audio buffer."""
    y = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32)  # Convert to float32
    y /= np.max(np.abs(y))  # Normalize
    bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
    return bpm

print("Listening for BPM...")

current_bpm = 200 # Really doesn't matter what number you put here

try:
    while True:
        audio_data = stream.read(CHUNK, exception_on_overflow=False)  # Capture audio chunk
        bpm = get_bpm(audio_data)
        if abs(current_bpm - bpm) > 5:
            print(f"Estimated BPM: {bpm}")
            # GIF BPM is estimated at 200, OBS expects a % relative to 100, hence we divide by 2.00
            result = ws.call(requests.SetInputSettings(inputName=source_name, inputSettings={'speed_percent': int(bpm/2.00+.5)}))
            current_bpm = bpm
            print(result)

except KeyboardInterrupt:
    print("\nStopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()


# Disconnect from OBS
ws.disconnect()