import time
import threading
import logging
from config import Config
from audio_processing.recorder import AudioRecorder
from audio_processing.wake_word import WakeWordDetector
from audio_processing.tts import TTSWorker
from nlp.whisper_transcriber import WhisperTranscriber
from nlp.llm_processor import LLMProcessor
from utils.colors import colors
from utils.log import print_log
from animation.opengl_animation import OpenGLAnimation
from nlp.user_memory_manager import UserMemoryManager
from nlp.api_client import OpenAIClient
from nlp.memory import Memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def voice_chat_loop(opengl_animation):
    logger.info("Starting voice chat loop")
    
    def record_and_transcribe():
        opengl_animation.set_state("listening", True)
        audio_file = recorder.record_audio()
        transcribed_text = whisper_transcriber.transcribe(audio_file)
        opengl_animation.set_state("listening", False)

        if not transcribed_text or len(transcribed_text.strip()) < 3:
            logger.warning("No or too short transcription detected")
            tts_worker.speak("I didn't hear anything.")
            return False

        opengl_animation.set_state("thinking", True)
        logger.info(f"Transcribed text: {transcribed_text}")
        return transcribed_text

    try:
        # Initialize components inside the thread
        recorder = AudioRecorder()
        tts_worker = TTSWorker("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
        wake_word_detector = WakeWordDetector(Config.PICOVOICE_ACCESS_KEY, ["wake_words/hey-camille.ppn", "wake_words/camille-stop.ppn", "wake_words/new-conversation.ppn"], tts_worker)
        whisper_transcriber = WhisperTranscriber()
        api_client = OpenAIClient(
            model=Config.MODEL_NAME,
            api_base=Config.OPENAI_API_BASE,
            api_key=Config.OPENAI_KEY
        )
        memory = Memory(api_client)
        memory_manager = UserMemoryManager(memory.db)
        llm_processor = LLMProcessor(Config.AI_NAME, Config.USER_NAME, api_client, memory, memory_manager)
        tts_worker.start()
        logger.info("All voice chat components initialized")
        opengl_animation.set_state("waiting", True)

        while opengl_animation.running:
            if memory_manager.needs_setup():
                time.sleep(3)
                print_log("Running user memory setup", "cyan")
                tts_worker.speak("Hey! I wil ask you a few questions to get to know you better.")
                time.sleep(5) # sleeping to await tts to finish asking question
                for question in memory_manager.get_setup_questions():
                    print_log(f"Asking: {question.question}", "cyan")
                    tts_worker.speak(f"Please answer the following: {question.question}")
                    time.sleep(2) # sleeping to await tts to finish asking question
                    setup_answer = record_and_transcribe()
                    if setup_answer:
                        print_log(f"User answered: {setup_answer}", "cyan")
                        memory_manager.save_setup_question(question, setup_answer)
                print_log("User memory setup complete", "cyan")
            
            wake_word_result = wake_word_detector.listen_for_wake_phrase()
            if wake_word_result == "start_listening":
                logger.info("Wake word detected")
                transcribed_text = record_and_transcribe()
                
                if not transcribed_text:
                    continue # Skip processing if no transcription
                
                response = llm_processor.process_input(transcribed_text)
                opengl_animation.set_state("thinking", False)
                logger.info(f"LLM response: {response}")
                tts_worker.speak(response)
            elif wake_word_result == "stop_speaking":
                continue
            elif wake_word_result == "new_conversation":
                llm_processor.clear_memory()
                continue
            
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
