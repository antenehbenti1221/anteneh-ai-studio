# ANTENEH AI STUDIO — ONE-CELL COLAB BOOTSTRAP
# Run this ONE cell after connecting a Colab GPU.
import os, sys, subprocess, time, re, json
from pathlib import Path

STUDIO=Path('/content/anteneh-ai-studio'); WAN=Path('/content/Wan2.1'); MODEL=Path('/content/Wan2.1-T2V-1.3B')

def sh(cmd, check=True):
    print('>', cmd)
    return subprocess.run(cmd, shell=True, check=check)

print('=== ANTENEH AI STUDIO — ONE CELL START ===')
# 1. Project
if not (STUDIO/'.git').exists(): sh('git clone https://github.com/antenehbenti1221/anteneh-ai-studio.git /content/anteneh-ai-studio')
# 2. Wan source
if not (WAN/'.git').exists(): sh('git clone --depth 1 https://github.com/Wan-Video/Wan2.1.git /content/Wan2.1')
# 3. Python dependencies (skip flash-attn for T4 compatibility)
req=WAN/'requirements.txt'; safe=Path('/content/Wan2.1/requirements_no_flash.txt')
if req.exists():
    safe.write_text('\n'.join(x for x in req.read_text().splitlines() if not x.strip().startswith('flash_attn'))+'\n')
    sh('pip install -q -r /content/Wan2.1/requirements_no_flash.txt')
sh('pip install -q fastapi uvicorn requests huggingface_hub')
# 4. Model
if not (MODEL/'diffusion_pytorch_model.safetensors').exists():
    sh('hf download Wan-AI/Wan2.1-T2V-1.3B --local-dir /content/Wan2.1-T2V-1.3B')
# 5. GPU check
import torch
assert torch.cuda.is_available(), 'No CUDA GPU attached. In Colab select Runtime > Change runtime type > GPU.'
print('GPU:',torch.cuda.get_device_name(0),'VRAM:',round(torch.cuda.get_device_properties(0).total_memory/1024**3,2),'GB')
# 6. Adapter
adapter=WAN/'anteneh_wan_adapter.py'
adapter.write_text('''import json, subprocess, sys\nfrom pathlib import Path\njob=Path(sys.argv[1]); out=Path(sys.argv[2]); data=json.loads(job.read_text()); out.parent.mkdir(parents=True,exist_ok=True)\ncmd=[sys.executable,"/content/Wan2.1/generate.py","--task","t2v-1.3B","--size","832*480","--ckpt_dir","/content/Wan2.1-T2V-1.3B","--prompt",data["prompt"],"--save_file",str(out)]\nsubprocess.run(cmd,check=True)\nif not out.exists(): raise RuntimeError("Wan2.1 did not create the requested output")\n''')
# 7. Environment
os.environ.update({'VIDEO_MODEL':'Wan2.1-T2V-1.3B','WORK_DIR':'/content/anteneh-ai-jobs','VIDEO_COMMAND':'python /content/Wan2.1/anteneh_wan_adapter.py {job} {output}'})
Path('/content/anteneh-ai-jobs').mkdir(exist_ok=True)
# 8. Start worker
subprocess.run("pkill -f 'uvicorn.*http_worker'",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(2)
log=open('/content/anteneh-worker.log','w')
p=subprocess.Popen([sys.executable,'-m','uvicorn','gpu-worker.http_worker:app','--host','0.0.0.0','--port','8000'],cwd=str(STUDIO),env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT)
time.sleep(5)
# 9. Verify local
import requests
r=requests.get('http://127.0.0.1:8000/health',timeout=15)
print('LOCAL HEALTH:',r.status_code,r.text)
assert r.ok, 'Worker failed. See /content/anteneh-worker.log'
# 10. Free public Cloudflare tunnel
cf=Path('/content/cloudflared')
if not cf.exists(): sh('wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /content/cloudflared && chmod +x /content/cloudflared')
subprocess.run('pkill -f cloudflared',shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
cf_log=open('/content/cloudflare-tunnel.log','w')
cfp=subprocess.Popen([str(cf),'tunnel','--url','http://127.0.0.1:8000','--no-autoupdate'],stdout=cf_log,stderr=subprocess.STDOUT)
time.sleep(8)
text=Path('/content/cloudflare-tunnel.log').read_text()
urls=re.findall(r'https://[A-Za-z0-9.-]+\.trycloudflare\.com',text)
assert urls,'Cloudflare tunnel URL was not created. See /content/cloudflare-tunnel.log'
public=urls[-1]
Path('/content/anteneh-public-url.txt').write_text(public)
try:
    pr=requests.get(public+'/health',timeout=30)
    print('PUBLIC HEALTH:',pr.status_code,pr.text)
except Exception as e: print('Public health check:',e)
print('\n==============================================')
print('ANTENEH AI STUDIO AUTOMATION ONLINE')
print('Worker:',public)
print('GPU:',torch.cuda.get_device_name(0))
print('Engine: Wan2.1 T2V 1.3B')
print('==============================================')
print('IMPORTANT: this public URL lasts only while this Colab runtime is alive.')
