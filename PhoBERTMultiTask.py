import torch
from torch import nn
from transformers import AutoModel

class PhoBERTMultiTask(nn.Module):
    def __init__(self, num_sentiment=3, num_topic=4):
        super().__init__()
        self.phobert = AutoModel.from_pretrained("vinai/phobert-base")
        self.dropout = nn.Dropout(0.1)

    
        self.sentiment_head = nn.Sequential(
            nn.Linear(768, 768),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(768, num_sentiment)
        )

        self.topic_head = nn.Sequential(
            nn.Linear(768, 768),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(768, num_topic)
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.phobert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        pooled = self.dropout(pooled)
        logits_sent = self.sentiment_head(pooled)
        logits_topic = self.topic_head(pooled)
        return logits_sent, logits_topic
