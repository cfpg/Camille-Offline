import time
from config import DEBUG, MODEL, AI_NAME, USER_NAME, PICOVOICE_ACCESS_KEY
from audio_processing.recorder import AudioRecorder
from audio_processing.wake_word import WakeWordDetector
from audio_processing.tts import TTSWorker
from nlp.whisper_transcriber import WhisperTranscriber
from nlp.llm_processor import LLMProcessor
from utils.colors import colors
from animation.opengl_animation import OpenGLAnimation


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

    # Start TTS worker and OpenGL animation
    tts_worker.start()
    opengl_animation.start()

    try:
        # Main loop
        while True:
            # Update OpenGL animation
            if not opengl_animation.render():
                break

            # Check for wake phrase
            if wake_word_detector.check_for_wake_phrase():
                opengl_animation.set_state(1)  # Listening state
                audio_file = recorder.record_audio()
                transcribed_text = whisper_transcriber.transcribe(audio_file)

                if not transcribed_text or len(transcribed_text.strip()) < 4:
                    tts_worker.speak("I didn't hear anything.")
                    continue

                response = llm_processor.process_input(transcribed_text)
                opengl_animation.set_state(2)  # Talking state
                tts_worker.speak(response)

            # Sleep briefly to avoid busy-waiting
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Stop the TTS worker and OpenGL animation gracefully
        tts_worker.stop()
        opengl_animation.stop()

        # Clean up audio resources
        recorder.audio.terminate()


if __name__ == "__main__":
    main()
