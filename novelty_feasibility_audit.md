# Novelty and Feasibility Audit

## Lightweight Exposure Alignment for VLM-Guided End-to-End Autonomous Driving

**Audit date:** September 8, 2026

**Audit type:** Pre-experiment novelty, red-ocean, and execution-risk review

**Evidence reviewed:** This repository's `README.md` and `literature_sota_survey.md`; the Senna, VAD/VADv2, Senna-2, DriveMA, SimLingo, and LinkVLA papers or official repositories; scheduled sampling and DAgger; and work on nuScenes open-loop evaluation.

## 1. Executive Verdict

**Recommendation: conditional go, with a narrower claim and an immediate implementation gate.**

The project is suitable and reasonably distinctive for a course research project, but it is not a novel learning algorithm. Mixing ground-truth and model-predicted conditioning is closely related to scheduled sampling, DAgger-style expert/policy mixtures, and ordinary training under corrupted or deployment-distribution inputs. The autonomous-driving subfield is also crowded with 2025-2026 work on language-action or decision-planning alignment. In particular, Senna-2, DriveMA, SimLingo, ORION, and LinkVLA substantially occupy the broad claim that high-level language or meta-actions should be aligned with low-level trajectories.

The defensible contribution is instead a **controlled systems study**: hold the VLM and planner architecture fixed, isolate the oracle-to-predicted meta-action conditioning gap, and measure the clean-performance/robustness tradeoff of inexpensive supervised exposure policies. The strongest result would be a careful diagnosis of *when* predicted-action exposure helps, not a claim that mixed or scheduled conditioning is new.

The plan is **not yet feasible as written** because the public Senna repository currently exposes Senna-VLM code and weights but not an identifiable Senna-E2E implementation or checkpoint. The linked VAD repository includes a VADv2 head and configuration, but recreating the Senna adapter and training path is integration work, not direct baseline reuse. The repository being audited also contains no experiment code, environment lockfile, dataset manifest, cached predictions, or reproduced baseline.

### Scorecard

Scores use 1 = weak/high risk and 5 = strong/low risk.

| Dimension | Score | Assessment |
|---|---:|---|
| Novelty of the broad problem | 2/5 | Decision-planning and language-action alignment are now crowded topics. |
| Novelty of the proposed method | 1.5/5 | Predicted, mixed, and scheduled conditioning are established ideas in adjacent fields. |
| Novelty of the controlled experiment | 3.5/5 | A frozen-interface, matched-budget ablation on the original Senna-style mismatch remains useful and appears under-isolated in the reviewed work. |
| Distinctiveness as a course project | 4/5 | The question is focused, testable, and more diagnostic than another end-to-end VLM benchmark. |
| Feasibility as currently written | 2/5 | The exact downstream baseline is not publicly packaged; data, GPU, and integration assumptions are unverified. |
| Feasibility after the recommended scope cut | 4/5 | A frozen-feature/planner-head study with three core conditions is realistic if the readiness gate passes. |
| Red-ocean exposure | 4/5 risk | The area is saturated; generic alignment framing will be hard to distinguish. |

## 2. What Is and Is Not Novel

### 2.1 Ideas that cannot support a novelty claim

1. **Train/inference exposure mismatch is established.** Scheduled sampling explicitly replaces some ground-truth conditioning tokens with model-generated tokens and schedules that replacement over training [1]. The proposal's fixed mixture and curriculum are direct conceptual analogues, even though the Senna interface is a single upstream decision rather than a recurrent decoder state.

2. **Expert/policy mixing is established.** DAgger trains on states reached by a mixture of expert and learned policies and decays the expert proportion over iterations [2]. The proposed method is not DAgger because it neither rolls out the planner nor aggregates visited states, but “gradually expose a learner to its deployment inputs” is not new.

3. **Decision-planning consistency is already an explicit research target.** Senna-2 presents a three-stage consistency-oriented training recipe with open-loop alignment and closed-loop hierarchical reinforcement learning [3]. DriveMA uses trajectory-verifiable meta-actions, meta-action-guided supervised training, and turn-level RL [4]. SimLingo aligns language and actions in closed-loop driving [5], and LinkVLA structurally couples language and action through a shared codebook and a trajectory-to-language objective [6].

4. **Meta-actions as an interface are established.** Senna introduced the VLM-to-E2E meta-action interface [7], and DriveMA argues directly for concise, trajectory-verifiable meta-actions [4].

5. **Confidence-aware mixing by itself is weak novelty.** Confidence gating is a standard selective-training idea. Here it is additionally underspecified: Senna's released evaluation script performs deterministic text generation and records parsed answers/failures, not a calibrated confidence value [8]. Extracting comparable sequence likelihoods and calibrating them would be a separate contribution, not a free experimental condition.

### 2.2 The contribution that remains defensible

The reviewed work does not clearly provide the following controlled experiment on the same frozen Senna-style interface:

- train the same downstream planner with oracle, natural predicted, and matched mixtures of meta-actions;
- keep upstream predictions, data, initialization, and optimization budget fixed;
- evaluate both oracle-conditioned and deployment-conditioned performance;
- separate natural VLM errors from synthetic counterfactual commands; and
- quantify whether robustness gains cost clean/oracle controllability.

This supports a conservative novelty statement:

> We isolate the effect of deployment-distribution meta-action exposure in a frozen VLM-to-planner interface and measure its trajectory, safety, and controllability tradeoffs under natural and controlled upstream errors.

It does **not** support statements such as “we introduce exposure alignment,” “we solve decision-planning inconsistency,” or “we propose a novel scheduled-conditioning algorithm.”

### 2.3 Nearest-neighbor overlap

| Prior work | What it already covers | Residual space for this project |
|---|---|---|
| Scheduled Sampling [1] | Ground-truth/generated input mixing and curricula | Apply and diagnose the idea at a frozen semantic-to-trajectory interface, without claiming algorithmic novelty |
| DAgger [2] | Expert/learner mixture and deployment-state exposure | Offline interface corruption without rollouts or dataset aggregation; explicitly distinguish the two |
| Senna [7] | The modular VLM meta-action to E2E planner and the relevant oracle/predicted boundary | Directly measure the boundary's exposure gap and downstream sensitivity |
| Senna-2 [3] | Explicit open- and closed-loop decision/planning alignment | Test how much a much cheaper supervised intervention recovers under a fixed older architecture |
| DriveMA [4] | Verifiable meta-actions, supervised conditioning, consistency rewards, and RL | Compare oracle versus frozen upstream predictions and isolate natural-error exposure |
| SimLingo [5] / LinkVLA [6] | Language-action alignment through data or architecture | A modular robustness study rather than a new unified VLA model |

## 3. The Central Scientific Risk: Contradictory Supervision

The proposal currently treats predicted meta-actions as shifted inputs, but an incorrect meta-action is also a **semantically conflicting instruction**.

Let `z_gt` be the action derived from the expert trajectory, `z_pred` the VLM action, and `y_gt` the expert trajectory. On VLM-error samples, training the planner on `(scene, z_pred) -> y_gt` asks it to produce a decelerating trajectory while, for example, being conditioned on `ACCELERATE`. This creates two incompatible notions of success:

- **Expert/safety fidelity:** remain close to `y_gt`, which may require ignoring `z_pred`.
- **Command fidelity:** generate a trajectory consistent with `z_pred`, which may move away from `y_gt` and can be unsafe when the upstream command is wrong.

Consequently, improved ADE/FDE after predicted-only training may mean that the planner learned to ignore the VLM, not that alignment improved. Conversely, higher decision-planning consistency may mean unsafe obedience to an erroneous command. A single aggregate “consistency” score cannot resolve this.

This is more than an evaluation detail: it determines what the method is optimizing. The study should stratify every result by whether `z_pred = z_gt` and explicitly report the tradeoff below.

| Upstream state | Desired diagnostic | Interpretation |
|---|---|---|
| `z_pred = z_gt` | Expert trajectory quality plus command consistency | Tests normal in-distribution use of the interface |
| `z_pred != z_gt` | Expert trajectory quality, safety proxy, and supplied-command consistency reported separately | Reveals whether the planner obeys, discounts, or safely overrides the VLM |
| Synthetic alternative command | Change in trajectory relative to the original command, without pretending the expert trajectory is the correct target for both | Tests controllability and sensitivity, not imitation accuracy |

This conflict can become the project's most interesting analysis if stated upfront. It also makes a negative result publishable as a course finding: exposure training may reduce the deployment gap by collapsing dependence on the semantic interface.

## 4. Red-Ocean and Saturation Risks

### 4.1 High-risk positioning

- **“VLM for autonomous driving.”** This label is heavily saturated and invites comparison with much larger unified VLA systems and closed-loop benchmarks.
- **“Language-action alignment.”** SimLingo, ORION, Senna-2, DriveMA, and LinkVLA already make alignment a central contribution [3-6, 9]. A generic alignment title will make the project look late.
- **“A new mixed/scheduled training strategy.”** Reviewers familiar with scheduled sampling or imitation learning will see this as a direct adaptation.
- **“Improved nuScenes planning.”** Numerous methods report small ADE/FDE or collision gains. Open-loop nuScenes results have known weaknesses: a simple model using ego state without perception can be competitive on displacement metrics, motivating explicit caution about what those metrics demonstrate [10].
- **“Confidence-aware robustness.”** Without held-out calibration and a matched-exposure control, this can reduce to selecting easy examples and will be difficult to interpret.

### 4.2 How to exit the red ocean

Position the work around **interface failure accounting**, not model superiority:

1. Define an **exposure gap** for each metric: the same ground-truth-trained planner evaluated with `z_gt` versus `z_pred`.
2. Define an **adaptation gain** under `z_pred`, paired with the loss under `z_gt`.
3. Measure **command influence**, such as trajectory change under counterfactual meta-actions, to detect a planner that simply ignores the interface.
4. Break natural errors down by empirical confusion pair and action class instead of reporting only a global average.
5. Use empirical-confusion corruption as the primary synthetic stress test; keep uniform random flips only as a sanity check.
6. Report confidence gating only if confidence can be extracted and calibrated. Match it against a random mixture with the same number of actual label substitutions.
7. Frame the output as a **low-compute Pareto study**: deployment robustness versus oracle performance versus command controllability.

This creates a sharper contribution than “method X beats baseline Y by a small amount.”

## 5. Feasibility Audit

### 5.1 Current repository readiness

The audited repository is at the concept stage. It contains a README and literature survey, but no:

- imported or pinned Senna/VAD code;
- environment or dependency lock;
- nuScenes path/manifest or sample-count check;
- model/checkpoint manifest;
- VLM prediction cache and schema;
- planner-conditioning implementation;
- baseline reproduction log; or
- experiment/evaluation scripts.

That is acceptable at proposal time, but none of the core execution assumptions has yet been demonstrated.

### 5.2 External implementation blockers

**Critical — exact Senna-E2E reuse is unavailable.** As of the audit date, the official Senna repository says it released “code and weight of Senna-VLM” and its visible top-level tree contains VLM/LLaVA data, training, and evaluation folders but no Senna-E2E module [8]. Its evaluation tooling measures meta-action text predictions, not downstream trajectories. The plan therefore cannot simply “use the original Senna architecture as a baseline.”

**High — VADv2 is only a partial substitute.** The official VAD repository provides VADv2 core code as one head file and one configuration intended to be integrated into VADv1 [11]. Reconstructing Senna's meta-action encoder and injection point from the paper is feasible engineering, but it weakens claims of exact reproduction and must be documented as a “Senna-style VADv2 reconstruction.”

**High — training budget may exceed a course allocation.** VAD's official instructions show an eight-GPU training command, while evaluation uses one GPU [12]. The Senna-VLM is a 7B six-view model; its repository describes 24 GB as “limited GPU memory” in the context of LoRA fine-tuning [8]. Caching VLM outputs removes repeated inference, but it does not make full VAD/VADv2 retraining cheap. Five conditions times three seeds would require 15 planner runs before hyperparameter debugging.

**Medium — the cache needs custom work.** The released Senna evaluator uses deterministic generation and saves failed parsed answers plus aggregate metrics [8]. The project needs a new cache that records every sample token, normalized speed/path labels, raw output, model/checkpoint hash, prompt version, and—only if used—well-defined log probabilities.

**Medium — data access is gated.** nuScenes is free for registered non-commercial use, but the team must still confirm account access, download/storage capacity, CAN-bus expansion, exact split generation, and agreement between Senna and VAD sample tokens [13]. The mini split is useful for plumbing only, not final conclusions.

**Medium — open-loop evidence is limited.** nuScenes ADE/FDE and collision metrics do not establish closed-loop safety [10]. A course project can remain open-loop, but the conclusion must say “open-loop robustness proxies” rather than “safer autonomous driving.”

### 5.3 Feasibility by component

| Component | Feasibility | Main condition |
|---|---:|---|
| Run released Senna-VLM inference | Medium | Appropriate GPU, checkpoint access, six-view data, and fixed prompt/parsing |
| Cache hard meta-actions | High after setup | Modify evaluator to save all predictions and metadata |
| Cache calibrated confidence | Low-medium | Extract normalized sequence scores, choose a calibration split, and validate ECE/reliability |
| Reproduce exact Senna-E2E | Low | No packaged public implementation/checkpoint was found |
| Build a Senna-style VADv2 planner | Medium | Nontrivial adapter/injection integration and baseline validation |
| Train five conditions with multiple seeds | Low-medium | Requires frozen features or planner-head-only training and a known GPU budget |
| ADE/FDE and repository collision evaluation | Medium-high | Baseline pipeline and data alignment must first work |
| Decision-planning consistency | Medium | Thresholds and ambiguous near-boundary trajectories must be prespecified |
| Closed-loop safety claims | Low | No closed-loop simulator or rollout plan is currently in scope |

## 6. Recommended Executable Scope

### 6.1 Mandatory readiness gate

Before committing to the five-condition study, require all of the following:

1. Reproduce one published or checkpoint-provided VAD/VADv2 validation result, or document the exact deviation.
2. Produce a versioned Senna-VLM cache for a small split and verify one-to-one sample-token alignment with planner data.
3. Add a meta-action input to the planner and overfit a 32-128-sample subset.
4. Demonstrate that changing only the meta-action changes the generated trajectory in the expected direction on at least a hand-audited test set.
5. Time one training epoch and estimate total GPU-hours and storage from measured values.

If any of steps 1-3 fails early, pivot to a frozen-feature or lightweight trajectory-head experiment. Do not spend the project schedule reconstructing the full unpublished Senna-E2E system.

### 6.2 Core experiment versus stretch goals

**Core, required:**

- ground-truth-only conditioning;
- predicted-only conditioning;
- one fixed mixture chosen before final evaluation;
- at least three seeds for the trainable planner/head;
- evaluation under `z_gt`, natural `z_pred`, and empirical-confusion corruption;
- results stratified by VLM-correct versus VLM-wrong samples; and
- counterfactual command-influence tests.

**Extension if the core finishes:** scheduled mixture.

**Stretch only:** confidence-aware mixture. It should be dropped unless the team has calibrated confidence and a matched-substitution control. Five weakly validated strategies are less valuable than three reproducible ones.

### 6.3 Compute-saving design

Prefer this sequence:

1. Freeze the VLM and cache once.
2. Start from a reproduced VAD/VADv2 checkpoint.
3. Freeze the image backbone and, if possible, the scene encoder.
4. Train only the meta-action adapter and trajectory/planning head.
5. Reuse identical cached scene features across conditions.
6. Run the full matrix only after a small-split experiment shows that the action input has measurable influence.

This changes the research claim from “retrain Senna” to “audit and adapt the Senna-style decision/planner interface,” but it is much more credible under limited compute.

## 7. Experimental Validity Requirements

The following are necessary for an interpretable result:

- **Actual-change rate:** A mixture selects predicted labels on some samples, but the input changes only when `z_pred != z_gt`. Report both the selection rate and actual-change rate. For example, a 50% mixture changes far fewer than 50% of inputs when the VLM is usually correct.
- **Matched training budgets:** Same sample order, optimizer steps, augmentations, initialization policy, and feature cache across conditions.
- **No validation leakage:** Choose mixture schedules, confidence thresholds, and trajectory-to-action thresholds using a development split, then lock them.
- **Class-aware reporting:** Macro-F1, per-action support, and confusion-pair results are needed because turns, stops, and lane changes are rare.
- **Natural and synthetic errors:** Natural errors establish realism; uniform flips establish only a stress-test bound; empirical-confusion sampling is the better middle ground.
- **Threshold sensitivity:** A trajectory-to-meta-action projector can change labels near speed/yaw/lateral thresholds. Prespecify rules and provide a small sensitivity analysis.
- **Uncertainty:** Report per-seed results and confidence intervals or paired bootstrap intervals, not only the best run.
- **Safety language:** Call nuScenes collision outputs “open-loop collision metrics/proxies” and avoid real-world safety claims.
- **Dependency measurement:** Report cache generation time, trainable parameter count, peak GPU memory, per-condition GPU-hours, and cache size. Low compute is part of the claimed value and must be demonstrated.

## 8. Decision and Revised Claim

### Go/no-go decision

**Go** if the team can, within an early time-box, reproduce a VAD/VADv2 baseline, join Senna predictions to the same samples, and prove that the injected meta-action affects planner outputs. Under those conditions, the project has a clear course-level contribution and can yield useful results even if no method wins every metric.

**No-go or pivot** if exact Senna-E2E reproduction remains the dependency, if only a single full training run is affordable, or if the planner ignores the added meta-action. In that case, use a frozen-feature lightweight planner and present the work explicitly as an interface sensitivity study.

### Recommended title

**When Should a Planner Trust Its VLM? A Controlled Exposure Audit of Meta-Action-Conditioned Driving**

### Recommended one-sentence claim

> We quantify the oracle-to-deployment conditioning gap at a frozen VLM-to-planner interface and test whether inexpensive predicted-action exposure improves deployment robustness without erasing command controllability or oracle-conditioned performance.

This wording is novel enough for the actual evidence sought, avoids competition with full VLA and RL systems, and makes the central tradeoff falsifiable.

## References

1. Samy Bengio, Oriol Vinyals, Navdeep Jaitly, and Noam Shazeer. [Scheduled Sampling for Sequence Prediction with Recurrent Neural Networks](https://papers.nips.cc/paper_files/paper/2015/hash/e995f98d56967d946471af29d7bf99f1-Abstract.html). NeurIPS 2015.
2. Stéphane Ross, Geoffrey Gordon, and Drew Bagnell. [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning](https://proceedings.mlr.press/v15/ross11a.html). AISTATS 2011.
3. Yuehao Song et al. [Senna-2: Aligning VLM and End-to-End Driving Policy for Consistent Decision Making and Planning](https://arxiv.org/abs/2603.11219). arXiv, 2026.
4. Weicheng Zheng et al. [DriveMA: Driving Vision-Language-Action Models with Verifiable Meta-Actions](https://arxiv.org/abs/2605.31271). arXiv, 2026.
5. Katrin Renz et al. [SimLingo: Vision-Only Closed-Loop Autonomous Driving with Language-Action Alignment](https://openaccess.thecvf.com/content/CVPR2025/html/Renz_SimLingo_Vision-Only_Closed-Loop_Autonomous_Driving_with_Language-Action_Alignment_CVPR_2025_paper.html). CVPR 2025.
6. Xinyang Wang et al. [Unifying Language-Action Understanding and Generation for Autonomous Driving](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Unifying_Language-Action_Understanding_and_Generation_for_Autonomous_Driving_CVPR_2026_paper.html). CVPR 2026.
7. Bo Jiang et al. [Senna: Bridging Large Vision-Language Models and End-to-End Autonomous Driving](https://arxiv.org/abs/2410.22313). arXiv, 2024; IJCV, 2026.
8. HUST-VL. [Official Senna repository](https://github.com/hustvl/Senna). Repository state reviewed September 8, 2026.
9. Haoyu Fu et al. [ORION: A Holistic End-to-End Autonomous Driving Framework by Vision-Language Instructed Action Generation](https://openaccess.thecvf.com/content/ICCV2025/html/Fu_ORION_A_Holistic_End-to-End_Autonomous_Driving_Framework_by_Vision-Language_Instructed_ICCV_2025_paper.html). ICCV 2025.
10. Jiang-Tian Zhai et al. [Rethinking the Open-Loop Evaluation of End-to-End Autonomous Driving in nuScenes](https://arxiv.org/abs/2305.10430). arXiv, 2023.
11. HUST-VL. [Official VAD/VADv2 repository](https://github.com/hustvl/VAD). Repository state reviewed September 8, 2026.
12. HUST-VL. [VAD training and evaluation instructions](https://github.com/hustvl/VAD/blob/main/docs/train_eval.md). Repository state reviewed September 8, 2026.
13. Motional. [nuScenes dataset](https://www.nuscenes.org/nuscenes). Access information reviewed September 8, 2026.
