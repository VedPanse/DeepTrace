from huggingface_hub import HfApi,snapshot_download
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
name='mlx-community/Qwen3-4B-Instruct-2507-4bit'
sha=HfApi().model_info(name).sha
(root/'results/model_pin.json').write_text(json.dumps({'model':name,'revision':sha,'purpose':'local fixed evaluation monitor; no training'},indent=2))
p=snapshot_download(name,revision=sha,local_dir=root/'models/qwen3-4b',ignore_patterns=['*.md','.gitattributes'])
print(p)
