"""Bounded comparison. No user recordings or model weights are committed."""
import base64,io,json,os,subprocess,sys,zipfile
import numpy as np
import tempfile
from pathlib import Path

encoded="".join(os.environ.get("HARU_EVAL_"+str(i),"") for i in range(32))
assert encoded, "Temporary private fixtures are required"
archive=zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded)))
fixtures={key:archive.read(key+".flac") for key in ("reference","chat","meal")}
for key,data in fixtures.items():
    pcm=subprocess.run(["ffmpeg","-v","error","-i","pipe:0","-f","f32le","-ac","1","-ar","24000","pipe:1"],
                       input=data,capture_output=True,check=True).stdout
    samples=np.frombuffer(pcm,dtype="<f4")
    peak=float(np.max(np.abs(samples)))
    active_seconds=float(np.count_nonzero(np.abs(samples)>.01)/24000)
    assert peak>.05 and active_seconds>.5, (key,peak,active_seconds)
    print(json.dumps({"input_check":key,"peak":peak,"active_seconds":active_seconds}),flush=True)
print(json.dumps({"evaluation_plan":{
    "chat_input":"今日は仕事が忙しくて疲れた。そっちは元気？",
    "chat_success":"Answer the question or acknowledge fatigue; do not repeat introductions or switch to an unrelated topic.",
    "held_out_meal":"Suggest dinner, then account for eggs, rice and no knife on the follow-up.",
    "adoption_gate":"Both listen-card chat repetitions relevant, and no regression on held-out meal versus baseline.",
    "sampling":"Uncontrolled server randomness; this is a bounded diagnostic, not a statistical benchmark.",
    "conditions":"Same pinned deployed Haru runtime, same clean synthetic reference, same input and 32 kbps Opus transport for both cards."
}},ensure_ascii=False),flush=True)
temp=tempfile.TemporaryDirectory(prefix="haru-eval-",dir=os.environ.get("RUNNER_TEMP"))
fixture_paths={key:Path(temp.name)/(key+".flac") for key in fixtures}
for key,path in fixture_paths.items():path.write_bytes(fixtures[key])
results=[]
for case,variant,repeat in [("chat","baseline",1),("chat","listen",1),("chat","baseline",2),("chat","listen",2),("meal","baseline",1),("meal","listen",1)]:
    env={key:value for key,value in os.environ.items() if not key.startswith("HARU_EVAL_")}
    env.update(HARU_CASE=case,HARU_CARD_VARIANT=variant,
        HARU_INPUT_TRANSPORT="FLAC fixture decoded then 32 kbps Opus; no 8 kbps intermediate",
        HARU_TEST_REFERENCE_PATH=str(fixture_paths["reference"]),
        HARU_TEST_INPUT_PATH=str(fixture_paths[case]))
    run=subprocess.run([sys.executable,"-u","cloud_smoke.py"],env=env,capture_output=True,text=True,timeout=300)
    if run.returncode:
        print(run.stdout,flush=True)
        raise RuntimeError(run.stderr[-2000:])
    result=None
    for line in run.stdout.splitlines():
        item=json.loads(line)
        if item.get("stage")=="result":
            result=item["result"]
    assert result is not None
    result.update(eval_case=case,variant=variant,repeat=repeat)
    results.append(result)
    print(json.dumps({"evaluation_result":result},ensure_ascii=False),flush=True)
print(json.dumps({"completed_cases":len(results),"content_quality":"Requires review against the fixed acceptance criteria; transport assertions alone do not pass conversational quality."}),flush=True)
