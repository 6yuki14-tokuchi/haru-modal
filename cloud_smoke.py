
import shutil
import base64,hashlib,json,os,select,socket,ssl,struct,subprocess,time,urllib.request,urllib.error
from pathlib import Path
BASE=os.environ["HARU_URL"]
PASSWORD=os.environ["HARU_PASSWORD"]
CASE=os.environ.get("HARU_CASE","short_chat")
FFMPEG=shutil.which("ffmpeg")
assert FFMPEG, "Cloud runner needs ffmpeg"
input_audio=base64.b64decode(os.environ["HARU_TEST_GROUNDING" if CASE=="grounding" else "HARU_TEST_CHAT"])
AUTH="Basic "+base64.b64encode(("haru:"+PASSWORD).encode()).decode()
def req(path,data=None,ctype=None,auth=True,timeout=900):
    h={"Authorization":AUTH} if auth else {}
    if ctype:h["Content-Type"]=ctype
    r=urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=h),timeout=timeout)
    return r.status,r.read()
def getjson(path):return json.loads(req(path)[1])
t0=time.monotonic()
config=getjson("/api/config")
assert config["default_language"]=="ja",config["default_language"]
assert config["time_limit_seconds"]==180
try:
    req("/api/config",auth=False,timeout=30)
    raise AssertionError("Unauthenticated request was not denied")
except urllib.error.HTTPError as e:
    assert e.code==401,e.code
for i in range(120):
    if getjson("/api/ready")["ready"]:break
    time.sleep(2)
else:raise RuntimeError("Model did not become ready")
print(json.dumps({"stage":"ready","elapsed_s":time.monotonic()-t0,"language":"ja","unauthenticated_status":401}),flush=True)
ref=subprocess.run([FFMPEG,"-v","error","-i","pipe:0","-ac","1","-ar","24000","-f","wav","pipe:1"],input=base64.b64decode(os.environ["HARU_TEST_REFERENCE"]),capture_output=True,check=True).stdout
reference=json.loads(req("/api/reference_audio",ref,"audio/wav")[1])
prompt=("あなたはテスト店の受付係のハルです。日本語で短く丁寧に話します。営業時間は午前10時から午後6時です。予約手数料は未確認です。金額を推測せず、分からないと伝えて担当者に確認します。" if CASE=="grounding" else "あなたの名前はハル。日本語でフランクに、親しい友人として短く自然に話します。相手の話を聞いて、質問や相づちを交えて会話してください。")
session=json.loads(req("/api/session",json.dumps({"system_prompt":prompt,"reference_audio_id":reference["id"],"guidance_scale":1.5}).encode(),"application/json")[1])
opus=subprocess.run([FFMPEG,"-v","error","-i","pipe:0","-af","apad=pad_dur=5","-ac","1","-ar","24000","-c:a","libopus","-b:a","32k","-application","voip","-page_duration","133333","-f","ogg","pipe:1"],input=input_audio,capture_output=True,check=True).stdout
pages=[];p=0
while p<len(opus):
    assert opus[p:p+4]==b"OggS"
    count=opus[p+26];size=27+count+sum(opus[p+27:p+27+count])
    granule=struct.unpack_from("<Q",opus,p+6)[0]
    pages.append((0 if granule==(2**64-1) else granule/48000,opus[p:p+size]))
    p+=size
host=urllib.parse.urlsplit(BASE).hostname
s=ssl.create_default_context().wrap_socket(socket.create_connection((host,443),timeout=30),server_hostname=host)
key=base64.b64encode(os.urandom(16)).decode()
path="/api/chat?session_id="+session["id"]
s.sendall(("GET "+path+" HTTP/1.1\r\nHost: "+host+"\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: "+key+"\r\nAuthorization: "+AUTH+"\r\nOrigin: "+BASE+"\r\n\r\n").encode())
buf=b""
while b"\r\n\r\n" not in buf:buf+=s.recv(4096)
headers,buf=buf.split(b"\r\n\r\n",1)
assert headers.startswith(b"HTTP/1.1 101"),headers[:150]
expected=base64.b64encode(hashlib.sha1((key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest())
assert b"sec-websocket-accept: "+expected in headers.lower() or expected in headers
def send(payload,opcode=2):
    n=len(payload);h=bytes([0x80|opcode])
    h+=bytes([0x80|n]) if n<126 else (bytes([0x80|126])+struct.pack("!H",n) if n<65536 else bytes([0x80|127])+struct.pack("!Q",n))
    mask=os.urandom(4);s.sendall(h+mask+bytes(v^mask[i%4] for i,v in enumerate(payload)))
def extract():
    global buf
    out=[]
    while len(buf)>=2:
        first,second=buf[:2];n=second&127;k=2
        if n==126:
            if len(buf)<4:break
            n=struct.unpack("!H",buf[2:4])[0];k=4
        elif n==127:
            if len(buf)<10:break
            n=struct.unpack("!Q",buf[2:10])[0];k=10
        if second&128:k+=4
        if len(buf)<k+n:break
        payload=buf[k:k+n]
        if second&128:
            mask=buf[k-4:k];payload=bytes(v^mask[i%4] for i,v in enumerate(payload))
        buf=buf[k+n:];out.append((first&15,payload))
    return out
started=time.monotonic();stream_start=None;idx=0;texts=[];audio=[];closed=False;handshake=False;chunks=0;first_audio=None
while time.monotonic()-started<175:
    now=time.monotonic()
    if handshake:
        while idx<len(pages) and now-stream_start>=pages[idx][0]:
            send(b"\x01"+pages[idx][1]);idx+=1
    if s.pending() or select.select([s],[],[],0.02)[0]:
        data=s.recv(65536)
        if not data:break
        buf+=data
    for opcode,payload in extract():
        if opcode==9:send(payload,10);continue
        if opcode==8:closed=True;break
        if opcode!=2 or not payload:continue
        if payload[0]==0 and not handshake:
            handshake=True;stream_start=time.monotonic()
        elif payload[0]==1:
            audio.append(payload[1:]);chunks+=1
            if first_audio is None:first_audio=time.monotonic()-stream_start
        elif payload[0]==2:
            part=payload[1:].decode("utf-8")
            texts.append(part)
            if "[error]" in part:raise RuntimeError(part)
    if closed:break
    if handshake and idx==len(pages) and now-stream_start>pages[-1][0]+20:break
send(b"",8);s.close()
ogg=b"".join(audio)
pcm=subprocess.run([FFMPEG,"-v","error","-i","pipe:0","-f","f32le","-ac","1","-ar","24000","pipe:1"],input=ogg,capture_output=True,check=True).stdout
import numpy as np
a=np.frombuffer(pcm,dtype="<f4")
result={"case":CASE,"input_transport":"8 kbps Opus from existing synthesized Japanese fixture","first_audio_after_handshake_s":first_audio,"default_language":config["default_language"],"unauthenticated_status":401,"model_ready":True,"websocket_handshake":handshake,"sent_ogg_pages":idx,"received_audio_chunks":chunks,"reply_text":"".join(texts),"output_audio_seconds":len(a)/24000,"audio_peak":float(np.max(np.abs(a))) if len(a) else 0,"audio_rms":float(np.sqrt(np.mean(a*a))) if len(a) else 0,"input_sha256":hashlib.sha256(input_audio).hexdigest(),"output_ogg_sha256":hashlib.sha256(ogg).hexdigest(),"elapsed_including_network_and_input_playback_s":time.monotonic()-t0,"scope":"Actual authenticated WebSocket audio stream from fixed synthesized Japanese recording; no physical microphone or subjective listening score."}
assert result["reply_text"],result
assert result["audio_peak"]>.001,result
assert result["output_audio_seconds"]>5,result
print(json.dumps({"stage":"result","result":result},ensure_ascii=False),flush=True)
