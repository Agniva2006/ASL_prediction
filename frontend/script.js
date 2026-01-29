const videoElement = document.getElementById("video");
const canvasElement = document.getElementById("canvas");
const canvasCtx = canvasElement.getContext("2d");

const letterEl = document.getElementById("letter");
const confidenceEl = document.getElementById("confidence");

// CHANGE THIS LATER WHEN BACKEND IS DEPLOYED
const API_URL = "https://asl-backend.onrender.com/predict";


// MediaPipe Hands
const hands = new Hands({
  locateFile: (file) =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.6,
  minTrackingConfidence: 0.6,
});

hands.onResults(onResults);

// Camera
const camera = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({ image: videoElement });
  },
  width: 640,
  height: 480,
});

camera.start();

// Extract 63 keypoints
function extractKeypoints(landmarks) {
  const kp = [];
  for (let i = 0; i < 21; i++) {
    kp.push(landmarks[i].x);
    kp.push(landmarks[i].y);
    kp.push(landmarks[i].z);
  }
  return kp;
}

// Call backend
async function sendToBackend(keypoints) {
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keypoints }),
    });

    const data = await res.json();

    letterEl.innerText = data.prediction;
    confidenceEl.innerText =
      "Confidence: " + (data.confidence * 100).toFixed(1) + "%";

  } catch (err) {
    console.error("Backend error:", err);
  }
}

// Throttle requests
let lastSent = 0;

function onResults(results) {
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const landmarks = results.multiHandLandmarks[0];

    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
      color: "#22c55e",
      lineWidth: 2,
    });
    drawLandmarks(canvasCtx, landmarks, {
      color: "#ef4444",
      lineWidth: 1,
    });

    const keypoints = extractKeypoints(landmarks);

    const now = Date.now();
    if (now - lastSent > 500) {
      sendToBackend(keypoints);
      lastSent = now;
    }
  } else {
    letterEl.innerText = "-";
    confidenceEl.innerText = "No hand detected";
  }

  canvasCtx.restore();
}
