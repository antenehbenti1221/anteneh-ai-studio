# ANTENEH AI STUDIO — ONE-CELL COLAB BOOTSTRAP v6
# Deterministic Wan2.1 launch: explicit PYTHONPATH + cwd + dashscope import dependency.
import os,sys,subprocess,time,re,json
from pathlib import Path
STUDIO=Path('/content/anteneh-ai-studio'); WAN=Path('/content/Wan2.1'); MODEL=Path('/content/Wan2.1-T2V-1.3B'); WORK=Path('/content/anteneh-ai-jobs'); WORK.mkdir(parents=True,exist_ok=True)
def sh(c,check=True): print('>',c); return subprocess.run(c,shell=True,check=check)
print('=== ANTENEH AI STUDIO — AUTOMATIC v6 ===')
import torch
if not torch.cuda.is_available(): raise RuntimeError('CUDA GPU is required.')
print('GPU:',torch.cuda.get_device_name(0)); print('VRAM:',round(torch.cuda.get_device_properties(0).total_memory/1024**3,2),'GB')
if not (STUDIO/'.git').exists(): sh('git clone https://github.com/antenehbenti1221/anteneh-ai-studio.git /content/anteneh-ai-studio')
if not (WAN/'generate.py').exists():
    if WAN.exists(): sh('rm -rf /content/Wan2.1')
    sh('git clone --depth 1 https://github.com/Wan-Video/Wan2.1.git /content/Wan2.1')
print('Wan:',WAN,'generate.py:',(WAN/'generate.py').exists())
sh('pip install -q ftfy dashscope fastapi uvicorn requests huggingface_hub imageio imageio-ffmpeg')
req=WAN/'requirements.txt'
if req.exists():
    safe=WAN/'requirements_no_flash.txt'
    safe.write_text('\n'.join(x for x in req.read_text().splitlines() if not x.strip().startswith('flash_attn'))+'\n')
    sh(f'{sys.executable} -m pip install -q -r {safe}')
# Repair the scientific stack only if import is broken; do not blindly downgrade a working NumPy.
env=os.environ.copy(); env['PYTHONPATH']=f'{WAN}:{STUDIO}:'+env.get('PYTHONPATH','')
env['PYTHONUNBUFFERED']='1'
test=subprocess.run([sys.executable,'-c','import sys; sys.path.insert(0,"/content/Wan2.1"); import ftfy, dashscope, torch, wan; print("IMPORTS_OK",ftfy.__version__,torch.__version__)'],cwd=str(WAN),env=env,text=True,capture_output=True)
if test.returncode!=0:
    print(test.stdout); print(test.stderr)
    sh(f'{sys.executable} -m pip install -q --force-reinstall "numpy<3" ftfy dashscope')
    test=subprocess.run([sys.executable,'-c','import sys; sys.path.insert(0,"/content/Wan2.1"); import ftfy, dashscope, torch, wan; print("IMPORTS_OK",ftfy.__version__,torch.__version__)'],cwd=str(WAN),env=env,text=True,capture_output=True)
    if test.returncode!=0: raise RuntimeError('Wan2.1 imports still fail:\n'+test.stderr)
print(test.stdout.strip())
required=[MODEL/'Wan2.1_VAE.pth',MODEL/'models_t5_umt5-xxl-enc-bf16.pth',MODEL/'diffusion_pytorch_model.safetensors']
if not all(x.exists() for x in required): sh(f'{sys.executable} -m huggingface_hub.commands.huggingface_cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir {MODEL}')
if not all(x.exists() for x in required): raise RuntimeError('Wan2.1 T2V 1.3B model incomplete.')
adapter=WAN/'anteneh_wan_adapter.py'
adapter.write_text(r'''import json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/content/Wan2.1'); MODEL=Path('/content/Wan2.1-T2V-1.3B')
job=Path(sys.argv[1]); out=Path(sys.argv[2]); data=json.loads(job.read_text(encoding='utf-8')); out.parent.mkdir(parents=True,exist_ok=True)
env=os.environ.copy(); env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH',''); env['PYTHONUNBUFFERED']='1'
cmd=[sys.executable,'generate.py','--task','t2v-1.3B','--size','832*480','--ckpt_dir',str(MODEL),'--offload_model','True','--t5_cpu','--sample_shift','8','--sample_guide_scale','6','--prompt',data['prompt'],'--save_file',str(out)]
print('WAN2.1 START:', ' '.join(cmd), flush=True)
result=subprocess.run(cmd,cwd=str(ROOT),env=env)
if result.returncode!=0: raise RuntimeError(f'Wan2.1 exited with code {result.returncode}')
if not out.exists() or out.stat().st_size==0: raise RuntimeError('Wan2.1 did not create a non-empty MP4.')
print('WAN2.1 READY:',out,'bytes=',out.stat().st_size,flush=True)
''',encoding='utf-8')
sh(f'{sys.executable} -m py_compile {adapter}')
env.update({'VIDEO_MODEL':'Wan2.1-T2V-1.3B','WORK_DIR':str(WORK),'VIDEO_RUNNER_CMD':f'{sys.executable} {adapter} {{job}} {{output}}','WAN_DIR':str(WAN),'PYTHONPATH':f'{WAN}:{STUDIO}:'+env.get('PYTHONPATH','')})
sh('fuser -k 8000/tcp 2>/dev/null || true',False); time.sleep(2)
log_path=Path('/content/anteneh-worker.log'); log=open(log_path,'w')
p=subprocess.Popen([sys.executable,'-m','uvicorn','gpu-worker.http_worker:app','--host','0.0.0.0','--port','8000'],cwd=str(STUDIO),env=env,stdout=log,stderr=subprocess.STDOUT)
import requests
for _ in range(45):
    try:
        r=requests.get('http://127.0.0.1:8000/health',timeout=2)
        if r.ok: print('LOCAL HEALTH:',r.json()); break
    except: pass
    time.sleep(1)
else: print(log_path.read_text(errors='ignore')[-16000:]); raise RuntimeError('Worker failed to start.')
cf=Path('/content/cloudflared')
if not cf.exists(): sh('wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /content/cloudflared && chmod +x /content/cloudflared')
sh('pkill -x cloudflared 2>/dev/null || true',False); time.sleep(2)
cf_log_path=Path('/content/cloudflare-tunnel.log'); cf_log=open(cf_log_path,'w'); cfp=subprocess.Popen([str(cf),'tunnel','--url','http://127.0.0.1:8000','--no-autoupdate'],stdout=cf_log,stderr=subprocess.STDOUT)
public=None
for _ in range(60):
    time.sleep(1); cf_log.flush(); text=cf_log_path.read_text(errors='ignore'); urls=re.findall(r'https://[A-Za-z0-9.-]+\.trycloudflare\.com',text)
    if urls: public=urls[-1]; break
if not public: print(cf_log_path.read_text(errors='ignore')[-12000:]); raise RuntimeError('Cloudflare tunnel failed.')
Path('/content/anteneh-public-url.txt').write_text(public); print('PUBLIC URL:',public)
for _ in range(20):
    try:
        h=requests.get(public+'/health',timeout=10)
        if h.ok: print('PUBLIC HEALTH:',h.json()); break
    except Exception as e: last=e
    time.sleep(2)
else: print('PUBLIC HEALTH PENDING:',repr(last))
print('=== REAL VIDEO GENERATION TEST ===')
prompt='A cinematic realistic scene of a thoughtful young Ethiopian man sitting at a wooden desk in the evening, looking at a notebook and thinking deeply about his future, warm realistic lighting, subtle camera movement.'
rr=requests.post('http://127.0.0.1:8000/jobs',json={'prompt':prompt,'duration_seconds':5},timeout=30)
print('TEST SUBMIT:',rr.status_code,rr.text)
if not rr.ok: raise RuntimeError('Test job submission failed.')
jid=rr.json().get('job_id') or rr.json().get('id')
if not jid: raise RuntimeError('Worker did not return a job id.')
final=None
for i in range(120):
    time.sleep(5); st=requests.get(f'http://127.0.0.1:8000/jobs/{jid}',timeout=20); print(f'TEST {i+1}:',st.text)
    if st.ok and st.json().get('status') in ('completed','failed','error'):
        final=st.json(); break
if not final or final.get('status')!='completed':
    print('--- WORKER LOG ---'); print(log_path.read_text(errors='ignore')[-24000:]); raise RuntimeError(f'REAL VIDEO TEST FAILED: {final}')
video=WORK/jid/'final.mp4'
if not video.exists() or video.stat().st_size==0: raise RuntimeError('Completed job has no valid MP4.')
print('=== SUCCESS ==='); print('TEST VIDEO:',video); print('PUBLIC API:',public); print('HEALTH:',public+'/health'); print('DOCS:',public+'/docs'); print('KEEP COLAB RUNTIME RUNNING.')
