import collections
import webrtcvad
import sounddevice as sd


class VADRecorder:
    def __init__(self, device=2, aggressiveness=2):
        self.device = device
        self.sample_rate = 16000
        self.frame_duration_ms = 30
        self.channels = 1
        self.dtype = "int16"
        self.vad = webrtcvad.Vad(aggressiveness)

    def record_phrase(self):
        print("🎤 écoute...")

        frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        bytes_per_frame = frame_size * 2  # int16 mono = 2 octets par sample

        ring_buffer = collections.deque(maxlen=20)
        triggered = False
        voiced_frames = []

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=frame_size,
            device=self.device,
            channels=self.channels,
            dtype=self.dtype,
        ) as stream:
            while True:
                frame, overflowed = stream.read(frame_size)

                if overflowed:
                    print("⚠ overflow audio détecté")

                if len(frame) != bytes_per_frame:
                    continue

                is_speech = self.vad.is_speech(frame, self.sample_rate)

                if not triggered:
                    ring_buffer.append((frame, is_speech))
                    num_voiced = sum(1 for _, speech in ring_buffer if speech)

                    if len(ring_buffer) == ring_buffer.maxlen and num_voiced > 0.8 * ring_buffer.maxlen:
                        triggered = True
                        print("🗣 parole détectée")
                        voiced_frames.extend(f for f, _ in ring_buffer)
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    ring_buffer.append((frame, is_speech))
                    num_unvoiced = sum(1 for _, speech in ring_buffer if not speech)

                    if len(ring_buffer) == ring_buffer.maxlen and num_unvoiced > 0.8 * ring_buffer.maxlen:
                        print("✅ fin de phrase")
                        break

        return b"".join(voiced_frames)