import pyaudio
import struct
import pvporcupine
import time
from utils.log import print_log
from utils.colors import colors
from config import Config
import multiprocessing


class WakeWordDetector:
    def __init__(self, access_key, keyword_paths):
        """
        Initialize the WakeWordDetector.

        Args:
            access_key (str): Picovoice access key.
            keyword_paths (list): Paths to wake word model files.
        """
        self.access_key = access_key
        self.keyword_paths = keyword_paths
        self.ctx = multiprocessing.get_context('spawn')
        self.wake_event = self.ctx.Event()
        self.wake_dict = self.ctx.Manager().dict({"action": None})
        self.process = None
        self.running = False

    def wake_word_worker(self, wake_event, wake_dict):
        porcupine = pvporcupine.create(access_key=self.access_key, keyword_paths=self.keyword_paths)
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print_log(f"Listening for wake phrase 'Hey {Config.AI_NAME}'...", "yellow")

        try:
            while self.running:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(pcm)

                if keyword_index >= 0:
                    wake_dict["action"] = "start_listening" if keyword_index == 0 else \
                                        "stop_speaking" if keyword_index == 1 else \
                                        "new_conversation"
                    wake_event.set()
                    print_log(f"Wake word detected: {wake_dict['action']}", "green")

        finally:
            audio_stream.close()
            pa.terminate()
            porcupine.delete()

    def start(self):
        self.running = True
        self.process = self.ctx.Process(
            target=self.wake_word_worker,
            args=(self.wake_event, self.wake_dict)
        )
        self.process.daemon = True
        self.process.start()

    def stop(self):
        self.running = False
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join()
