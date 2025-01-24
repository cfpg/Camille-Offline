import wave
import numpy as np
import pyaudio
from utils.colors import colors
from config import DEBUG


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
        print(f"{colors['yellow']}Calibrating noise floor...{colors['reset']}")
        frames = []
        for _ in range(int(self.rate / self.chunk * calibration_duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        # Convert frames to float array
        audio_data = self.bytes_to_float_array(b''.join(frames))

        # Calculate the RMS of the noise floor
        noise_floor_rms = np.sqrt(np.mean(audio_data ** 2))
        print(
            f"{colors['yellow']}Noise floor RMS: {noise_floor_rms}{colors['reset']}")

        # Set the silence threshold slightly above the noise floor
        silence_threshold = noise_floor_rms * 1.5  # Adjust the multiplier as needed
        print(
            f"{colors['yellow']}Silence threshold set to: {silence_threshold}{colors['reset']}")
        return silence_threshold

    def record_audio(self, silence_threshold, max_silent_chunks=15):
        stream = self.audio.open(format=self.format, channels=self.channels,
                            rate=self.rate, input=True, frames_per_buffer=self.chunk)

        # Calibrate noise floor and set silence threshold
        silence_threshold = self.calibrate_noise_floor(stream)

        print(f"{colors['green']}Listening for command...{colors['reset']}")
        frames = []

        # Set thresholds and silence detection parameters
        max_silent_chunks = 15  # Adjust based on your needs
        silent_chunk_count = 0

        while True:
            data = stream.read(self.chunk)
            if not data:
                break

            # Convert data to float representation for analysis
            audio_data = self.bytes_to_float_array(data)

            # Calculate the RMS (Root Mean Square) as a measure of loudness
            rms = np.sqrt(np.mean(audio_data ** 2))

            if DEBUG:
                print(
                    f"{colors['cyan']}Raw audio max: {np.max(audio_data)}; min: {np.min(audio_data)}; RMS: {rms}{colors['reset']}")
                print(
                    f"{colors['cyan']}silent chunks: {silent_chunk_count}; RMS: {rms}{colors['reset']}")

            # If the RMS is below a certain threshold, consider it silent
            if rms < silence_threshold:  # Adjust this threshold based on your environment and testing
                silent_chunk_count += 1
                if silent_chunk_count > max_silent_chunks:
                    print(
                        f"{colors['red']}Detecting silence... Stopping recording.{colors['reset']}")
                    break
            else:
                if DEBUG:
                    print(
                        f"{colors['cyan']}Someone is speaking...{colors['reset']}")

                silent_chunk_count = 0

            frames.append(data)

        print(f"{colors['red']}Stopping recording.{colors['reset']}")
        stream.stop_stream()
        stream.close()

        wf = wave.open("temp_audio.wav", 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return "temp_audio.wav"
