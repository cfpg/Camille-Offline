import time
from config import DEBUG, MODEL, AI_NAME, USER_NAME, PICOVOICE_ACCESS_KEY, MEMCACHED_HOST, MEMCACHED_KEY
from audio_processing.recorder import AudioRecorder
from audio_processing.wake_word import WakeWordDetector
from audio_processing.tts import TTSWorker
from nlp.whisper_transcriber import WhisperTranscriber
from nlp.llm_processor import LLMProcessor
from utils.colors import colors
from pymemcache.client import base


def initialize_memcached():
    """Initialize and return a Memcached client."""
    host, port = MEMCACHED_HOST.split(':')
    return base.Client((host, int(port)))


def main():
    print(f"{colors['yellow']}Starting up...{colors['reset']}")

    # Initialize components
    recorder = AudioRecorder()
    tts_worker = TTSWorker(
        "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
    wake_word_detector = WakeWordDetector(
        PICOVOICE_ACCESS_KEY, ["hey-camille.ppn"], tts_worker)
    whisper_transcriber = WhisperTranscriber()
    memcached_client = initialize_memcached()
    llm_processor = LLMProcessor(
        MODEL, memcached_client, MEMCACHED_KEY, AI_NAME, USER_NAME)

    # Start TTS worker
    tts_worker.start()

    try:
        while True:
            if wake_word_detector.listen_for_wake_phrase():
                silence_threshold = recorder.calibrate_noise_floor(recorder.audio.open(
                    format=recorder.format, channels=recorder.channels, rate=recorder.rate, input=True, frames_per_buffer=recorder.chunk))
                audio_file = recorder.record_audio(silence_threshold)
                transcribed_text = whisper_transcriber.transcribe(audio_file)
                response = llm_processor.process_input(transcribed_text)
                tts_worker.speak(response)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Stop the TTS worker gracefully
        tts_worker.stop()

        # Clean up audio resources
        recorder.audio.terminate()

        # Clear the conversation in Memcached
        memcached_client.delete(MEMCACHED_KEY)


if __name__ == "__main__":
    main()
