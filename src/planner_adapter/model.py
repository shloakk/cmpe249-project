"""Lightweight residual action adapter, independent of the VAD integration."""
from __future__ import annotations

import torch
from torch import nn


class MetaActionAdapter(nn.Module):
    def __init__(self, output_dim: int, embedding_dim: int = 32):
        super().__init__()
        self.speed_embedding = nn.Embedding(4, embedding_dim)
        self.path_embedding = nn.Embedding(5, embedding_dim)
        self.projection = nn.Sequential(
            nn.Linear(embedding_dim * 2, output_dim),
            nn.ReLU(),
            nn.Linear(output_dim, output_dim),
        )
        # Start at the released VAD behavior and learn a residual.
        nn.init.zeros_(self.projection[-1].weight)
        nn.init.zeros_(self.projection[-1].bias)

    def forward(self, speed_ids: torch.Tensor, path_ids: torch.Tensor) -> torch.Tensor:
        action = torch.cat((
            self.speed_embedding(speed_ids), self.path_embedding(path_ids)
        ), dim=-1)
        return self.projection(action)
