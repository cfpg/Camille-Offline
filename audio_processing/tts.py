import pyttsx4
import multiprocessing
from utils.log import print_log


class TTSWorker:
    def __init__(self, voice_id):
        """
        Initialize the TTSWorker.

        Args:
            voice_id (str): The voice ID for the TTS engine.
        """
        self.voice_id = voice_id
        # Use a context manager for proper process synchronization
        self.ctx = multiprocessing.get_context('spawn')  # Use spawn context for better cross-platform compatibility
        self.queue = self.ctx.Queue()
        self.process = None
        self.state_event = self.ctx.Event()
        self.state_dict = self.ctx.Manager().dict({"speaking": False})
        print_log(f"TTSWorker initialized with voice_id: {voice_id}")

    def tts_worker(self, queue, state_event, state_dict):
        """Worker function to handle TTS in a separate process."""
        print_log("TTS worker process starting")
        try:
            engine = pyttsx4.init()
            engine.setProperty('voice', self.voice_id)
            engine.say("")
            engine.runAndWait()
            print_log("TTS engine initialized successfully")

            while True:
                try:
                    phrase = queue.get()
                    if phrase is None:
                        print_log("Received shutdown signal")
                        break

                    print_log(f"Processing phrase: {phrase}")
                    state_dict["speaking"] = True
                    state_event.set()

                    engine.say(phrase)
                    engine.runAndWait()

                    state_dict["speaking"] = False
                    state_event.set()
                    
                    print_log("TTS processing complete")

                except Exception as e:
                    print_log(f"Error processing TTS phrase: {str(e)}", "red")

        except Exception as e:
            print_log(f"Error in TTS worker process: {str(e)}", "red")
        finally:
            print_log("TTS worker process shutting down")

    def start(self):
        """Start the TTS worker process."""
        print_log("Starting TTS worker process")
        self.process = self.ctx.Process(
            target=self.tts_worker,
            args=(self.queue, self.state_event, self.state_dict)
        )
        self.process.daemon = True  # Make process daemon so it exits when main process exits
        self.process.start()
        print_log(f"TTS worker process started with PID: {self.process.pid}")

    def speak(self, phrase):
        """Add a phrase to the TTS queue and set state in main thread."""
        try:
            print_log(f"Queueing phrase: {phrase}")
            self.queue.put(phrase)
        except Exception as e:
            print_log(f"Error queueing phrase: {str(e)}", "red")

    def silence(self):
        """Silence the TTS worker by clearing the queue and restarting the process."""
        print_log("Silencing TTS Worker.", "orange")
        self.stopForcefully()
        self.start()
    
    def stop(self):
        """Stop the TTS worker process gracefully."""
        if self.process and self.process.is_alive():
            print_log("Stopping TTS worker process")
            try:
                self.queue.put(None)
                self.process.join(timeout=5)  # Wait up to 2 seconds for process to finish

                # Force animation state back to waiting
                self.state_dict["speaking"] = False
                self.state_event.set()

                if self.process.is_alive():
                    self.stopForcefully()
            except Exception as e:
                print_log(f"Error stopping TTS worker: {str(e)}", "red")
        print_log("TTS worker process stopped")
    
    def stopForcefully(self):
        try:
            print_log("TTS worker process didn't terminate gracefully, terminating forcefully", "red")
            self.process.terminate()
            self.process.join()
        except Exception as e:
            print_log(f"Error forcefully stopping TTS worker: {str(e)}", "red")
