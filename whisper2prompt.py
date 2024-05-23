import argparse
import os
import traceback
import requests
from glob import glob
from tqdm import tqdm
from pathlib import Path
base_path=Path(__file__).parent.absolute()
base_path = base_path/"models"
local = False
if os.path.exists(base_path):
    local = True

def check_fw_local_models():
    '''
    启动时检查本地是否有 Faster Whisper 模型.
    '''
    model_size_list = [
        "tiny",     "tiny.en", 
        "base",     "base.en", 
        "small",    "small.en", 
        "medium",   "medium.en", 
        "large",    "large-v1", 
        "large-v2", "large-v3"]
    for i, size in enumerate(model_size_list):
        if local:
            if os.path.exists(base_path/f'faster-whisper-{size}'):
                model_size_list[i] = size + '(local)'
            else:
                if os.path.exists(f'faster-whisper-{size}'):
                    model_size_list[i] = size + '(local)'
        
    return model_size_list

os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

language_code_list = [
    "af", "am", "ar", "as", "az", 
    "ba", "be", "bg", "bn", "bo", 
    "br", "bs", "ca", "cs", "cy", 
    "da", "de", "el", "en", "es", 
    "et", "eu", "fa", "fi", "fo", 
    "fr", "gl", "gu", "ha", "haw", 
    "he", "hi", "hr", "ht", "hu", 
    "hy", "id", "is", "it", "ja", 
    "jw", "ka", "kk", "km", "kn", 
    "ko", "la", "lb", "ln", "lo", 
    "lt", "lv", "mg", "mi", "mk", 
    "ml", "mn", "mr", "ms", "mt", 
    "my", "ne", "nl", "nn", "no", 
    "oc", "pa", "pl", "ps", "pt", 
    "ro", "ru", "sa", "sd", "si", 
    "sk", "sl", "sn", "so", "sq", 
    "sr", "su", "sv", "sw", "ta", 
    "te", "tg", "th", "tk", "tl", 
    "tr", "tt", "uk", "ur", "uz", 
    "vi", "yi", "yo", "zh", "yue",
    "auto"]

def execute_asr(input_files, output_folder, model_size, language,precision):
    output_file_paths =[]
    for input_file in input_files:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_file_name = os.path.basename(input_file)
        output_file_path = os.path.abspath(f'{output_folder}/{output_file_name}.json')
        if os.path.exists(output_file_path):
            output_file_paths.append(output_file_path)
        if 'local' in model_size:
            if local:
                model_size = model_size.split('(')[0]
                model_path = str(base_path/f'faster-whisper-{model_size}')
            else:
                model_size = model_size.split('(')[0]
                model_path = str(f'faster-whisper-{model_size}')
        else:
            if local:
                model_path = str(base_path/f'faster-whisper-{model_size}')
            else:
                model_path = str(f'faster-whisper-{model_size}')
        if language == 'auto':
            language = None #不设置语种由模型自动输出概率最高的语种
    if len(output_file_paths)==len(input_files):
        return output_file_paths
    print("loading faster whisper model:",model_size,model_path)
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    try:  
        from faster_whisper import WhisperModel
        model = WhisperModel(model_path, device="cuda", compute_type=precision,download_root=model_path)
    except:
        return print(traceback.format_exc())
    output = []

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for input_file in input_files:
        print(input_file)
        output =[]
        output_file_name = os.path.basename(input_file)
        output_file_path = os.path.abspath(f'{output_folder}/{output_file_name}.json')
        if os.path.exists(output_file_path):
            continue
        file = input_file
        try:
            segments, info = model.transcribe(
            audio          = file,
            beam_size      = 5,
            vad_filter     = True,
            vad_parameters = dict(min_silence_duration_ms=700),
            language       = language)
            for segment in segments:
                output.append(dict(name="Name",start=segment.start, end=segment.end,message=segment.text))
        except:
            return print(traceback.format_exc())
        
        import json
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False)
            print(f"ASR 任务完成->标注文件路径: {output_file_path}\n")
            output_file_paths.append(output_file_path)
    return output_file_paths
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str, required=True,
                        help="Path to the folder containing WAV files.")
    parser.add_argument("-o", "--output_folder", type=str, required=True, 
                        help="Output folder to store transcriptions.")
    parser.add_argument("-s", "--model_size", type=str, default='large-v3', 
                        choices=check_fw_local_models(),
                        help="Model Size of Faster Whisper")
    parser.add_argument("-l", "--language", type=str, default='ja',
                        choices=language_code_list,
                        help="Language of the audio files.")
    parser.add_argument("-p", "--precision", type=str, default='float16', choices=['float16','float32'],
                        help="fp16 or fp32")

    cmd = parser.parse_args()
    output_file_path = execute_asr(
        input_file  = cmd.input_file,
        output_folder = cmd.output_folder,
        model_size    = cmd.model_size,
        language      = cmd.language,
        precision     = cmd.precision,
    )