"""Strict JSON: absent actuator positions are null, never nonstandard NaN."""
import math
import json
import numpy as np

def serializable(value):
    if isinstance(value,np.ndarray):return serializable(value.tolist())
    if isinstance(value,np.generic):return serializable(value.item())
    if isinstance(value,float) and not math.isfinite(value):return None
    if isinstance(value,dict):return {k:serializable(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [serializable(v) for v in value]
    return value

def dumps(value):return json.dumps(serializable(value),indent=2,allow_nan=False)
