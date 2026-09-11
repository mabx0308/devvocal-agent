import asyncio
import os
import subprocess
import time
import pyttsx3
from dotenv import load_dotenv
from google import genai
import sounddevice as sd
from speechmatics.rt import (
    AsyncClient,
    AudioEncoding,
    AudioFormat,
    ServerMessageType,
    TranscriptResult,
    TranscriptionConfig,
)

# Load secret API keys from .env file
load_dotenv()

SPEECHMATICS_KEY = os.getenv("SPEECHMATICS_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_KEY)

# Text-To-Speech engine setup
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 180)

is_speaking = False

def speak(text: str):
    """Speaks through speakers while locking the mic to prevent self-listening."""
    global is_speaking
    is_speaking = True
    print(f"\n[DEVVOCAL]: {text}\n")
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error]: {e}")
    finally:
        time.sleep(0.4)  # Wait for room acoustics to settle
        is_speaking = False

SAMPLE_RATE = 16000
CHUNK_SIZE = 2048

audio_format = AudioFormat(
    encoding=AudioEncoding.PCM_S16LE,
    sample_rate=SAMPLE_RATE,
    chunk_size=CHUNK_SIZE
)

def query_gemini_with_fallback(prompt: str) -> str:
    """Tries the primary model and falls back if servers are busy."""
    candidate_models = ["gemini-2.5-flash", "gemini-3.6-flash"]
    last_err = None
    for model_name in candidate_models:
        try:
            chat = ai_client.chats.create(model=model_name)
            response = chat.send_message(prompt)
            return response.text.strip()
        except Exception as e:
            last_err = e
            print(f"[Model {model_name} busy, trying alternate...]")
            time.sleep(0.5)
    raise last_err

def execute_action(command_intent: str):
    """Processes the full finalized sentence."""
    print(f"\n[Agent Processing Full Prompt]: '{command_intent}'")
    
    prompt = f"""
    You are an intelligent voice desktop assistant named DevVocal.
    The user spoke this complete command: "{command_intent}"

    Rules:
    1. If the user wants to list files or inspect directory contents: reply strictly "EXEC:dir"
    2. If the user wants to check git status: reply strictly "EXEC:git status"
    3. If the user wants to open VS Code: reply strictly "EXEC:code ."
    4. Otherwise, answer concisely in 1 to 2 clear spoken sentences suitable for speech.
    """
    try:
        result = query_gemini_with_fallback(prompt)

        if result.startswith("EXEC:"):
            cmd = result.replace("EXEC:", "").strip()
            print(f"[SYSTEM EXECUTING]: {cmd}")
            speak("Executing command on your system.")
            try:
                output = subprocess.check_output(cmd, shell=True, text=True)
                print(f"[TERMINAL OUTPUT]:\n{output[:350]}")
            except Exception as cmd_err:
                print(f"[Command Error]: {cmd_err}")
        else:
            speak(result)
    except Exception as e:
        print(f"[LLM Error]: {e}")

# Buffer to accumulate words into complete thoughts
text_buffer = []
debounce_task = None

async def process_accumulated_text():
    """Waits for 1.5 seconds of silence before firing the LLM."""
    await asyncio.sleep(1.5)
    global text_buffer
    if text_buffer:
        full_sentence = " ".join(text_buffer).strip()
        text_buffer = []
        if len(full_sentence) > 3 and any(c.isalnum() for c in full_sentence):
            print(f"\n[Final Sentence Captured]: \"{full_sentence}\"")
            execute_action(full_sentence)

async def main():
    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    def mic_callback(indata, frames, time_info, status):
        # Drop mic audio while the assistant is speaking
        if not is_speaking:
            loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

    print("\n=======================================================")
    print(" 🎙️  DevVocal Assistant is Active! Speak into your mic...")
    print("=======================================================\n")

    async with AsyncClient(api_key=SPEECHMATICS_KEY) as client:
        @client.on(ServerMessageType.ADD_TRANSCRIPT)
        def handle_finals(msg):
            global debounce_task
            if is_speaking:
                return

            transcript_result = TranscriptResult.from_message(msg)
            if transcript_result.metadata and transcript_result.metadata.transcript:
                chunk = transcript_result.metadata.transcript.strip()
                if chunk and chunk != ".":
                    text_buffer.append(chunk)
                    print(f"[Hearing]: {chunk}")

                    # Reset silence debounce timer
                    if debounce_task and not debounce_task.done():
                        debounce_task.cancel()
                    debounce_task = asyncio.create_task(process_accumulated_text())

        config = TranscriptionConfig(
            language="en",
            enable_partials=False,
            max_delay=1.0
        )

        await client.start_session(transcription_config=config, audio_format=audio_format)

        stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            channels=1,
            dtype="int16",
            callback=mic_callback
        )

        with stream:
            try:
                while True:
                    data = await audio_queue.get()
                    await client.send_audio(data)
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\nAssistant stopped cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass