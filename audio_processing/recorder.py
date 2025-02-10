import wave
import logging
import numpy as np
import pyaudio
from utils.colors import colors
from utils.log import print_log


logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, format=pyaudio.paInt16, channels=1, rate=8000, chunk=1024):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()

    def bytes_to_float_array(self, a_bytes):
        # Convert bytes to int (assuming 2 bytes per sample)
        a_int = np.frombuffer(a_bytes, dtype=np.int16)
        # Normalize to float between -1 and 1
        return a_int.astype(np.float32) / 32768.0

    def calibrate_noise_floor(self, stream, calibration_duration=1):
        print_log(f"Calibrating noise floor...", "yellow")
        frames = []
        for _ in range(int(self.rate / self.chunk * calibration_duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        # Convert frames to float array
        audio_data = self.bytes_to_float_array(b''.join(frames))

        # Calculate the RMS of the noise floor
        noise_floor_rms = np.sqrt(np.mean(audio_data ** 2))
        print_log(f"Noise floor RMS: {colors['reset']}{noise_floor_rms}", "yellow")

        # Set the silence threshold slightly above the noise floor
        silence_threshold = noise_floor_rms * 1.5  # Adjust the multiplier as needed
        print_log(f"Silence threshold set to: {colors['reset']}{silence_threshold}", "yellow")
        return silence_threshold

    def record_audio(self, max_silent_chunks=15):
        stream = self.audio.open(format=self.format, channels=self.channels,
                               rate=self.rate, input=True, frames_per_buffer=self.chunk)
        
        silence_threshold = self.calibrate_noise_floor(stream)
        frames = []
        silent_chunk_count = 0

        print_log("Starting audio recording")
        try:
            while True:
                data = stream.read(self.chunk, exception_on_overflow=False)
                if not data:
                    break

                audio_data = self.bytes_to_float_array(data)
                rms = np.sqrt(np.mean(audio_data ** 2))

                if rms < silence_threshold:
                    silent_chunk_count += 1
                    if silent_chunk_count > max_silent_chunks:
                        print_log("Silence detected, stopping recording")
                        break
                else:
                    silent_chunk_count = 0

                frames.append(data)

        finally:
            print_log("Stopping audio recording")
            stream.stop_stream()
            stream.close()

        # Save audio file
        wf = wave.open("temp_audio.wav", 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return "temp_audio.wav"
