import collections
import webrtcvad
import sounddevice as sd

from app.logger import get_logger

logger = get_logger(__name__)


class VADRecorder:
    def __init__(self, device=2, aggressiveness=3):
        self.device = device
        self.sample_rate = 16000
        self.frame_duration_ms = 30
        self.channels = 1
        self.dtype = "int16"
        self.vad = webrtcvad.Vad(aggressiveness)

        # réglages robustes en environnement bruyant
        self.start_buffer_frames = 12   # ~360 ms
        self.end_buffer_frames = 12     # ~360 ms
        self.max_frames_after_trigger = 333  # ~10 secondes max

    def record_phrase(self):
        logger.info("ecoute...")

        frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        bytes_per_frame = frame_size * 2  # int16 mono = 2 octets par sample

        start_buffer = collections.deque(maxlen=self.start_buffer_frames)
        end_buffer = collections.deque(maxlen=self.end_buffer_frames)

        triggered = False
        voiced_frames = []
        triggered_frame_count = 0

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
                    logger.warning("overflow audio détecté")

                if len(frame) != bytes_per_frame:
                    continue

                is_speech = self.vad.is_speech(frame, self.sample_rate)

                if not triggered:
                    start_buffer.append((frame, is_speech))
                    num_voiced = sum(1 for _, speech in start_buffer if speech)

                    # déclenchement plus réactif
                    if (
                        len(start_buffer) == start_buffer.maxlen
                        and num_voiced >= 0.7 * start_buffer.maxlen
                    ):
                        triggered = True
                        logger.info("parole détectée")
                        voiced_frames.extend(f for f, _ in start_buffer)
                        start_buffer.clear()
                        end_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    end_buffer.append((frame, is_speech))
                    triggered_frame_count += 1

                    num_unvoiced = sum(1 for _, speech in end_buffer if not speech)

                    # coupe plus vite
                    if (
                        len(end_buffer) == end_buffer.maxlen
                        and num_unvoiced >= 0.7 * end_buffer.maxlen
                    ):
                        logger.info("fin de phrase")
                        break

                    # sécurité si bruit continu / gens qui parlent autour
                    if triggered_frame_count >= self.max_frames_after_trigger:
                        logger.info("fin forcée (durée max atteinte)")
                        break

        return b"".join(voiced_frames)