import pyaudio
import struct
import pvporcupine
import time
from utils.log import print_log
from utils.colors import colors
from config import Config


class WakeWordDetector:
    def __init__(self, access_key, keyword_paths, tts_worker):
        """
        Initialize the WakeWordDetector.

        Args:
            access_key (str): Picovoice access key.
            keyword_paths (list): Paths to wake word model files.
            tts_worker (TTSWorker): Instance of TTSWorker for text-to-speech functionality.
        """
        self.porcupine = pvporcupine.create(
            access_key=access_key, keyword_paths=keyword_paths)
        self.tts_worker = tts_worker

    def listen_for_wake_phrase(self):
        """
        Listen for the wake phrase and trigger TTS when detected.

        Returns:
            bool: True if the wake phrase is detected, False if interrupted.
        """
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

        print_log(
            f"Listening for wake phrase 'Hey {Config.AI_NAME}'...", "yellow")

        try:
            while True:
                pcm = audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from(
                    "h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)

                if Config.DEBUG:
                    print_log(f"Heard:{colors['reset']} {keyword_index}", "blue")

                if keyword_index >= 0:
                    print_log(f"Wake phrase detected!", "cyan")
                    # Add the TTS request to the queue
                    self.tts_worker.speak(f"Yes {Config.USER_NAME}")
                    return True
        except KeyboardInterrupt:
            print("\nExiting wake phrase listener...")
            return False
        finally:
            audio_stream.close()
            pa.terminate()
