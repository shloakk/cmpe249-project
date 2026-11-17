"""VAD head with a zero-initialized residual meta-action adapter.

Copy beside VAD_head.py and import it from that package's __init__.py. The
released decoder and checkpoint keys remain unchanged; a pre-hook modifies only
the tensor entering ego_fut_decoder.
"""
import hashlib
import json
import random

import torch
from mmcv.runner import force_fp32
from mmdet.models import HEADS
from torch import nn

from .VAD_head import VADHead

SPEED = ("KEEP", "ACCELERATE", "DECELERATE", "STOP")
PATH = ("RIGHT_TURN", "RIGHT_CHANGE", "LEFT_TURN", "LEFT_CHANGE", "STRAIGHT")


class MetaActionAdapter(nn.Module):
    def __init__(self, output_dim, embedding_dim=32):
        super().__init__()
        self.speed = nn.Embedding(len(SPEED), embedding_dim)
        self.path = nn.Embedding(len(PATH), embedding_dim)
        self.projection = nn.Sequential(
            nn.Linear(embedding_dim * 2, output_dim), nn.ReLU(),
            nn.Linear(output_dim, output_dim),
        )
        nn.init.zeros_(self.projection[-1].weight)
        nn.init.zeros_(self.projection[-1].bias)

    def forward(self, speed_ids, path_ids):
        action = torch.cat((self.speed(speed_ids), self.path(path_ids)), dim=-1)
        return self.projection(action)


@HEADS.register_module()
class ConditionedVADHead(VADHead):
    """Released VADHead plus C1/C2/C3/real cached action conditioning."""

    def __init__(self, *args, meta_action_cfg=None, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = meta_action_cfg or {}
        self.meta_condition = cfg.get("condition", "c1").lower()
        self.meta_seed = int(cfg.get("seed", 249))
        self.uniform_probability = float(cfg.get("uniform_probability", 0.0))
        self.action_cache = self._load_cache(cfg.get("cache_path"))
        self.confusions = self._load_confusions(cfg.get("confusion_path"))
        input_dim = self.ego_fut_decoder[0].in_features
        self.meta_action_adapter = MetaActionAdapter(
            input_dim, int(cfg.get("embedding_dim", 32))
        )
        self._meta_ids = None
        self.ego_fut_decoder.register_forward_pre_hook(self._inject_action)

    @staticmethod
    def _load_cache(path):
        cache = {}
        if not path:
            return cache
        with open(path) as handle:
            for line in handle:
                row = json.loads(line)
                cache[str(row["token"])] = row
        return cache

    @staticmethod
    def _load_confusions(path):
        if not path:
            return {}
        with open(path) as handle:
            rows = json.load(handle).get("joint_confusions", [])
        tables = {}
        for row in rows:
            key = (row["gt_speed"], row["gt_path"])
            tables.setdefault(key, []).append((
                (row["pred_speed"], row["pred_path"]), int(row["count"])
            ))
        return tables

    def _rng(self, token):
        digest = hashlib.sha256(f"{self.meta_seed}:{token}".encode()).digest()
        return random.Random(int.from_bytes(digest[:8], "big"))

    def _select(self, token):
        row = self.action_cache.get(str(token))
        if row is None:
            raise KeyError(f"meta-action cache has no token {token}")
        truth = (row["gt_speed"], row["gt_path"])
        if self.meta_condition == "c1":
            return truth
        if self.meta_condition == "real":
            if not row.get("parse_ok"):
                return truth
            return row["pred_speed"], row["pred_path"]
        rng = self._rng(token)
        if self.meta_condition == "c2":
            if rng.random() >= self.uniform_probability:
                return truth
            alternatives = [
                (speed, path) for speed in SPEED for path in PATH
                if (speed, path) != truth
            ]
            return rng.choice(alternatives)
        if self.meta_condition == "c3":
            choices = self.confusions.get(truth)
            if not choices:
                return truth
            return rng.choices(
                [choice for choice, _ in choices],
                weights=[weight for _, weight in choices], k=1,
            )[0]
        raise ValueError(f"unknown meta-action condition: {self.meta_condition}")

    def _inject_action(self, module, inputs):
        if self._meta_ids is None:
            return inputs
        tensor = inputs[0]
        speed_ids, path_ids = self._meta_ids
        residual = self.meta_action_adapter(speed_ids, path_ids).unsqueeze(1)
        return (tensor + residual.to(dtype=tensor.dtype),) + inputs[1:]

    @force_fp32(apply_to=("mlvl_feats", "prev_bev"))
    def forward(self, mlvl_feats, img_metas, prev_bev=None, only_bev=False,
                ego_his_trajs=None, ego_lcf_feat=None):
        if not only_bev:
            selected = [
                self._select(meta.get("sample_idx") or meta.get("token"))
                for meta in img_metas
            ]
            device = mlvl_feats[0].device
            self._meta_ids = (
                torch.tensor([SPEED.index(item[0]) for item in selected], device=device),
                torch.tensor([PATH.index(item[1]) for item in selected], device=device),
            )
        try:
            return super().forward(
                mlvl_feats, img_metas, prev_bev=prev_bev, only_bev=only_bev,
                ego_his_trajs=ego_his_trajs, ego_lcf_feat=ego_lcf_feat,
            )
        finally:
            self._meta_ids = None
