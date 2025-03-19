import time
import threading
import logging
import json
from config import Config
from audio_processing.recorder import AudioRecorder
from audio_processing.wake_word import WakeWordDetector
from audio_processing.tts import TTSWorker
from nlp.whisper_transcriber import WhisperTranscriber
from nlp.llm_processor import LLMProcessor
from utils.colors import colors
from utils.log import print_log
from animation.video_animation import VideoAnimation
from nlp.user_memory_manager import UserMemoryManager
from nlp.api_client import OpenAIClient
from nlp.memory import Memory
from tools.task_manager_tool import TaskManager
from datetime import datetime, timedelta

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

def voice_chat_loop(animation):
    logger.info("Starting voice chat loop")
    
    # Add these variables at the start of the function
    last_reminder_check = 0
    reminded_task_ids = set()
    REMINDER_CHECK_INTERVAL = 60  # Check every minute
    aiAskedAQuestion = False  # Add flag to track if the AI expects the user to answer a question

    def record_and_transcribe():
        animation.set_state("listening", True)
        audio_file = recorder.record_audio()
        transcribed_text = whisper_transcriber.transcribe(audio_file)
        animation.set_state("listening", False)

        if not transcribed_text or len(transcribed_text.strip()) < 3:
            logger.warning("No or too short transcription detected")
            tts_worker.speak("I didn't hear anything.")
            return False

        animation.set_state("thinking", True)
        logger.info(f"Transcribed text: {transcribed_text}")
        return transcribed_text

    try:
        # Initialize components inside the thread
        recorder = AudioRecorder()
        tts_worker = TTSWorker("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
        wake_word_detector = WakeWordDetector(Config.PICOVOICE_ACCESS_KEY, 
            ["wake_words/hey-camille.ppn", "wake_words/camille-stop.ppn", "wake_words/new-conversation.ppn"])
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
        time.sleep(3) # Await TTS Worker startup
        logger.info("All voice chat components initialized")
        animation.set_state("waiting", True)

        wake_word_detector.start()  # Start the wake word detection process

        # Add task_manager initialization
        task_manager = TaskManager()

        while animation.running:
            current_time = time.time()
            
            if current_time - last_reminder_check >= REMINDER_CHECK_INTERVAL:
                logger.info("Checking for upcoming reminders...")
                last_reminder_check = current_time
                
                # Update to filter tasks only for today
                upcoming_tasks = task_manager.get_upcoming_tasks(15)
                
                if upcoming_tasks:
                    logger.info(f"Found {len(upcoming_tasks)} upcoming tasks for today")
                    # Filter out tasks we've already reminded about
                    new_tasks = [task for task in upcoming_tasks if task['id'] not in reminded_task_ids]
                    
                    if new_tasks:
                        logger.info(f"Sending reminder for {len(new_tasks)} new tasks")
                        # Add new task IDs to reminded set
                        reminded_task_ids.update(task['id'] for task in new_tasks)
                        
                        # Construct reminder message
                        if len(new_tasks) == 1:
                            message = f"Hey {Config.USER_NAME}, you have to {new_tasks[0]['description']} in 15 minutes."
                        else:
                            task_descriptions = [task['description'] for task in new_tasks]
                            tasks_text = ", and ".join(", ".join(task_descriptions).rsplit(", ", 1))
                            message = f"Hey {Config.USER_NAME}, you have to {tasks_text} in 15 minutes."
                        
                        logger.info(f"Speaking reminder: {message}")
                        # Speak the reminder
                        tts_worker.speak(message)
                else:
                    logger.debug("No upcoming tasks found")

            if memory_manager.needs_setup():
                print_log("Running user memory setup", "cyan")
                tts_worker.speak("Hey! I wil ask you a few questions to get to know you better.")
                time.sleep(5) # sleeping to await tts to finish asking question
                for question in memory_manager.get_setup_questions():
                    print_log(f"Asking: {question.question}", "cyan")
                    tts_worker.speak(f"Answer the following: {question.question}")
                    time.sleep(2) # sleeping to await tts to finish asking question
                    setup_answer = record_and_transcribe()
                    if setup_answer:
                        print_log(f"User answered: {setup_answer}", "cyan")
                        memory_manager.save_setup_question(question, setup_answer)
                
                # Update system prompt with new user memories
                llm_processor._initialize_system_prompt()
                print_log("User memory setup complete", "cyan")
            
            # Check for wake word events
            if wake_word_detector.wake_event.is_set():
                action = wake_word_detector.wake_dict["action"]
                logger.info(f"Wake word detected with action: {action}")
                
                if action == "start_listening":
                    if not aiAskedAQuestion == True:
                        tts_worker.speak(f"Yes {Config.USER_NAME}")
                    elif aiAskedAQuestion == True:
                        aiAskedAQuestion = False  # Reset flag since we're handling it now

                    transcribed_text = record_and_transcribe()
                    if transcribed_text:
                        response, continue_conversation = llm_processor.process_input(transcribed_text)
                        animation.set_state("thinking", False)
                        logger.info(f"LLM response: {response}")
                        tts_worker.speak(response)
                            
                        # If the AI wants to continue the conversation, wait for TTS to finish then set wake event
                        if continue_conversation:
                            logger.info("AI wants to continue conversation, will wait for TTS to finish")
                            aiAskedAQuestion = True
                elif action == "stop_speaking":
                    tts_worker.silence()
                    tts_worker.speak(f"Okay {Config.USER_NAME}")
                elif action == "new_conversation":
                    tts_worker.speak(f"Starting a new conversation {Config.USER_NAME}")
                    llm_processor.clear_memory()
                
                wake_word_detector.wake_event.clear()
                print(f"Clearing wake word event")

            # Check for TTS state changes
            if tts_worker.state_event.is_set():
                logger.info(f"TTSWorker sent a State Event change: {tts_worker.state_dict}")
                animation.set_state("speaking", tts_worker.state_dict["speaking"])
                tts_worker.state_event.clear()
                logger.info(f"Clearing TTSWorker state event")

            # If we're continuing conversation and TTS just finished speaking, trigger next recording
            if aiAskedAQuestion and not tts_worker.state_dict["speaking"]:
                logger.info("TTS finished speaking and conversation should continue, setting wake event")
                wake_word_detector.wake_dict["action"] = "start_listening"
                wake_word_detector.wake_event.set()

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error in voice chat loop: {str(e)}", exc_info=True)
    finally:
        if recorder:
             recorder.audio.terminate()
        tts_worker.stop()
        wake_word_detector.stop()
        logger.info("Voice chat thread stopped")

def main():
    logger.info("Starting application")
    print(f"{colors['yellow']}Starting up...{colors['reset']}")

    try:
        # Initialize Video animation with all state videos
        video_paths = {
            "waiting": "./videos/camille-waiting.mp4",
            "listening": "./videos/camille-waiting.mp4",
            "speaking": "./videos/camille-talking.mp4",
            "thinking": "./videos/camille-thinking.mp4"
        }
        logger.info("Creating Video Animation instance")
        animation = VideoAnimation(video_paths)
        animation.start()
        
        if not animation.running:
            logger.error("Video Animation failed to initialize properly")
            return

        voice_chat_thread = threading.Thread(target=voice_chat_loop, args=(animation,))
        voice_chat_thread.daemon = True
        voice_chat_thread.start()
        logger.info("Voice chat thread started")

        # Main loop - update animation in main thread
        while animation.running:
            if not animation.update():  # Call update in main thread
                break
            time.sleep(0.001)  # Small sleep to prevent CPU overload

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
    finally:
        logger.info("Cleaning up resources")
        animation.running = False
        voice_chat_thread.join(timeout=2)
        animation.stop()
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
