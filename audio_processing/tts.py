import pyttsx4
import multiprocessing
from threading import Event


class TTSWorker:
    def __init__(self, voice_id):
        """
        Initialize the TTSWorker.

        Args:
            voice_id (str): The voice ID for the TTS engine.
        """
        self.voice_id = voice_id
        self.queue = multiprocessing.Queue()
        self.process = None
        self.tts_finished_event = Event()
        self.state_event = Event()  # Event to signal state changes
        self.current_state = 0  # Default state

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
            self.current_state = 1  # Set state to listening
            self.state_event.set()  # Signal state change
            engine.say(phrase)
            self.tts_finished_event.set()  # Notify main thread TTS has started
            engine.runAndWait()
            self.tts_finished_event.clear()  # Notify main thread TTS is finished
            print(f"Finished processing TTS.")
            self.current_state = 0  # Set state to waiting
            self.state_event.set()  # Signal state change

    def start(self):
        """Start the TTS worker process."""
        self.process = multiprocessing.Process(
            target=self.tts_worker, args=(self.queue,))
        self.process.start()

    def speak(self, phrase):
        """Add a phrase to the TTS queue and set state in main thread."""
        self.queue.put(phrase)
        if not self.tts_finished_event.is_set():
            # Set animation state to talking immediately
            self.current_state = 2  # Set state to talking
            self.state_event.set()  # Signal state change

    def stop(self):
        """Stop the TTS worker process gracefully."""
        self.queue.put(None)  # Send sentinel to exit the process
        self.process.join()
