import os
import csv
import multiprocessing
import wave
from piper.voice import PiperVoice, SynthesisConfig
import subprocess

# Configuration
MODEL_PATH = "en_US-amy-medium.onnx"
CONFIG_PATH = "en_US-amy-medium.onnx.json"
TSV_FILE = "words.tsv"

# Global variable to hold the voice instance for each worker process
voice_instance = None

def init_worker(model, config):
    """
    This runs ONCE when each worker process starts.
    It loads the model into the process's local memory.
    """
    global voice_instance
    voice_instance = PiperVoice.load(model, config)

def process_row(row):
    """Runs for every row, using the already-loaded voice_instance."""
    if len(row) < 1:
        return None

    filename_base = row[0].strip()
    # Use the second collumn for the string, if it's present.
    text_content = row[0].strip() + '.' if len(row) < 2 else row[1].strip()
    
    wav_filename = f"snd/{filename_base}.wav"
    mp3_filename = f"snd/{filename_base}.mp3"
    
    print(f"Processing '{text_content}' into {mp3_filename}")
    
    syn_config = SynthesisConfig(
        length_scale=1.2,  # twice as slow
    )
    # sentence_silence=0.2

    try:
        # 1. Generate WAV
        with wave.open(wav_filename, "wb") as wav_file:
            voice_instance.synthesize_wav(text_content, wav_file, syn_config=syn_config)
        
        # 2. Convert to MP3 using a direct ffmpeg system call
        # -y overwrites if exists, -i is input, -acodec libmp3lame uses mp3
        subprocess.run(
            ['ffmpeg', '-y', '-i', wav_filename, '-codec:a', 'libmp3lame', '-q:a', '3', mp3_filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        os.remove(wav_filename)
        return f"Converted: {mp3_filename}"
    except Exception as e:
        return f"Error: {e}"

def main():
    # 1. Prepare data
    with open(TSV_FILE, mode='r', encoding='utf-8') as f:
        rows = list(csv.reader(f, delimiter='\t'))

    num_cores = multiprocessing.cpu_count()
    num_rows = len(rows)
    print(f"Initializing {num_cores} workers to process {num_rows} rows...")

    # 2. Create the Pool with an initializer
    # The 'initargs' are passed to the init_worker function
    with multiprocessing.Pool(
        processes=num_cores, 
        initializer=init_worker, 
        initargs=(MODEL_PATH, CONFIG_PATH)
    ) as pool:
        results = pool.map(process_row, rows)

    print("Batch processing complete.")

if __name__ == "__main__":
    main()