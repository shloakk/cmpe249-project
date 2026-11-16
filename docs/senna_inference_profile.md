# Senna-VLM inference package profile

## Observed blocker and decision

Job 116271 created the isolated Python 3.10.22 Conda environment and installed
upstream torch 2.0.1+cu118, torchvision 0.15.2+cu118, torchaudio 2.0.2+cu118 and
triton 2.0.0. The complete official requirements install then failed because
`aidisdk==0.18.0` could not be found on the configured public indexes. Do not
replace it with aidisdk 1.x: that is not an equivalent pinned dependency.

A text search of the pinned official source found aidisdk only in requirements.txt,
with no code reference. The released frozen-model inference route was inspected:
`eval_tools/senna_plan_cmd_eval_multi_img.py`, `data_tools/senna_qa_utils.py`,
`llava.model.builder.load_senna_pretrained_model`, `llava.senna.senna_llava_llama`,
the Senna architecture, CLIP encoder, multimodal projector and supporting
conversation/image utilities. This route does not call the VLM training or
service scripts. The generic builder also has optional paths not used by the
released Senna loader; their common dependencies are retained conservatively.

We now use a **candidate inference-only projection** rather than claim the full
export is installable unchanged. It supports frozen Senna-VLM inference, not VLM
training, distributed training, annotation generation or service deployment.
No model logic, weights, prompts, generation settings or official version pins
are changed. This is an explicit environment deviation requiring import and
inference validation, not an exact recreation of the authors' full environment.

## Provenance and omissions

`configs/senna-inference-packages.json` selects 37 runtime packages. The generator
`python3 -m src.senna_requirements` checks the original requirements SHA-256 against
our upstream lock and copies exact original `==` pins for each selected package.
It rejects unknown packages, non-exact/duplicate pins and duplicate selections.
It writes both the install file and a JSON audit listing all 37 included and
130 excluded pins, so omissions are reviewable rather than silent.

Excluded groups include the unavailable aidisdk, DeepSpeed/VLM training and
training-only tools, Ray/services, cloud SDKs, plotting/annotation utilities and
their unrelated dependencies. The pinned upstream source remains unchanged.
Future dataset/cache utilities may require their own documented profile additions;
this profile alone does not establish dataset readiness.

Before retry, public PyPI release metadata was checked for all 34 selected
non-PyTorch packages. Their default Linux/Python 3.10 dependency requirements
are satisfied by the selected pins. The three torch-family packages were
successfully installed in the returned HPC log. These checks do not establish
import success or CUDA operation. Runtime package availability/builds still need
the returned HPC result; no dependency resolver or GPU test ran locally.

The original torch-first step installed newest unpinned transient dependencies,
including NumPy 2.2.6. The new single profile resolution pins NumPy to upstream
1.26.4, Pillow to 10.3.0, and the remaining runtime dependencies to their official
versions before imports. Bootstrap Python/pip/setuptools/wheel remain separate
from the inference export. Package freezes and explicit Conda listings capture
what was actually resolved.

## Resume the reviewed partial environment

Use the existing prefix, preserving the successful bootstrap and downloaded
wheels. The default remains to refuse an existing prefix. For this reviewed
partial install, run directly with explicit `CMPE249_RESUME_SENNA=1`:

```bash
CMPE249_RESUME_SENNA=1 bash scripts/environments/setup_senna.sh
```

Resume requires a Conda history file, a working Python 3.10 interpreter and
exact installed versions of all three torch-family packages. It logs the
pre-existing state, then resolves the profile in place. No deletion, environment
recreation or model-weight download occurs. If the guard fails, preserve the
prefix and return its error rather than forcing a retry.

Generated provenance artifacts under `$CMPE249_ARTIFACT_ROOT/environments`:

- `senna-inference.requirements.txt`
- `senna-inference.requirements.audit.json`

The probe checks every selected installed version, imports the actual
`SennaLlavaLlamaForCausalLM` class as well as loader/helper modules, tests a CUDA
operation and NumPy↔torch interoperability, and runs pip check/freeze.
Require `SENNA_IMPORTS_OK`, exactly one visible GPU and SLURM COMPLETED/exit 0:0.
Even success does not establish checkpoint loading or Senna prediction accuracy.

Installation now ends with SENNA_PACKAGES_OK, package metadata and pip checks;
this mode performs no model/torch imports or GPU initialization. It runs without
SLURM and logs to `logs/senna-install-<UTC>-<pid>.log` under the artifact root.
Only the separate `scripts/hpc/validate_senna.sbatch` job tests imports and CUDA.
See [environment execution](environments.md) for validation submission commands.
