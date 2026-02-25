import os
import csv
import multiprocessing
import wave
import subprocess
import argparse

# Configuration for Piper
PIPER_MODEL = "en_US-amy-medium.onnx"
PIPER_CONFIG = "en_US-amy-medium.onnx.json"

# Configuration for Kitten
KITTEN_MODEL = "KittenML/kitten-tts-mini-0.8"

TSV_FILE = "words.tsv"

# Global variables to hold the voice instance and engine type for each worker process
voice_instance = None
current_engine = None

def init_worker(engine, model, config):
    """
    This runs ONCE when each worker process starts.
    It loads the appropriate model into the process's local memory.
    """
    global voice_instance, current_engine
    current_engine = engine
    
    try:
        if engine == "piper":
            from piper.voice import PiperVoice
            voice_instance = PiperVoice.load(model, config)
        elif engine == "kitten":
            from kittentts import KittenTTS
            voice_instance = KittenTTS(model)
    except ImportError as e:
        print(f"Error: Required library for engine '{engine}' is not installed. {e}")
        raise

def process_row(row):
    """Runs for every row, using the already-loaded voice_instance."""
    if len(row) < 1:
        return None

    filename_base = row[0].strip()
    # Use the second column for the string, if it's present.
    text_content = row[0].strip() + '.' if len(row) < 2 else row[1].strip()
    
    wav_filename = f"snd/{filename_base}.wav"
    mp3_filename = f"snd/{filename_base}.mp3"
    
    print(f"[{current_engine}] Processing '{text_content}' into {mp3_filename}")
    
    try:
        if current_engine == "piper":
            from piper.voice import SynthesisConfig
            syn_config = SynthesisConfig(
                length_scale=1.2,  # twice as slow
            )
            with wave.open(wav_filename, "wb") as wav_file:
                voice_instance.synthesize_wav(text_content, wav_file, syn_config=syn_config)
        
        elif current_engine == "kitten":
            import soundfile as sf
            # Generate audio (usually returns a numpy array)
            audio = voice_instance.generate(text_content, voice='Jasper')
            # KittenTTS typically uses a 24000Hz sample rate
            sf.write(wav_filename, audio, 24000)

        # 2. Convert to MP3 using ffmpeg
        subprocess.run(
            ['ffmpeg', '-y', '-i', wav_filename, '-codec:a', 'libmp3lame', '-q:a', '3', mp3_filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        if os.path.exists(wav_filename):
            os.remove(wav_filename)
        return f"Converted: {mp3_filename}"
    except Exception as e:
        if os.path.exists(wav_filename):
            os.remove(wav_filename)
        return f"Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="Generate MP3s for word game using Piper or Kitten TTS.")
    parser.add_argument("--engine", choices=["piper", "kitten"], default="piper", 
                        help="TTS engine to use (default: piper)")
    parser.add_argument("--model", type=str, help="Path to the model file or name")
    parser.add_argument("--config", type=str, help="Path to the config file (Piper only)")
    
    args = parser.parse_args()

    # Determine model and config paths
    if args.engine == "piper":
        model = args.model if args.model else PIPER_MODEL
        config = args.config if args.config else PIPER_CONFIG
    else:
        model = args.model if args.model else KITTEN_MODEL
        config = None

    # 1. Prepare data
    if not os.path.exists("snd"):
        os.makedirs("snd")

    with open(TSV_FILE, mode='r', encoding='utf-8') as f:
        rows = list(csv.reader(f, delimiter='\t'))

    num_cores = multiprocessing.cpu_count()
    num_rows = len(rows)
    print(f"Initializing {num_cores} workers for engine '{args.engine}' to process {num_rows} rows...")

    # 2. Create the Pool with an initializer
    with multiprocessing.Pool(
        processes=num_cores, 
        initializer=init_worker, 
        initargs=(args.engine, model, config)
    ) as pool:
        results = pool.map(process_row, rows)

    print("Batch processing complete.")

if __name__ == "__main__":
    main()
