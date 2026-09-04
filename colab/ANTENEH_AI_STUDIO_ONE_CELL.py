# ANTENEH AI STUDIO — ONE-CELL COLAB BOOTSTRAP
# Automatic repair + startup for Wan2.1 T2V 1.3B.
import os,sys,subprocess,time,re
from pathlib import Path
STUDIO=Path('/content/anteneh-ai-studio'); WAN=Path('/content/Wan2.1'); MODEL=Path('/content/Wan2.1-T2V-1.3B'); WORK=Path('/content/anteneh-ai-jobs'); WORK.mkdir(parents=True,exist_ok=True)
def sh(c,check=True): print('>',c); return subprocess.run(c,shell=True,check=check)
print('=== ANTENEH AI STUDIO AUTOMATIC START ===')
import torch
if not torch.cuda.is_available(): raise RuntimeError('No CUDA GPU. Select Runtime > Change runtime type > GPU.')
print('GPU:',torch.cuda.get_device_name(0)); print('VRAM:',round(torch.cuda.get_device_properties(0).total_memory/1024**3,2),'GB')
if not (STUDIO/'.git').exists(): sh('git clone https://github.com/antenehbenti1221/anteneh-ai-studio.git /content/anteneh-ai-studio')
if not (WAN/'generate.py').exists():
    if WAN.exists(): sh('rm -rf /content/Wan2.1')
    sh('git clone --depth 1 https://github.com/Wan-Video/Wan2.1.git /content/Wan2.1')
# Explicitly repair the dependency seen in the failed run.
sh('pip install -q ftfy fastapi uvicorn requests huggingface_hub imageio imageio-ffmpeg')
req=WAN/'requirements.txt'
if req.exists():
    safe=WAN/'requirements_no_flash.txt'; safe.write_text('\n'.join(x for x in req.read_text().splitlines() if not x.strip().startswith('flash_attn'))+'\n'); sh('pip install -q -r /content/Wan2.1/requirements_no_flash.txt')
required=[MODEL/'Wan2.1_VAE.pth',MODEL/'models_t5_umt5-xxl-enc-bf16.pth',MODEL/'diffusion_pytorch_model.safetensors']
if not all(x.exists() for x in required): sh('hf download Wan-AI/Wan2.1-T2V-1.3B --local-dir /content/Wan2.1-T2V-1.3B')
if not all(x.exists() for x in required): raise RuntimeError('Wan2.1 model is incomplete.')
# Recreate adapter AFTER Wan source is present so recloning cannot erase it.
adapter=WAN/'anteneh_wan_adapter.py'
adapter.write_text(r'''import json,subprocess,sys
from pathlib import Path
job=Path(sys.argv[1]); out=Path(sys.argv[2]); data=json.loads(job.read_text(encoding='utf-8')); out.parent.mkdir(parents=True,exist_ok=True)
cmd=[sys.executable,'/content/Wan2.1/generate.py','--task','t2v-1.3B','--size','832*480','--ckpt_dir','/content/Wan2.1-T2V-1.3B','--offload_model','True','--t5_cpu','--sample_shift','8','--sample_guide_scale','6','--prompt',data['prompt'],'--save_file',str(out)]
print('WAN2.1 START'); subprocess.run(cmd,check=True)
if not out.exists() or out.stat().st_size==0: raise RuntimeError('Wan2.1 did not create a non-empty MP4.')
print('WAN2.1 READY:',out)
''',encoding='utf-8')
sh(f'{sys.executable} -m py_compile {adapter}')
os.environ.update({'VIDEO_MODEL':'Wan2.1-T2V-1.3B','WORK_DIR':str(WORK),'VIDEO_RUNNER_CMD':f'{sys.executable} {adapter} {{job}} {{output}}'})
sh('fuser -k 8000/tcp 2>/dev/null || true',False); time.sleep(2)
log_path=Path('/content/anteneh-worker.log'); log=open(log_path,'w')
p=subprocess.Popen([sys.executable,'-m','uvicorn','gpu-worker.http_worker:app','--host','0.0.0.0','--port','8000'],cwd=str(STUDIO),env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT)
import requests
for _ in range(30):
    try:
        r=requests.get('http://127.0.0.1:8000/health',timeout=2)
        if r.ok: print('LOCAL HEALTH:',r.json()); break
    except: pass
    time.sleep(1)
else: print(log_path.read_text(errors='ignore')[-12000:]); raise RuntimeError('Worker failed.')
cf=Path('/content/cloudflared')
if not cf.exists(): sh('wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /content/cloudflared && chmod +x /content/cloudflared')
sh('pkill -f cloudflared || true',False); time.sleep(2)
cf_log_path=Path('/content/cloudflare-tunnel.log'); cf_log=open(cf_log_path,'w'); cfp=subprocess.Popen([str(cf),'tunnel','--url','http://127.0.0.1:8000','--no-autoupdate'],stdout=cf_log,stderr=subprocess.STDOUT)
public=None
for _ in range(30):
    time.sleep(1); cf_log.flush(); text=cf_log_path.read_text(errors='ignore'); urls=re.findall(r'https://[A-Za-z0-9.-]+\.trycloudflare\.com',text)
    if urls: public=urls[-1]; break
if not public: print(cf_log_path.read_text(errors='ignore')[-10000:]); raise RuntimeError('Public tunnel failed.')
Path('/content/anteneh-public-url.txt').write_text(public); print('PUBLIC URL:',public)
try: print('PUBLIC HEALTH:',requests.get(public+'/health',timeout=30).json())
except Exception as e: print('Public health:',e)
print('=== AUTOMATION ONLINE ==='); print('Worker:',public); print('Engine: Wan2.1 T2V 1.3B'); print('Keep Colab runtime running.')
