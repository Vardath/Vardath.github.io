"""Three distinct publisher models, fixed local roles."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MODEL_ID='deepthort-triad'
PROFILES={
 'implementation':('Rnj-1-Instruct 8B','EssentialAI/rnj-1-instruct-GGUF','Rnj-1-Instruct-8B-Q4_K_M.gguf','0d72c498da745ee74a477264e7c01edfe22bd8a36441b22d482dea3b992abfab',5_000_000_000),
 'janus':('Granite 4.2 3B','ibm-granite/granite-4.2-3b-GGUF','granite-4.2-3b-Q4_K_M.gguf','e0406663965846ae22a403456eb826ccce5f450840491f71952f18a7cb78e7d5',2_100_000_000),
 'sentinel':('MiniCPM5 2B','openbmb/MiniCPM5-2B-GGUF','MiniCPM5-2B-Q4_K_M.gguf','ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd',1_500_000_000),
}
TAG='b12644'
RUNTIME_SHA256='245c62729788171ee29259cc7c6a69ed2af79701dc537983d677c841d9076029'
RUNTIME_URL=f'https://github.com/ggml-org/llama.cpp/releases/download/{TAG}/llama-{TAG}-bin-win-cpu-x64.zip'
def model_path(role,root=ROOT):return Path(root)/'models'/'triad'/PROFILES[role][2]
def runtime_path(root=ROOT):return Path(root)/'runtime'/'triad'/'llama-server.exe'
def role_for_council(role):
    return 'sentinel' if role.upper().startswith('SENTINEL') else 'janus'
def ready(root=ROOT):
    try:return runtime_path(root).is_file() and all(model_path(r,root).stat().st_size>=p[4] for r,p in PROFILES.items())
    except OSError:return False
def total_weights(root=ROOT):
    return sum(model_path(r,root).stat().st_size for r in PROFILES)
