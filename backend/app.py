import json
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ASL Alphabet Recognition API")


session = ort.InferenceSession("asl_mlp.onnx", providers=["CPUExecutionProvider"])

# Load label map
with open("label_map.json") as f:
    label2idx = json.load(f)

idx2label = {v: k for k, v in label2idx.items()}

class InputData(BaseModel):
    keypoints: list  # length = 63

def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

@app.get("/")
def root():
    return {"status": "ASL backend running"}

@app.post("/predict")
def predict(data: InputData):
    x = np.array(data.keypoints, dtype=np.float32).reshape(1, 63)
    logits = session.run(None, {"keypoints": x})[0]
    probs = softmax(logits[0])
    pred = int(np.argmax(probs))

    return {
        "prediction": idx2label[pred],
        "confidence": float(probs[pred])
    }
