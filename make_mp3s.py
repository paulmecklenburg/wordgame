import os
import csv
import multiprocessing
import wave
import subprocess
import argparse
import torch

# Configuration
PIPER_MODEL_PATH = "en_US-amy-medium.onnx"
PIPER_CONFIG_PATH = "en_US-amy-medium.onnx.json"
QWEN_MODEL_NAME = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
TSV_FILE = "words.tsv"
SND_DIR = "snd"

# Ensure output directory exists
os.makedirs(SND_DIR, exist_ok=True)

# Global variable for Piper
voice_instance = None

def convert_to_mp3(wav_filename, mp3_filename):
    """Utility to convert WAV to MP3 using ffmpeg."""
    subprocess.run(
        ['ffmpeg', '-y', '-nostdin', '-i', wav_filename, '-codec:a', 'libmp3lame', '-q:a', '3', mp3_filename],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if os.path.exists(wav_filename):
        os.remove(wav_filename)

def init_piper_worker(model, config):
    from piper.voice import PiperVoice
    global voice_instance
    voice_instance = PiperVoice.load(model, config)

def process_row_piper(row):
    from piper.voice import SynthesisConfig
    if len(row) < 1:
        return None

    filename_base = row[0].strip()
    text_content = row[0].strip() + '.' if len(row) < 2 else row[1].strip()
    
    wav_filename = os.path.join(SND_DIR, f"{filename_base}.wav")
    mp3_filename = os.path.join(SND_DIR, f"{filename_base}.mp3")
    
    print(f"Processing '{text_content}' into {mp3_filename}")
    
    syn_config = SynthesisConfig(
        length_scale=1.2,
    )

    try:
        with wave.open(wav_filename, "wb") as wav_file:
            voice_instance.synthesize_wav(text_content, wav_file, syn_config=syn_config)
        
        convert_to_mp3(wav_filename, mp3_filename)
        return f"Converted: {mp3_filename}"
    except Exception as e:
        return f"Error: {e}"

def main():
    # Use 'spawn' for multiprocessing to avoid issues with library state (like ONNX) and the TTY
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    parser = argparse.ArgumentParser(description="Generate MP3 files from TSV using Piper or Qwen3-TTS.")
    parser.add_argument("--engine", choices=["piper", "qwen"], default="piper", help="TTS engine to use.")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for Qwen3-TTS.")
    args = parser.parse_args()

    # 1. Prepare data
    with open(TSV_FILE, mode='r', encoding='utf-8') as f:
        rows = list(csv.reader(f, delimiter='\t'))

    if args.engine == "piper":
        num_cores = multiprocessing.cpu_count()
        print(f"Using Piper. Initializing {num_cores} workers for {len(rows)} rows...")
        with multiprocessing.Pool(
            processes=num_cores, 
            initializer=init_piper_worker, 
            initargs=(PIPER_MODEL_PATH, PIPER_CONFIG_PATH)
        ) as pool:
            results = pool.map(process_row_piper, rows)
        print("Batch processing complete.")

    elif args.engine == "qwen":
        print(f"Using Qwen3-TTS ({QWEN_MODEL_NAME}).")
        from qwen_tts import Qwen3TTSModel
        import torchaudio

        # Load model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        print(f"Loading model on {device} with {dtype}...")
        
        model = Qwen3TTSModel.from_pretrained(
            QWEN_MODEL_NAME,
            device_map=device,
            torch_dtype=dtype
        )

        # Prepare texts
        all_data = []
        for row in rows:
            if not row: continue
            filename_base = row[0].strip()
            text_content = row[0].strip() + '.' if len(row) < 2 else row[1].strip()
            all_data.append((filename_base, text_content))

        # Process in batches
        for i in range(0, len(all_data), args.batch_size):
            batch = all_data[i : i + args.batch_size]
            batch_filenames = [item[0] for item in batch]
            batch_texts = [item[1] for item in batch]

            print(f"Processing batch {i // args.batch_size + 1}: {len(batch_texts)} items...")
            
            # Using the batch inference API
            # Based on Qwen3-TTS documentation for VoiceDesign models
            wavs, sr = model.generate_custom_voice(
                text=batch_texts,
                language=["English"] * len(batch_texts),
                speaker=["Aiden"] * len(batch_texts),
                instruct=["Slow and clear."] * len(batch_texts)
            )

            # Save WAVs and convert to MP3
            for j, wav in enumerate(wavs):
                filename_base = batch_filenames[j]
                wav_filename = os.path.join(SND_DIR, f"{filename_base}.wav")
                mp3_filename = os.path.join(SND_DIR, f"{filename_base}.mp3")

                # Ensure wav is a 2D tensor (channels, samples) for torchaudio
                if not isinstance(wav, torch.Tensor):
                    wav = torch.tensor(wav)
                
                if wav.ndim == 1:
                    wav = wav.unsqueeze(0)
                
                # Qwen-TTS might output float32 waveforms
                torchaudio.save(wav_filename, wav.to(torch.float32).cpu(), sr)
                
                # Convert to MP3
                convert_to_mp3(wav_filename, mp3_filename)
                print(f"Generated: {mp3_filename}")

        print("Batch processing complete.")

if __name__ == "__main__":
    main()