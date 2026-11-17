# VAD conditioning integration

This is an additive integration against pinned official VAD commit
`1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8`. It does not claim to reproduce
unreleased Senna-E2E code.

`prepare_config.py` verifies that commit, copies one registered head beside the
official `VADHead`, and creates a condition-specific copy of the official Tiny
stage-2 config. The released decoder remains in place. A zero-initialized
residual adapter injects the speed/path embedding immediately before that
decoder, preserving baseline behavior at initialization and existing decoder
checkpoint keys.

Conditions: C1 uses ground truth; C2 samples a different action pair uniformly
at the measured real error rate; C3 samples the empirical joint confusion
distribution; `real` uses cached Senna predictions at evaluation time.
