# Literature and State-of-the-Art Survey

## Lightweight Exposure Alignment for VLM-Guided End-to-End Autonomous Driving

**Survey date:** September 8, 2026  
**Scope:** Recent work from 2023-2026 on vision-language-guided end-to-end autonomous driving, with emphasis on high-level decision interfaces, low-level trajectory planning, decision-planning consistency, and train-inference mismatch.

## 1. Problem Context

The project proposal studies a specific interface failure in modular vision-language-guided driving. In the original Senna pipeline, a vision-language model (Senna-VLM) predicts a discrete high-level meta-action, such as accelerating, decelerating, keeping speed, turning, or changing lanes. A downstream end-to-end planner (Senna-E2E) converts that decision and the perceived scene into a numerical trajectory. The important mismatch is that the planner is trained with ground-truth meta-actions but receives VLM-predicted meta-actions at deployment. The Senna authors state this training/inference distinction directly [1]. Prediction errors therefore move the planner away from the conditioning distribution seen in training.

The proposed project asks whether a lightweight supervised intervention can reduce this mismatch: cache Senna-VLM predictions, then train the planner using predicted, mixed, scheduled, or confidence-aware meta-action conditioning. This is narrower than building a new driving VLM or performing closed-loop reinforcement learning (RL). The most relevant literature consequently falls into four groups:

1. **The modular baseline:** Senna establishes the VLM-to-planner interface and its train-inference mismatch.
2. **Explicit decision-planning alignment:** Senna-2, DriveMA, and RDA-Driver introduce consistency objectives and, in the two newest systems, RL-based alignment.
3. **Training-only VLM supervision or better upstream decisions:** VLM-AD and RAD show how cached VLM-derived signals or improved meta-action predictions can benefit driving without solving downstream exposure robustness directly.
4. **Alternative system designs:** DriveVLM and EMMA either combine learned and conventional planners or collapse multiple outputs into a unified multimodal model.

## 2. Summary of Recent Papers and Models

| Work | Year and status | Decision/planning design | Training or alignment mechanism | Main reported result | Relevance to this project |
|---|---|---|---|---|---|
| **Senna** [1] | 2024, arXiv | Senna-VLM emits natural-language meta-actions; Senna-E2E generates trajectories | Three-stage VLM training; E2E planner receives ground-truth decisions during training | DriveX pretraining plus nuScenes fine-tuning reduces average planning error by 27.12% and collision rate by 33.33% relative to no pretraining | Direct baseline and source of the train-inference conditioning mismatch |
| **Senna-2** [2] | 2026, arXiv preprint | VLM, decision adapter, and diffusion-based E2E planner | Driving pretraining, open-loop consistency alignment, then closed-loop hierarchical RL | Reports +19.3% decision-planning F1, -5.7% open-loop FDE, and -30.6% at-fault collision rate versus its cited baselines | Closest SOTA; validates consistency as a target but uses substantially more complex alignment |
| **DriveMA** [3] | 2026, arXiv preprint | A driving VLA emits verifiable meta-actions followed by trajectories | Action-centric pretraining, meta-action-conditioned SFT, and turn-level credit-assignment RL | Reports 8.060 RFS with a 2B model and 98.79% language-action consistency for its full reward variant | Closest independent evidence that trajectory-verifiable meta-actions are effective; also shows the marginal gain from supervised meta-action conditioning before RL |
| **RDA-Driver** [4] | 2024, arXiv | Multimodal LLM jointly generates chain-of-thought reasoning and planning decisions | Explicit reasoning-decision alignment constraint during end-to-end training | Reports 0.80 L2 planning error and 0.32 collision rate on nuScenes | Shows that intermediate semantic outputs require explicit coupling to executed decisions, though it aligns reasoning rather than predicted conditioning distributions |
| **VLM-AD** [5] | 2025, CoRL | A conventional E2E driving model is augmented with VLM-generated reasoning and action labels during training | GPT-4o annotations supervise auxiliary text-alignment and action-classification heads; no VLM at inference | Improves open-loop nuScenes planning/collision metrics and closed-loop CARLA route completion/driving score across several E2E backbones | Strong precedent for caching VLM outputs and using them only as inexpensive supervised training signals |
| **RAD** [6] | 2025, arXiv | Retrieval-augmented VLM predicts high-level meta-actions from nuScenes scenes | Retrieval pipeline plus VLM fine-tuning for spatial and bird's-eye-view understanding | Improves match accuracy, F1, and the authors' aggregate score over evaluated baselines | Attacks upstream meta-action error; complementary to, but different from, training the planner to tolerate residual errors |
| **DriveVLM / DriveVLM-Dual** [7] | 2024, arXiv | VLM performs scene description, analysis, and hierarchical planning; Dual variant fuses it with a conventional AD stack | Supervised hierarchical reasoning/planning and hybrid system integration | Reports gains on nuScenes and SUP-AD and a production-vehicle deployment | Motivates separating semantic reasoning from precise control, but does not directly study exposure to erroneous intermediate decisions |
| **EMMA** [8] | 2025, TMLR | A unified multimodal model maps camera data and textual context to trajectories, objects, and road graphs in a shared language space | Multitask co-training across planning, detection, and road-graph generation | Reports SOTA motion planning on nuScenes and competitive Waymo results | Represents the opposite design choice: remove the explicit VLM-to-planner boundary instead of hardening it |

The numeric results above are not directly comparable across rows. The papers use different datasets, horizons, planners, collision definitions, closed-loop simulators, and composite scores. They are best interpreted as evidence for design choices rather than as a single leaderboard.

## 3. Detailed Review

### 3.1 Senna: Bridging Large Vision-Language Models and End-to-End Autonomous Driving

Jiang et al. introduce a two-system architecture that assigns semantic reasoning and numerical trajectory generation to different model classes [1]. Senna-VLM consumes surround-view imagery and text context and produces structured natural-language meta-actions. A meta-action encoder converts these decisions into features used by Senna-E2E, an extension of VADv2, to generate the final trajectory. This division is motivated by the observation that large VLMs offer commonsense and long-tail reasoning but are weak at exact numerical output, whereas specialized E2E planners are well suited to trajectory regression.

Senna is the essential baseline for the proposed study because the paper explicitly states that Senna-E2E receives ground-truth planning decisions during training and Senna-VLM predictions during inference. Thus, even if the marginal decision accuracy of the VLM is high, the downstream planner is evaluated under a corrupted or shifted conditional input distribution. The original work concentrates on improving VLM scene understanding, scalable planning-oriented question-answer data, and cross-domain pretraining; it does not isolate the planner's sensitivity to predicted meta-actions or compare oracle-conditioned and prediction-conditioned planner training.

**Implication.** Reproducing Senna with frozen cached VLM predictions creates a well-defined baseline. The key comparisons should report both oracle-conditioned performance and deployment-conditioned performance so that the cost of the interface mismatch is visible.

### 3.2 Senna-2: Aligning VLM and End-to-End Driving Policy for Consistent Decision Making and Planning

Senna-2 directly names decision-planning inconsistency as a system-level problem [2]. Its architecture contains a Qwen2.5-VL-3B decision model, a decision adapter, and a diffusion-based E2E planner. The adapter combines hidden VLM tokens with learned embeddings for discrete speed and direction categories. A kinematic mapping function also projects planned trajectories back into meta-action classes, allowing the model to test whether its low-level motion agrees with the VLM's high-level intent.

Training proceeds in three stages. First, the VLM and E2E components are pretrained and the adapter is learned while the VLM is frozen. Second, open-loop alignment uses the trajectory-to-decision projection as an explicit consistency signal and selectively refines inconsistent samples. Third, hierarchical RL in 3D Gaussian Splatting environments improves closed-loop safety and efficiency. The paper reports a 19.3% F1 improvement in decision-planning consistency, a 5.7% reduction in open-loop final displacement error (FDE), and a 30.6% reduction in closed-loop at-fault collision rate.

This is the closest state of the art to the proposal, but it does not make the proposed study redundant. Senna-2 changes the architecture, introduces a richer adapter and diffusion planner, uses explicit consistency selection, and culminates in online hierarchical RL. Its ablations also show a tradeoff: Stage 1 alone gives the lowest open-loop FDE, while later alignment stages improve consistency and closed-loop performance. That result argues for evaluating consistency, trajectory accuracy, and robustness together rather than assuming they move in lockstep.

**Implication.** The proposed trajectory-to-meta-action consistency metric is well supported. A lightweight study can ask how much of Senna-2's alignment benefit is obtainable solely by matching the planner's training-time conditioning distribution to deployment.

### 3.3 DriveMA: Driving Vision-Language-Action Models with Verifiable Meta-Actions

DriveMA independently converges on compact, trajectory-verifiable meta-actions as a useful language-action interface [3]. Instead of relying on verbose chain-of-thought text, it derives longitudinal and lateral action labels from expert trajectories. The generated trajectory can be projected back to an action label using deterministic rules, enabling direct measurement and reward of language-action consistency.

The supervised portion has two stages: action-centric pretraining and meta-action-conditioned planning fine-tuning. The later RL stage assigns rewards separately to meta-action and trajectory turns, combining trajectory quality, meta-action correctness, and consistency. The ablation is especially informative for this project. Relative to direct trajectory supervised fine-tuning (SFT), meta-action SFT improves the reported Rater Feedback Score from 7.741 to 7.804 and reduces 5-second average displacement error from 3.065 to 2.802. Action-centric pretraining further raises the score to 7.893. Full turn-level RL reaches 8.060 and raises language-action consistency to 98.79%.

DriveMA therefore shows both that supervised meta-action conditioning provides value and that explicit RL consistency optimization can add more. However, it does not isolate the exact Senna-style question of whether the downstream trajectory generator should be trained on oracle labels, its own model's predicted labels, or a controlled mixture of the two.

**Implication.** Meta-action verifiability makes the proposed supervised robustness study measurable. DriveMA's predicted-versus-oracle meta-action analyses also motivate reporting a planner's performance under both conditions, not just its end-to-end average.

### 3.4 RDA-Driver: Making Large Language Models Better Planners with Reasoning-Decision Alignment

RDA-Driver addresses a related mismatch between generated chain-of-thought reasoning and the consequent driving decision [4]. It uses a multimodality-augmented LLM to produce reasoning and planning outputs together and adds an alignment constraint that links paired reasoning steps to planning results. Redesigned chain-of-thought annotations are intended to improve both scene understanding and the faithfulness of subsequent decisions. The authors report 0.80 L2 error and 0.32 collision rate on nuScenes, along with results on DriveLM-nuScenes.

The paper is conceptually important because it rejects the assumption that an interpretable intermediate output automatically governs downstream behavior. Its mismatch, however, is semantic reasoning versus decision, rather than oracle meta-action conditioning versus predicted meta-action conditioning. It also trains a joint language planner rather than hardening a fixed VLM plus downstream planner interface.

**Implication.** Decision-planning consistency should be treated as a first-class objective and metric, but the proposed project can test a simpler causal mechanism: conditioning distribution shift.

### 3.5 VLM-AD: End-to-End Autonomous Driving through Vision-Language Model Supervision

VLM-AD uses a VLM as an offline teacher rather than as an inference-time module [5]. During dataset preparation, GPT-4o receives a front-view image with the expert future trajectory projected onto it and generates free-form reasoning plus structured action annotations. Auxiliary text-alignment and action-classification heads then supervise standard E2E driving backbones. The VLM is not fine-tuned and is not required during deployment. The method improves planning and collision metrics on nuScenes for UniAD, VAD, and SparseDrive variants, and improves route completion and driving score in CARLA Town05.

This is strong evidence for the feasibility of the proposal's cache-once design. It demonstrates that VLM-derived information can be materialized offline and reused as a supervised signal, keeping inference latency and repeated training cost low. Nevertheless, the role of the VLM is different: its annotations enrich internal representations, while the deployed planner does not consume potentially erroneous VLM decisions. VLM-AD therefore avoids the interface mismatch rather than training robustness to it.

**Implication.** Cached Senna-VLM predictions are a defensible experimental artifact. The experiment should version the cache, store confidence/logit information where available, and ensure every conditioning strategy uses the identical cached predictions.

### 3.6 RAD: Retrieval-Augmented Decision-Making of Meta-Actions with Vision-Language Models

RAD focuses on the upstream half of the interface [6]. It identifies inadequate spatial perception and hallucination as causes of unreliable VLM meta-actions, then uses a three-part retrieval-augmented pipeline (embedding, retrieval, and generation) plus nuScenes-derived fine-tuning to improve meta-action decisions. Its evaluation emphasizes decision match accuracy and F1 rather than downstream trajectory quality.

RAD and exposure alignment address different failure modes. RAD attempts to lower the upstream prediction error rate; exposure alignment attempts to reduce the downstream cost of whatever errors remain. Better meta-action accuracy alone does not guarantee robustness because rare but systematic errors can still cause large trajectory deviations, and a planner trained only on oracle actions may overreact to a plausible but incorrect command.

**Implication.** Upstream decision quality and downstream decision sensitivity should be reported separately. Confidence-aware conditioning is particularly well motivated if confidence is calibrated; otherwise entropy or top-two margin should be treated only as heuristics.

### 3.7 DriveVLM and DriveVLM-Dual

DriveVLM organizes VLM reasoning into scene description, scene analysis, and hierarchical planning [7]. Because VLMs have spatial-reasoning and computational limitations, DriveVLM-Dual combines the VLM-based system with a conventional autonomous-driving stack. The authors evaluate on nuScenes and a proprietary SUP-AD dataset and report deployment on a production vehicle.

This architecture reinforces the logic behind Senna's division of labor: semantic models are useful for long-tail understanding, while specialized planners remain important for precise motion. However, hierarchical interfaces create intermediate predictions whose errors can propagate. DriveVLM-Dual mitigates this through system fusion, not through controlled exposure of a downstream planner to the VLM's empirical prediction distribution.

**Implication.** Interface robustness is a general concern beyond Senna. A successful lightweight conditioning method could transfer to other hierarchical or dual-system driving stacks.

### 3.8 EMMA: End-to-End Multimodal Model for Autonomous Driving

EMMA explores the opposite architectural extreme [8]. Built on a multimodal large-model foundation, it represents navigation commands, ego state, trajectories, 3D objects, and road-graph elements in a shared language space. Task-specific prompts allow one model to generate multiple driving outputs, and multitask co-training improves planning, detection, and road-graph tasks. The current paper reports state-of-the-art motion-planning results on nuScenes and competitive results on Waymo benchmarks.

A unified model can reduce explicit handoff errors because there is no separate frozen VLM prediction passed into an independently trained planner. It also sacrifices some of the modularity, computational economy, and diagnostic clarity of Senna. For a course project with limited compute, retraining or reproducing a generalist multimodal model is much less feasible than fine-tuning a downstream planner.

**Implication.** Exposure alignment is most valuable when a modular architecture is retained for cost, interpretability, or component reuse. EMMA is a useful architectural comparator, not a practical experimental baseline for this project.

## 4. State-of-the-Art Synthesis

### 4.1 What the recent literature establishes

- **A semantic-to-trajectory interface is useful but not self-enforcing.** Senna, RDA-Driver, Senna-2, and DriveMA all provide evidence that a high-level statement can disagree with the actual motion unless the connection is trained or checked explicitly.
- **Trajectory-verifiable meta-actions are emerging as a strong interface.** Senna-2 and DriveMA both convert trajectories back into discrete decisions. This supports the proposal's kinematic consistency evaluator and makes controlled error injection interpretable.
- **Alignment improves more than open-loop displacement alone can reveal.** Senna-2's training-stage tradeoffs and DriveMA's consistency ablations show why FDE/ADE, collision measures, and decision-following metrics must be reported together.
- **The strongest direct alignment systems now use RL.** Senna-2 uses hierarchical closed-loop RL, while DriveMA uses turn-level credit-assignment RL. These approaches improve consistency but add environments, reward design, rollouts, and substantially more training complexity.
- **Offline VLM signals are viable.** VLM-AD shows that VLM outputs can be generated once and used as auxiliary supervision without retaining the VLM at inference. This supports the compute assumptions in the proposal.
- **Improving the VLM is complementary, not sufficient.** RAD improves meta-action prediction but does not answer how a planner behaves under remaining errors.

### 4.2 Closest SOTA and remaining gap

As of the survey date, **Senna-2** is the closest direct model for VLM-to-E2E decision-planning consistency, and **DriveMA** provides the strongest independent meta-action-based alignment evidence. Both use explicit alignment machinery and RL for their best results. The reviewed literature does not present a focused Senna ablation that holds the VLM fixed and compares:

1. ground-truth-only planner conditioning;
2. cached predicted-only conditioning;
3. a fixed random mixture of ground-truth and predicted decisions;
4. a curriculum that increases predicted-decision exposure; and
5. a confidence-aware mixture.

That gap is the clearest contribution opportunity. The novelty should be stated conservatively: the project does not introduce decision-planning consistency as a new problem, because Senna-2 and DriveMA explicitly optimize it. Instead, it isolates **deployment-distribution exposure during supervised downstream training** as a low-compute treatment and measures how much robustness it provides relative to stronger alignment methods.

## 5. Recommended Experimental Framing

### 5.1 Core hypotheses

- **H1:** Training with some cached Senna-VLM predictions improves deployment-conditioned trajectory and consistency metrics relative to ground-truth-only conditioning.
- **H2:** Mixed or scheduled conditioning preserves more oracle-conditioned accuracy than predicted-only conditioning.
- **H3:** Exposure-trained planners degrade more gradually as injected meta-action error increases.
- **H4:** Confidence-aware conditioning helps only when the VLM confidence signal is meaningfully calibrated; otherwise a simple schedule may be more reliable.

### 5.2 Minimum comparison matrix

Use the same planner initialization, training examples, optimization budget, and frozen VLM prediction cache for every row.

| Training condition | Evaluation with ground-truth actions | Evaluation with natural VLM predictions | Evaluation with injected errors |
|---|---:|---:|---:|
| Ground-truth only | Required | Required | Required |
| Predicted only | Required | Required | Required |
| Fixed mixture | Required | Required | Required |
| Scheduled mixture | Required | Required | Required |
| Confidence-aware mixture | Required if implemented | Required if implemented | Required if implemented |

The paired evaluation columns separate three phenomena: loss of clean/oracle capability, gain under realistic deployment inputs, and robustness to controlled corruption.

### 5.3 Metrics

- **Trajectory quality:** ADE and FDE at the same horizons used by the selected Senna evaluation configuration.
- **Safety:** the repository's collision-related metrics, reported with their exact definitions.
- **Decision-planning consistency:** macro-F1 or per-class F1 between the conditioning meta-action and the action recovered from the generated trajectory. Macro averaging is important if action classes are imbalanced.
- **Upstream decision quality:** accuracy and per-class F1 of Senna-VLM predictions against ground-truth meta-actions.
- **Robustness curve:** each trajectory/safety metric versus injected meta-action error rate. Report area under the degradation curve or the slope over a prespecified error interval in addition to individual points.
- **Confidence analysis:** reliability diagram or expected calibration error before treating probability or entropy as a trustworthy gating signal.

### 5.4 Threats to validity

- A trajectory-to-action rule can hide ambiguity near decision thresholds; thresholds should be fixed before comparing methods and sensitivity-tested.
- Random label flips may not resemble the structured confusions made by a real VLM. Include both natural VLM errors and synthetic corruption, and consider sampling corruptions from the empirical confusion matrix.
- If predicted and ground-truth actions are usually identical, an unstratified mixture changes few samples. Report the replacement rate and the rate of actually changed labels separately.
- Overall ADE/FDE can conceal failures in rare action classes. Report per-class consistency and performance, especially for turns, lane changes, and stops.
- Open-loop improvements do not guarantee closed-loop safety. Conclusions should remain scoped to the available evaluation unless a closed-loop simulator is used.
- Confidence gating can preferentially expose easy examples. Compare it with a mixture matched for the same number of predicted-action substitutions.

## 6. Conclusion

Recent work has moved from merely adding language to driving systems toward verifying and optimizing whether semantic decisions are actually executed. Senna establishes the modular decision-to-trajectory pipeline but trains its planner with oracle decisions. Senna-2 and DriveMA show that explicit consistency alignment, especially with RL, can improve decision following and safety. RDA-Driver demonstrates a similar alignment need between reasoning and decisions, while VLM-AD confirms that cached VLM-derived supervision can be used economically. RAD improves upstream decisions, and DriveVLM and EMMA illustrate alternative hybrid and unified architectures.

The proposal occupies a useful middle ground. It retains Senna's interpretable, computationally feasible modular design and asks whether supervised exposure to the exact deployment-time meta-action distribution can recover part of the benefit of much heavier alignment pipelines. The strongest contribution will be a controlled measurement of the oracle-to-predicted conditioning gap, backed by robustness curves and decision-planning consistency metrics, rather than a claim to replace full closed-loop alignment.

## References

1. Bo Jiang et al. [**Senna: Bridging Large Vision-Language Models and End-to-End Autonomous Driving**](https://arxiv.org/abs/2410.22313). arXiv:2410.22313, 2024.
2. Yuehao Song et al. [**Senna-2: Aligning VLM and End-to-End Driving Policy for Consistent Decision Making and Planning**](https://arxiv.org/abs/2603.11219). arXiv:2603.11219, 2026.
3. Weicheng Zheng et al. [**DriveMA: Driving Vision-Language-Action Models with Verifiable Meta-Actions**](https://arxiv.org/abs/2605.31271). arXiv:2605.31271, 2026.
4. Zhijian Huang et al. [**Making Large Language Models Better Planners with Reasoning-Decision Alignment**](https://arxiv.org/abs/2408.13890). arXiv:2408.13890, 2024.
5. Yi Xu et al. [**VLM-AD: End-to-End Autonomous Driving through Vision-Language Model Supervision**](https://arxiv.org/abs/2412.14446). CoRL 2025; arXiv:2412.14446.
6. Yujin Wang et al. [**RAD: Retrieval-Augmented Decision-Making of Meta-Actions with Vision-Language Models in Autonomous Driving**](https://arxiv.org/abs/2503.13861). arXiv:2503.13861, 2025.
7. Xiaoyu Tian et al. [**DriveVLM: The Convergence of Autonomous Driving and Large Vision-Language Models**](https://arxiv.org/abs/2402.12289). arXiv:2402.12289, 2024.
8. Jyh-Jing Hwang et al. [**EMMA: End-to-End Multimodal Model for Autonomous Driving**](https://arxiv.org/abs/2410.23262). TMLR, 2025; arXiv:2410.23262.
