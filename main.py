import os, re, json, uuid, shutil, subprocess, threading
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE=Path(__file__).resolve().parent
DATA=BASE/'data'; DATA.mkdir(exist_ok=True)
REF=DATA/'reference.wav'
LANGS={'es':'Español','en':'English','fr':'Français','pt':'Português','de':'Deutsch','it':'Italiano','ja':'日本語','ko':'한국어','zh':'中文','ar':'العربية','hi':'हिन्दी','ru':'Русский','nl':'Nederlands','pl':'Polski','tr':'Türkçe','sv':'Svenska','da':'Dansk','fi':'Suomi','no':'Norsk','el':'Ελληνικά','he':'עברית','ms':'Bahasa Melayu','sw':'Kiswahili'}
app=FastAPI(title='Valentino AI Studio v2')
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
templates=Jinja2Templates(directory=BASE/'templates')
model=None
model_lock=threading.Lock()
queue_lock=threading.Lock()
active_jobs=set()
state_lock=threading.Lock()

def directory(job_id):
    if not re.fullmatch('[a-f0-9]{32}',job_id): raise HTTPException(400,'ID inválido')
    return DATA/job_id

def read(job_id):
    p=directory(job_id)/'job.json'
    if not p.exists(): raise HTTPException(404,'Trabalho não encontrado')
    return json.loads(p.read_text(encoding='utf-8'))

def update(job_id,**kw):
    with state_lock:
        state=read(job_id);state.update(kw)
        p=directory(job_id)/'job.json';temp=p.with_suffix('.tmp')
        temp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(p)

def split_text(text,limit=280):
    sentences=re.split(r'(?<=[.!?。！？])\s+',re.sub(r'\s+',' ',text).strip())
    parts=[];buf=''
    for sentence in sentences:
        while len(sentence)>limit:
            k=sentence.rfind(' ',0,limit)
            if k<limit//3:k=limit
            if buf:parts.append(buf);buf=''
            parts.append(sentence[:k].strip());sentence=sentence[k:].strip()
        if buf and len(buf)+len(sentence)+1>limit:parts.append(buf);buf=''
        buf=(buf+' '+sentence).strip()
    if buf:parts.append(buf)
    return [p for p in parts if p]

def load_model():
    global model
    if model is None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        model=ChatterboxMultilingualTTS.from_pretrained(device='cpu')
    return model

def run(job_id):
    folder=directory(job_id)
    try:
        state=read(job_id)
        job_ref=folder/'reference.wav'
        if not job_ref.exists():raise RuntimeError('A referência deste trabalho não foi encontrada.')
        if not shutil.which('ffmpeg'):raise RuntimeError('FFmpeg não encontrado no PATH.')
        text=(folder/'script.txt').read_text(encoding='utf-8')
        parts=split_text(text)
        update(job_id,status='processing',total=len(parts),error=None)
        import torchaudio
        with model_lock:
            voice=load_model()
            for i,part in enumerate(parts):
                wav=folder/f'{i:05d}.wav'
                if not wav.exists():
                    audio = voice.generate(
                        part,
                        language_id=state['language'],
                        audio_prompt_path=str(job_ref),
                        exaggeration=0.3,
                        cfg_weight=0.5,
                        temperature=0.7
                    )
                    torchaudio.save(str(wav),audio.cpu(),voice.sr)
                update(job_id,completed=i+1,progress=round((i+1)/len(parts)*95,1))
        playlist=folder/'concat.txt'
        playlist.write_text(''.join(f"file '{i:05d}.wav'\n" for i in range(len(parts))),encoding='utf-8')
        output=folder/'narracao.mp3'
        subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(playlist),'-c:a','libmp3lame','-b:a','192k',str(output)],cwd=folder,check=True)
        update(job_id,status='done',progress=100,output_bytes=output.stat().st_size)
    except Exception as exc:
        update(job_id,status='error',error=str(exc))
    finally:
        with queue_lock:
            active_jobs.discard(job_id)

@app.get('/')
def home(request:Request):return templates.TemplateResponse(request=request,name='index.html',context={'languages':LANGS})

@app.get('/api/info')
def info():return {'reference_ready':REF.exists(),'engine':'Chatterbox Multilingual (CPU)','ffmpeg':bool(shutil.which('ffmpeg')),'languages':LANGS}

@app.post('/api/reference')
async def reference(file:UploadFile=File(...)):
    if not shutil.which('ffmpeg'):raise HTTPException(503,'Instale FFmpeg e adicione ao PATH.')
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in {'.wav','.mp3','.m4a','.ogg','.flac','.mp4'}:raise HTTPException(400,'Formato não suportado')
    raw=DATA/('upload'+suffix);size=0
    with raw.open('wb') as out:
        while block:=await file.read(1024*1024):
            size+=len(block)
            if size>80*1024*1024:
                raw.unlink(missing_ok=True);raise HTTPException(413,'Amostra maior que 80 MB')
            out.write(block)
    try:
        subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(raw),'-vn','-ac','1','-ar','24000','-t','30',str(REF)],check=True)
    except subprocess.CalledProcessError:raise HTTPException(400,'Falha ao converter a amostra')
    finally:raw.unlink(missing_ok=True)
    return {'ok':True,'message':'Amostra de até 30 segundos preparada.'}

@app.post('/api/jobs')
def create(text:str=Form(...),language:str=Form('es')):
    if language not in LANGS:raise HTTPException(400,'Idioma inválido')
    if not REF.exists():raise HTTPException(400,'Envie uma amostra primeiro')
    if not shutil.which('ffmpeg'):raise HTTPException(503,'FFmpeg não encontrado no PATH')
    if not text.strip():raise HTTPException(400,'Texto vazio')
    if len(text)>500000:raise HTTPException(413,'Limite de 500 mil caracteres')
    jid=uuid.uuid4().hex;folder=directory(jid);folder.mkdir()
    (folder/'script.txt').write_text(text.strip(),encoding='utf-8')
    shutil.copy2(REF,folder/'reference.wav')
    state={'id':jid,'language':language,'characters':len(text),'status':'queued','progress':0,'completed':0,'total':0,'created_at':datetime.now(timezone.utc).isoformat(),'error':None}
    (folder/'job.json').write_text(json.dumps(state,ensure_ascii=False),encoding='utf-8')
    with queue_lock: active_jobs.add(jid)
    threading.Thread(target=run,args=(jid,),daemon=True).start()
    return state

@app.get('/api/jobs')
def jobs():
    result=[]
    for p in DATA.glob('*/job.json'):
        try:result.append(json.loads(p.read_text(encoding='utf-8')))
        except Exception:pass
    return sorted(result,key=lambda j:j['created_at'],reverse=True)[:50]

@app.get('/api/jobs/{job_id}')
def status(job_id:str):return read(job_id)

@app.post('/api/jobs/{job_id}/retry')
def retry(job_id:str):
    state=read(job_id)
    if state['status'] in ('queued','processing'):raise HTTPException(409,'Trabalho já está em execução')
    with queue_lock:
        if job_id in active_jobs:raise HTTPException(409,'Trabalho já está em execução')
        active_jobs.add(job_id)
    update(job_id,status='queued',error=None)
    threading.Thread(target=run,args=(job_id,),daemon=True).start()
    return {'ok':True}

@app.get('/api/jobs/{job_id}/download')
def download(job_id:str):
    if read(job_id)['status']!='done':raise HTTPException(409,'Áudio ainda não está pronto')
    return FileResponse(directory(job_id)/'narracao.mp3',media_type='audio/mpeg',filename='valentino-narracao.mp3')
