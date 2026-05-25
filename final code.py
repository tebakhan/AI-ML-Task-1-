import time
import audioop
import pyaudio

# --- CONFIGURATION (CHUNKS & THRESHOLDS) ---
FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
CHANNELS = 1  # Mono audio
RATE = 16000  # Sample rate (16kHz standard for STT)
CHUNK = 1024  # Buffer size

# Silence Detection Settings
SILENCE_THRESHOLD = (
    500  # less energy means silence (adjust if room is noisy)
)
THINKING_PAUSE_LIMIT = 2.0  # 2 seconds pause = User is thinking
ABANDONMENT_LIMIT = 5.0  # 5 seconds silence = Call/Speech Abandoned

# --- MAIN DETECTION MODULE ---
def start_speech_timeout_detector():
    p = pyaudio.PyAudio()

    # Open microphone stream
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print(">>> Listening started... start speaking ")

    silence_start_time = None
    speech_detected = False
    thinking_triggered = False

    try:
        while True:
            # Read audio data from mic
            data = stream.read(CHUNK, exception_on_overflow=False)

            # Calculate RMS (Root Mean Square) which represents volume/energy
            rms = audioop.rms(data, 2)

            # Check if current chunk is silence or speech
            if rms < SILENCE_THRESHOLD:
                # if no silenec track previously, then start the timer
                if silence_start_time is None:
                    silence_start_time = time.time()
                else:
                    silence_duration = time.time() - silence_start_time

                    # Case 1: Thinking Pause Detect (betwwen 2-5 seconds
                    if (
                        silence_duration >= THINKING_PAUSE_LIMIT
                        and not thinking_triggered
                    ):
                        print(
                            f"[STATUS] User is thinking... (Paused for {THINKING_PAUSE_LIMIT}s)"
                        )
                        thinking_triggered = True

                    # Case 2: Complete Abandonment / Timeout (Greater than 5 seconds)
                    if silence_duration >= ABANDONMENT_LIMIT:
                        print(
                            f"\n[TIMEOUT] Speech Abandoned! No response for {ABANDONMENT_LIMIT} seconds."
                        )
                        print(">>> Closing STT Pipeline Session.")
                        break
            else:
                # As if user said something (Speech detected)
                if not speech_detected:
                    print("[STATUS] Speech Detected!")
                    speech_detected = True

                # Reset all timers and flags because user spoke
                silence_start_time = None
                if thinking_triggered:
                    print("[STATUS] User resumed speaking after a pause.")
                    thinking_triggered = False

    except KeyboardInterrupt:
        print("\nStopping detector manually...")

    finally:
        # Stream aur PyAudio clean up is neccessary 
        stream.stop_stream()
        stream.close()
        p.terminate()
        print(">>> Pipeline closed successfully.")


if __name__ == "__main__":
    start_speech_timeout_detector()