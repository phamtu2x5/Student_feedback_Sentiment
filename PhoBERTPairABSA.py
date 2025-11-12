import torch
from torch import nn
from transformers import AutoModel

class PhoBERTPairABSA(nn.Module):
    """Pair-ABSA model: Predicts sentiment for a specific topic in a sentence"""
    def __init__(self, base_model="vinai/phobert-base", num_cls=4, dropout=0.2):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(base_model)
        hidden_size = self.backbone.config.hidden_size
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size),
            nn.GELU(),
            nn.LayerNorm(hidden_size),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_cls)
        )
    
    def forward(self, input_ids, attention_mask):
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        cls = out.last_hidden_state[:, 0, :]
        logits = self.classifier(cls)
        return logits
