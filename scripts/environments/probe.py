"""Check installed package versions, optionally testing model imports and CUDA."""
import argparse
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.senna_requirements import project

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('model', choices=('senna', 'vad'))
parser.add_argument('--upstream', required=True, type=Path)
parser.add_argument('--packages-only', action='store_true', help='Check metadata and pip consistency without importing torch or initializing CUDA')
args = parser.parse_args()
print('python:', sys.version, 'executable:', sys.executable, 'host:', platform.node(), flush=True)
print('CUDA_VISIBLE_DEVICES:', os.environ.get('CUDA_VISIBLE_DEVICES'), flush=True)
sys.path.insert(0, str(args.upstream.resolve()))
expected = {'senna': {'torch': '2.0.1+cu118', 'torchvision': '0.15.2+cu118',
                      'transformers': '4.31.0', 'tokenizers': '0.13.3'},
            'vad': {'torch': '1.9.1+cu111', 'torchvision': '0.10.1+cu111',
                    'mmcv-full': '1.4.0', 'mmdet': '2.14.0', 'mmsegmentation': '0.14.1',
                    'mmdet3d': '0.17.1'}}[args.model]
if args.model == 'senna':
    profile = json.loads((Path(__file__).resolve().parents[2] / 'configs/senna-inference-packages.json').read_text())
    pins, _ = project((args.upstream / 'requirements.txt').read_text(), profile['packages'])
    expected = dict(pin.split('==', 1) for pin in pins)
for name, version in expected.items():
    actual = metadata.version(name)
    print(name, actual, flush=True)
    if actual != version:
        raise SystemExit(f'{name}: expected {version}, found {actual}')
if args.packages_only:
    subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'freeze', '--all'], check=True)
    print(args.model.upper() + '_PACKAGES_OK; GPU/model validation not performed', flush=True)
    sys.exit(0)
import torch
print(json.dumps({'torch_cuda': torch.version.cuda, 'cuda_available': torch.cuda.is_available(),
                  'visible_gpu_count': torch.cuda.device_count()}), flush=True)
if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
    raise SystemExit('Exactly one visible CUDA device is required')
print('assigned_gpu:', torch.cuda.get_device_name(0), flush=True)
x = torch.arange(16, device='cuda', dtype=torch.float32).reshape(4, 4)
assert torch.isfinite(x @ x).all().item()
torch.cuda.synchronize()
modules = {'senna': ['llava.model.language_model.llava_llama', 'llava.senna.senna_llava_llama', 'llava.model.multimodal_projector.Qformer',
                      'llava.model.builder', 'data_tools.senna_qa_utils'],
           'vad': ['mmcv.ops', 'mmdet', 'mmseg', 'mmdet3d', 'projects.mmdet3d_plugin']}[args.model]
for name in modules:
    module = importlib.import_module(name)
    print('IMPORTED', name, getattr(module, '__file__', None), flush=True)
if args.model == 'senna':
    from llava.model.builder import load_senna_pretrained_model
    from llava.senna.senna_llava_llama import SennaLlavaLlamaForCausalLM
    assert callable(load_senna_pretrained_model)
    assert issubclass(SennaLlavaLlamaForCausalLM, torch.nn.Module)
    import numpy as np
    assert np.allclose(torch.from_numpy(np.array([1., 2.], dtype=np.float32)).numpy(), [1., 2.])
else:
    from mmcv.ops import nms
    boxes = torch.tensor([[0., 0., 1., 1.], [0., 0., 1., 1.]], device='cuda')
    _, indices = nms(boxes, torch.tensor([0.9, 0.8], device='cuda'), 0.5)
    assert len(indices) == 1
subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'freeze', '--all'], check=True)
print(args.model.upper() + '_IMPORTS_OK', flush=True)
