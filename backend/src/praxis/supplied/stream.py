"""Bounded microphone windows: 4 seconds of context, 2 seconds of new audio."""
import numpy as np


class MicrophoneWindows:
    def __init__(self, vad):
        self.vad = vad
        self.previous = None
        self.previous_speech = False
        self.started = False
        self.last_sequence = None
        self.remainder = np.empty(0, dtype=np.float32)

    def push(self, sequence, audio):
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if len(audio) != 32000 or not np.isfinite(audio).all():
            raise ValueError("Expected a two-second mono 16kHz block")
        if self.last_sequence is not None and sequence != self.last_sequence + 1:
            self.previous = None
            self.previous_speech = False
            self.started = False
            self.remainder = np.empty(0, dtype=np.float32)
            self.vad.model.reset_states()
        self.last_sequence = sequence
        frames = np.concatenate((self.remainder, audio))
        speech = False
        end = len(frames) // 512 * 512
        for offset in range(0, end, 512):
            speech = self.vad.speech(frames[offset:offset + 512]) or speech
        self.remainder = frames[end:].copy()
        previous = self.previous
        previous_speech = self.previous_speech
        self.previous = audio.copy()
        self.previous_speech = speech
        if previous is None or not (speech or (previous_speech and not self.started)):
            return None
        # Only the new half is transcribed; the acoustic branch receives full context.
        window = np.concatenate((previous, audio))
        new_speech = audio if self.started else window
        self.started = True
        return window, new_speech
