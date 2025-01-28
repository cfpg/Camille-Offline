import time
import threading
from config import DEBUG, MODEL, AI_NAME, USER_NAME, PICOVOICE_ACCESS_KEY
from audio_processing.recorder import AudioRecorder
from audio_processing.wake_word import WakeWordDetector
from audio_processing.tts import TTSWorker
from nlp.whisper_transcriber import WhisperTranscriber
from nlp.llm_processor import LLMProcessor
from utils.colors import colors
from animation.opengl_animation import OpenGLAnimation


def voice_chat_loop(opengl_animation, recorder, wake_word_detector, whisper_transcriber, tts_worker, llm_processor):
    while opengl_animation.running:
        if wake_word_detector.listen_for_wake_phrase():
            opengl_animation.set_state(1)  # Set state to listening
            audio_file = recorder.record_audio()
            transcribed_text = whisper_transcriber.transcribe(audio_file)

            if not transcribed_text or len(transcribed_text.strip()) < 4:
                tts_worker.speak("I didn't hear anything.")
                opengl_animation.set_state(0)  # Set state to waiting
                continue

            response = llm_processor.process_input(transcribed_text)
            tts_worker.speak(response)

        time.sleep(0.1) # Reduce CPU usage in the thread
        
def main():
    print(f"{colors['yellow']}Starting up...{colors['reset']}")

    # Initialize components
    recorder = AudioRecorder()
    tts_worker = TTSWorker(
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
    wake_word_detector = WakeWordDetector(
        PICOVOICE_ACCESS_KEY, ["hey-camille.ppn"], tts_worker)
    whisper_transcriber = WhisperTranscriber()
    llm_processor = LLMProcessor(MODEL, AI_NAME, USER_NAME)
    opengl_animation = OpenGLAnimation()

    # Start TTS worker
    tts_worker.start()
    opengl_animation.start()

    voice_chat_thread = threading.Thread(target=voice_chat_loop, args=(
        opengl_animation, recorder, wake_word_detector, whisper_transcriber, tts_worker, llm_processor))
    voice_chat_thread.daemon = True  # Allow main thread to exit without waiting for this thread
    voice_chat_thread.start()

    try:
        while True:
            if not opengl_animation.render():
                break
            time.sleep(1/60)  # Limit frame rate to 60 FPS and reduce CPU usage
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        opengl_animation.running = False  # Signal thread to stop
        voice_chat_thread.join(timeout=2)  # Give thread a moment to stop
        tts_worker.stop()
        opengl_animation.stop()
        recorder.audio.terminate()


if __name__ == "__main__":
    main()
