from pydantic import BaseModel
from typing import Optional, List

class PredictionResponse(BaseModel):
    has_pneumothorax: bool
    confidence:       float
    verdict:          str
    overlay_b64:      Optional[str]
    heatmap_b64:      Optional[str]
    scan_id:          int

class ScanHistory(BaseModel):
    id:         int
    filename:   str
    result:     str
    confidence: float
    has_ptx:    bool
    created_at: str

class StatsResponse(BaseModel):
    total:          int
    positive:       int
    negative:       int
    avg_confidence: float