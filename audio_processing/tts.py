import pyttsx4
import multiprocessing

class TTSWorker:
    def __init__(self, voice_id):
        self.voice_id = voice_id
        self.queue = multiprocessing.Queue()
        self.process = None

    def tts_worker(self, queue):
        """Worker function to handle TTS in a separate process."""
        engine = pyttsx4.init()
        engine.setProperty('voice', self.voice_id)

        # Pre-initialize the engine by speaking an empty string
        engine.say("")
        engine.runAndWait()

        while True:
            phrase = queue.get()
            if phrase is None:  # Sentinel value to exit the process
                break

            print(f"Queuing phrase: {phrase}")
            engine.say(phrase)
            engine.runAndWait()
            print(f"Finished processing TTS.")

    def start(self):
        self.process = multiprocessing.Process(target=self.tts_worker, args=(self.queue,))
        self.process.start()

    def speak(self, phrase):
        self.queue.put(phrase)

    def stop(self):
        self.queue.put(None)
        self.process.join()