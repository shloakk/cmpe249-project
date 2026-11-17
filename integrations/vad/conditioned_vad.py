"""Adapter-only training wrapper for official VAD."""
from mmdet.models import DETECTORS

from .VAD import VAD


@DETECTORS.register_module()
class ConditionedVAD(VAD):
    def __init__(self, *args, train_adapter_only=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.train_adapter_only = train_adapter_only
        if train_adapter_only:
            for parameter in self.parameters():
                parameter.requires_grad = False
            for parameter in self.pts_bbox_head.meta_action_adapter.parameters():
                parameter.requires_grad = True

    def train(self, mode=True):
        if self.train_adapter_only:
            # Keep the frozen released planner deterministic (no dropout or
            # running-stat updates); only the adapter enters training mode.
            super().train(False)
            self.pts_bbox_head.meta_action_adapter.train(mode)
            return self
        return super().train(mode)
