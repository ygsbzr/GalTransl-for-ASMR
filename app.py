# follow main.py to create a web-based demo
import sys, os
sys.path.append(os.path.dirname(__file__))
import gradio as gr
import tkinter as tk
from tkinter import filedialog
def get_lrc_savepath():
    window =tk.Tk()
    window.wm_attributes("-topmost",1)
    window.withdraw()
    lrc_path=filedialog.askdirectory()
    return lrc_path
    
def worker(input_files, model_size, translator, gpt_token, moonshot_token, sakura_address, proxy_address,save_path):
    for input_file in input_files:
        if input_file.endswith('.srt'):
            from srt2prompt import make_prompt
            print("正在进行字幕转换...")
            import os
            output_file_path = os.path.join('sampleProject/gt_input', os.path.basename(input_file).replace('.srt','.json'))
            make_prompt(input_file, output_file_path)
            print("字幕转换完成！")
    else:
        import os
        print("正在进行语音识别...")
        from whisper2prompt import execute_asr
        output_file_paths = execute_asr(
            input_files  = input_files,
            output_folder = 'sampleProject/gt_input',
            model_size    = model_size,
            language      = 'ja',
            precision     = 'float16',
        )
        print("语音识别完成！")

    print("正在进行翻译配置...")
    with open('sampleProject/config.yaml', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        if gpt_token:
            if 'GPT35' in line:
                lines[idx+2] = f"      - token: {gpt_token}\n"
                lines[idx+6] = f"    defaultEndpoint: https://api.openai.com\n"
                lines[idx+7] = f'    rewriteModelName: ""\n'
            if 'GPT4:' in line:
                lines[idx+2] = f"      - token: {gpt_token}\n"
        if moonshot_token:
            if 'GPT35' in line:
                lines[idx+4] = f"      - token: {moonshot_token}\n"
                lines[idx+6] = f"    defaultEndpoint: https://api.moonshot.cn\n"
                lines[idx+7] = f'    rewriteModelName: "moonshot-v1-8k"\n'
        if sakura_address:
            if 'Sakura' in line:
                lines[idx+1] = f"    endpoint: {sakura_address}\n"
        if proxy_address:
            if 'proxy' in line:
                lines[idx+1] = f"  enableProxy: true\n"
                lines[idx+3] = f"    - address: {proxy_address}\n"
        else:
            if 'proxy' in line:
                lines[idx+1] = f"  enableProxy: false\n"

    with open('sampleProject/config.yaml', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("正在进行翻译...")
    from GalTransl.__main__ import worker
    worker('sampleProject', 'config.yaml', translator, show_banner=False)

    print("正在生成字幕文件...")
    from prompt2srt import make_srt, make_lrc
    tmp_path=""
    for output_file_path in output_file_paths:
        fbase =os.path.basename(output_file_path)
        pure_name =""
        while fbase.rfind(".mp3")!=-1:
            fbase =fbase[:fbase.rfind(".mp3")]
        while fbase.rfind(".wav")!=-1:
            fbase =fbase[:fbase.rfind(".wav")]
        pure_name=fbase
        save_path_part = ""
        if save_path=="":
            save_path_part = input_file[:input_file.rfind(".")]
        else:
            save_path_part = save_path+"\\"+pure_name
        tmp_path =save_path_part
        print(output_file_path)
        make_srt(output_file_path.replace('gt_input','gt_output'), save_path_part+'.srt')
        make_lrc(output_file_path.replace('gt_input','gt_output'), save_path_part+'.lrc')

    return tmp_path+'.srt', tmp_path+'.lrc'

with gr.Blocks() as demo:
    gr.Markdown("# 欢迎使用GalTransl for ASMR！")
    gr.Markdown("您可以使用本程序将日语音视频文件/字幕文件转换为中文字幕文件。")
    input_files = gr.Files(label="1. 请选择音视频文件/SRT文件（或拖拽文件到窗口）")
    model_size = gr.Radio(
        label="2. 请选择语音识别模型大小:",
        choices=['small', 'medium', 'large-v3',],
        value='small'
    )
    from GalTransl import TRANSLATOR_SUPPORTED
    translator = gr.Radio(
        label="3. 请选择翻译器：",
        choices=list(TRANSLATOR_SUPPORTED.keys())[:6],
        value=list(TRANSLATOR_SUPPORTED.keys())[0]
    )
    gpt_token = gr.Textbox(label="4. 请输入GPT3.5/4 API Token", placeholder="留空为使用上次配置的Token")
    moonshot_token = gr.Textbox(label="5. 请输入Moonshot API Token", placeholder="留空为使用上次配置的Token，翻译器请选择GPT3.5")
    sakura_address = gr.Textbox(label="6. 请输入Sakura API地址", placeholder="留空为使用上次配置的地址")
    proxy_address = gr.Textbox(label="7. 请输入翻译引擎代理地址", placeholder="留空为不使用代理")
    save_path =gr.Text(label="save_path")
    output_folder = gr.Button("选择保存位置")
    output_folder.click(get_lrc_savepath,inputs=[],outputs=[save_path],queue=True)


    run = gr.Button("8. 运行（状态详情请见命令行）")
    output_srt = gr.File(label="9. 字幕文件(SRT)")
    output_lrc = gr.File(label="10. 字幕文件(LRC)")

    run.click(worker, inputs=[input_files, model_size, translator, gpt_token, moonshot_token, sakura_address, proxy_address,save_path], outputs=[output_srt, output_lrc], queue=True)

demo.queue().launch(inbrowser=True, server_name='0.0.0.0')
