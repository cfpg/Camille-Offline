import pyttsx4
import multiprocessing
import logging


logger = logging.getLogger(__name__)

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
        logger.info(f"TTSWorker initialized with voice_id: {voice_id}")

    def tts_worker(self, queue, state_event, state_dict):
        """Worker function to handle TTS in a separate process."""
        logger.info("TTS worker process starting")
        try:
            engine = pyttsx4.init()
            engine.setProperty('voice', self.voice_id)
            engine.say("")
            engine.runAndWait()
            logger.info("TTS engine initialized successfully")

            while True:
                try:
                    phrase = queue.get()
                    if phrase is None:
                        logger.info("Received shutdown signal")
                        break

                    logger.info(f"Processing phrase: {phrase}")
                    state_dict["speaking"] = True
                    state_event.set()

                    engine.say(phrase)
                    engine.runAndWait()

                    state_dict["speaking"] = False
                    state_event.set()
                    
                    logger.info("TTS processing complete")

                except Exception as e:
                    logger.error(f"Error processing TTS phrase: {str(e)}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in TTS worker process: {str(e)}", exc_info=True)
        finally:
            logger.info("TTS worker process shutting down")

    def start(self):
        """Start the TTS worker process."""
        logger.info("Starting TTS worker process")
        self.process = self.ctx.Process(
            target=self.tts_worker,
            args=(self.queue, self.state_event, self.state_dict)
        )
        self.process.daemon = True  # Make process daemon so it exits when main process exits
        self.process.start()
        logger.info(f"TTS worker process started with PID: {self.process.pid}")

    def speak(self, phrase):
        """Add a phrase to the TTS queue and set state in main thread."""
        try:
            logger.info(f"Queueing phrase: {phrase}")
            self.queue.put(phrase)
        except Exception as e:
            logger.error(f"Error queueing phrase: {str(e)}", exc_info=True)

    def stop(self):
        """Stop the TTS worker process gracefully."""
        if self.process and self.process.is_alive():
            logger.info("Stopping TTS worker process")
            try:
                self.queue.put(None)
                self.process.join(timeout=5)  # Wait up to 5 seconds for process to finish

                # Force animation state back to waiting
                with self.current_state.get_lock():
                    self.current_state.value = 0
                self.state_event.set()

                if self.process.is_alive():
                    logger.warning("TTS worker process didn't terminate gracefully, terminating forcefully")
                    self.process.terminate()
                    self.process.join()
            except Exception as e:
                logger.error(f"Error stopping TTS worker: {str(e)}", exc_info=True)
        logger.info("TTS worker process stopped")
