import time
import threading
import logging
from config import DEBUG, MODEL, AI_NAME, USER_NAME, PICOVOICE_ACCESS_KEY
from audio_processing.recorder import AudioRecorder
from audio_processing.wake_word import WakeWordDetector
from audio_processing.tts import TTSWorker
from nlp.whisper_transcriber import WhisperTranscriber
from nlp.llm_processor import LLMProcessor
from utils.colors import colors
from animation.opengl_animation import OpenGLAnimation

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def voice_chat_loop(opengl_animation):
    logger.info("Starting voice chat loop")

    try:
        # Initialize components inside the thread
        recorder = AudioRecorder()
        tts_worker = TTSWorker("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
        wake_word_detector = WakeWordDetector(PICOVOICE_ACCESS_KEY, ["hey-camille.ppn"], tts_worker)
        whisper_transcriber = WhisperTranscriber()
        llm_processor = LLMProcessor(MODEL, AI_NAME, USER_NAME)
        tts_worker.start()
        logger.info("All voice chat components initialized")

        while opengl_animation.running:
            if wake_word_detector.listen_for_wake_phrase():
                logger.info("Wake word detected")
                opengl_animation.set_state("listening", True)
                audio_file = recorder.record_audio()
                transcribed_text = whisper_transcriber.transcribe(audio_file)
                opengl_animation.set_state("listening", False)

                if not transcribed_text or len(transcribed_text.strip()) < 4:
                    logger.warning("No or too short transcription detected")
                    tts_worker.speak("I didn't hear anything.")
                    continue

                opengl_animation.set_state("thinking", True)
                logger.info(f"Transcribed text: {transcribed_text}")
                response = llm_processor.process_input(transcribed_text)
                opengl_animation.set_state("thinking", False)
                logger.info(f"LLM response: {response}")
                tts_worker.speak(response)
            
            # Check for state changes from TTS worker
            if tts_worker.state_event.is_set():
                logger.info(f"TTSWorker sent a State Event change: {tts_worker.state_dict}")
                opengl_animation.set_state("speaking", tts_worker.state_dict["speaking"])
                tts_worker.state_event.clear()

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error in voice chat loop: {str(e)}", exc_info=True)
    finally:
        if recorder:
             recorder.audio.terminate()
        tts_worker.stop()
        logger.info("Voice chat thread stopped")

def main():
    logger.info("Starting application")
    print(f"{colors['yellow']}Starting up...{colors['reset']}")

    try:
        # Initialize OpenGL animation first
        logger.info("Creating OpenGL Animation instance")
        opengl_animation = OpenGLAnimation()
        logger.info("Starting OpenGL Animation")
        opengl_animation.start()  # Call start() to initialize GLFW and shaders
        
        if not opengl_animation.running:
            logger.error("OpenGL Animation failed to initialize properly")
            return

        voice_chat_thread = threading.Thread(target=voice_chat_loop, args=(
            opengl_animation,))
        voice_chat_thread.daemon = True  # Make thread daemon so it exits with main thread
        voice_chat_thread.start()
        logger.info("Voice chat thread started")

        # Main rendering loop
        while opengl_animation.running:
            if not opengl_animation.render():
                logger.info("OpenGL animation stopped rendering")
                break

            # Limit frame rate (optional, GLFW's swap interval might already handle this)
            time.sleep(1/60)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
    finally:
        logger.info("Cleaning up resources")
        opengl_animation.running = False
        voice_chat_thread.join(timeout=2)
        opengl_animation.stop()
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
