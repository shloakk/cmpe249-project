# Lightweight Exposure Alignment for VLM-Guided End-to-End Autonomous Driving

## Team Members

- Parth Panchal (018333965)
- Shloak Aggarwal (018189938)

## Abstract

Recent autonomous-driving systems such as Senna use a Vision-Language Model (VLM) to predict high-level driving decisions and an end-to-end planner to generate vehicle trajectories. A train-inference mismatch can arise when the planner is trained using ground-truth decisions but receives imperfect VLM predictions during deployment. This project investigates whether lightweight exposure to VLM-predicted decisions during supervised planner training can improve decision-planning consistency and robustness without reinforcement learning or large-scale closed-loop alignment. Using the original Senna architecture as a baseline, we will keep the VLM fixed, cache its predictions, and compare ground-truth, predicted, mixed, scheduled, and confidence-aware planner conditioning strategies. Experiments will use the public Senna codebase and nuScenes-based evaluation, measuring trajectory displacement error, collision-related metrics, decision-planning consistency, and robustness to injected upstream decision errors. The study will assess whether reducing the distribution mismatch at the VLM-to-planner interface provides an effective, computationally feasible alternative to more complex alignment methods.

## Selected Track

VLM-Guided Autonomous Driving
