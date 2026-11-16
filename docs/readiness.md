# Readiness requirements and upstream policy

The HPC smoke test passed: job 116264, COMPLETED, exit 0:0.
Model environment imports remain pending. Environment pinning requires this evidence. Official sources have now been inspected; see [environment setup](environments.md).
Candidate recipes must not be mistaken for tested or fully resolved locks.

0. Local unit tests, shell syntax, current-tree privacy/artifact checks; then
   returned SLURM COMPLETED/exit 0 logs with ENVIRONMENT_SMOKE_OK. Until returned,
   the overall gate is PENDING. Infrastructure failures must be fixed first.
1. Inspect and pin official hustvl/Senna and hustvl/VAD commits. Inspect their
   exact environment instructions. Create environment-senna.yml and a separate
   VAD environment or Apptainer definition using evidenced versions. Require
   successful imports in both environments on one A100, exactly one torch-visible
   GPU and complete version logs. No checkpoint download until storage passes.
2. Full input checks, trusted annotation compatibility/provenance, CAN-bus
   resolution and deterministic 50-sample manifest.
3. Official Senna inference first, then auditable cache for all 50 samples.
4. Development-only confusion estimation with denominators and parse rules.
5. Released VAD checkpoint smoke and full validation before changing architecture.
6. Adapter overfit on 32–128 samples and counterfactual action influence.
7. Measured one-seed pilot before experiment arrays and any three-seed expansion.

Use a reproducible clone script with full SHA pins rather than submodules in
environment setup: this keeps the user-operated HPC `git pull --ff-only` handoff simple and
avoids nested Git initialization. Clone into ignored `upstream/`, refuse dirty
checkouts and verify the checked-out SHA. Do not vendor repositories or resolve
floating HEAD during a run. This is a policy decision, not a claim pins exist.

Later SLURM scripts (dataset validation, cache, baseline, overfit, experiment
arrays, aggregation) are added when their prerequisites pass; do not submit empty jobs.
Every run must log command, commit/dirty state, environment, host, GPU, inputs,
outputs, wall time, peak memory, status and failures. Resume only with matching
configuration/provenance and prevent duplicate expensive jobs.

The historical literature documents retain cited paper claims; the infrastructure setup did not
revalidate those external claims. Their new scope notes supersede earlier
experimental recommendations, not the bibliographic record.
