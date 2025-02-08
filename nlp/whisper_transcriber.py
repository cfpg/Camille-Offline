import whisper
import functools


class WhisperTranscriber:
    def __init__(self, model_name="tiny"):
        whisper.torch.load = functools.partial(whisper.torch.load, weights_only=True)
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_file):
        result = self.model.transcribe(audio_file, language="en")
        return result["text"].strip()
