// ==========================================================================
// SIGN0 REAL-TIME ASL RECOGNITION ENGINE (CLIENT-SIDE JS)
// ==========================================================================

const videoElement = document.getElementById("video");
const canvasElement = document.getElementById("canvas");
const canvasCtx = canvasElement.getContext("2d");
const videoOverlay = document.getElementById("videoOverlay");

const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

const predictedLetterEl = document.getElementById("predictedLetter");
const confidencePercentEl = document.getElementById("confidencePercent");
const confidenceBarEl = document.getElementById("confidenceBar");
const top3ListEl = document.getElementById("top3List");
const handStateLabelEl = document.getElementById("handStateLabel");

const latencyPillEl = document.getElementById("latencyPill");
const backendPillEl = document.getElementById("backendPill");

const sentenceDisplayEl = document.getElementById("sentenceDisplay");
const addLetterBtn = document.getElementById("addLetterBtn");
const spaceBtn = document.getElementById("spaceBtn");
const backspaceBtn = document.getElementById("backspaceBtn");
const clearBtn = document.getElementById("clearBtn");
const speakSentenceBtn = document.getElementById("speakSentenceBtn");
const ttsToggleBtn = document.getElementById("ttsToggle");

// ==========================================
// API CONFIGURATION & BACKEND AUTO-DETECTION
// ==========================================
const LOCAL_PORTS = [8005, 8001, 8000, 8080];
const REMOTE_API = "https://asl-prediction.onrender.com/predict";
let activeApiUrl = `http://localhost:8005/predict`;

let ttsEnabled = true;
let currentPrediction = "-";
let currentConfidence = 0;
let lastSpokenLetter = "";
let lastSentTime = 0;
const SEND_INTERVAL_MS = 300;

// Auto-detect working local backend port
async function checkBackendConnection() {
  for (const port of LOCAL_PORTS) {
    try {
      const res = await fetch(`http://localhost:${port}/`, { method: "GET" });
      if (res.ok) {
        activeApiUrl = `http://localhost:${port}/predict`;
        backendPillEl.innerText = `Local API (Port ${port})`;
        backendPillEl.className = "val text-blue";
        return;
      }
    } catch (err) {
      // Continue checking next port
    }
  }
  
  // Fallback to production remote API if no local port is active
  activeApiUrl = REMOTE_API;
  backendPillEl.innerText = "Production Render API";
  backendPillEl.className = "val text-blue";
}
checkBackendConnection();

// ==========================================
// LANDMARK NORMALIZATION (MUST MATCH PYTHON)
// ==========================================
function normalizeKeypoints(landmarks) {
  const kp = [];
  for (let i = 0; i < 21; i++) {
    kp.push(landmarks[i].x, landmarks[i].y, landmarks[i].z);
  }

  // 1. Translate Wrist (Point 0) to origin
  const wristX = kp[0], wristY = kp[1], wristZ = kp[2];
  const translated = [];
  let maxDist = 0;

  for (let i = 0; i < 21; i++) {
    const dx = kp[i * 3] - wristX;
    const dy = kp[i * 3 + 1] - wristY;
    const dz = kp[i * 3 + 2] - wristZ;
    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (dist > maxDist) maxDist = dist;
    translated.push(dx, dy, dz);
  }

  if (maxDist < 1e-6) maxDist = 1.0;

  // 2. Scale by max Euclidean distance
  const normalized = [];
  for (let i = 0; i < translated.length; i++) {
    normalized.push(translated[i] / maxDist);
  }

  return normalized;
}

// ==========================================
// MEDIAPIPE HANDS INITIALIZATION
// ==========================================
const hands = new Hands({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.6,
  minTrackingConfidence: 0.6,
});

hands.onResults(onResults);

// ==========================================
// RESILIENT CAMERA INITIALIZATION
// ==========================================
async function startCamera() {
  setStatus("yellow", "Requesting Camera Access...");

  // Strategy 1: MediaPipe Camera Utility with ideal resolution constraints
  try {
    const camera = new Camera(videoElement, {
      onFrame: async () => {
        if (videoElement.readyState >= 2) {
          await hands.send({ image: videoElement });
        }
      },
      width: 640,
      height: 480,
    });
    await camera.start();
    if (videoOverlay) videoOverlay.classList.add("hidden");
    setStatus("green", "Camera Active & Tracking");
    return;
  } catch (err1) {
    console.warn("MediaPipe Camera util failed, trying native getUserMedia fallback:", err1);
  }

  // Strategy 2: Native browser getUserMedia fallback with flexible video constraints
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: "user",
        width: { ideal: 640 },
        height: { ideal: 480 }
      },
      audio: false
    });

    videoElement.srcObject = stream;
    await videoElement.play();

    if (videoOverlay) videoOverlay.classList.add("hidden");
    setStatus("green", "Camera Active (Native Stream)");

    let isProcessing = false;
    async function frameLoop() {
      if (!isProcessing && videoElement.readyState >= 2) {
        isProcessing = true;
        try {
          await hands.send({ image: videoElement });
        } catch (e) {
          console.error("Hands process error:", e);
        }
        isProcessing = false;
      }
      requestAnimationFrame(frameLoop);
    }
    requestAnimationFrame(frameLoop);
  } catch (err2) {
    console.error("Native camera fallback error:", err2);
    setStatus("red", "Camera Error: Webcam not found or permission denied");
  }
}

startCamera();

// ==========================================
// CUSTOM CANVAS LANDMARK VISUALIZER
// ==========================================
function drawStyledLandmarks(ctx, landmarks) {
  const w = canvasElement.width;
  const h = canvasElement.height;

  // Draw connectors
  if (typeof HAND_CONNECTIONS !== "undefined") {
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#38bdf8"; // Neon cyan
    for (const conn of HAND_CONNECTIONS) {
      const p1 = landmarks[conn[0]];
      const p2 = landmarks[conn[1]];
      ctx.beginPath();
      ctx.moveTo(p1.x * w, p1.y * h);
      ctx.lineTo(p2.x * w, p2.y * h);
      ctx.stroke();
    }
  }

  // Draw joint nodes
  for (let i = 0; i < landmarks.length; i++) {
    const lm = landmarks[i];
    const cx = lm.x * w;
    const cy = lm.y * h;

    ctx.beginPath();
    ctx.arc(cx, cy, i === 0 ? 7 : 4, 0, 2 * Math.PI);
    ctx.fillStyle = i === 0 ? "#ef4444" : "#22c55e"; // Red for wrist, green for joints
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
}

// ==========================================
// MAIN FRAME HANDLER & BACKEND CALL
// ==========================================
function onResults(results) {
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  if (results.multiHandLandmarks && results.multiHandLandmarks.length === 1) {
    const landmarks = results.multiHandLandmarks[0];
    drawStyledLandmarks(canvasCtx, landmarks);

    const normKeypoints = normalizeKeypoints(landmarks);
    const now = Date.now();

    if (now - lastSentTime > SEND_INTERVAL_MS) {
      sendToBackend(normKeypoints);
      lastSentTime = now;
    }
  } else {
    resetPredictionDisplay("No hand detected");
  }
}

// ==========================================
// BACKEND PREDICTION FETCH
// ==========================================
async function sendToBackend(keypoints) {
  const startTime = performance.now();
  try {
    const res = await fetch(activeApiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keypoints }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const roundtripLatency = Math.round(performance.now() - startTime);

    updatePredictionDisplay(data, roundtripLatency);
    setStatus("green", "Real-Time Tracking Active");
  } catch (err) {
    setStatus("yellow", "API Retrying...");
    latencyPillEl.innerText = "-";
  }
}

// ==========================================
// UI DISPLAY UPDATER
// ==========================================
function updatePredictionDisplay(data, latencyMs) {
  currentPrediction = data.prediction;
  currentConfidence = Math.round(data.confidence * 100);

  predictedLetterEl.innerText = currentPrediction;
  confidencePercentEl.innerText = `${currentConfidence}%`;
  confidenceBarEl.style.width = `${currentConfidence}%`;
  handStateLabelEl.innerText = "Hand Tracked & Classifying";
  latencyPillEl.innerText = `${latencyMs} ms`;

  // Render Top-3 candidates
  if (data.top_3 && data.top_3.length > 0) {
    top3ListEl.innerHTML = data.top_3
      .map(
        (c) => `
      <div class="top3-item">
        <span class="lbl">${c.label}</span>
        <span class="prob">${(c.probability * 100).toFixed(1)}%</span>
      </div>`
      )
      .join("");
  }

  // Audio Speech Synthesis for changes with high confidence (>80%)
  if (ttsEnabled && currentConfidence >= 80 && currentPrediction !== lastSpokenLetter) {
    speakText(currentPrediction);
    lastSpokenLetter = currentPrediction;
  }
}

function resetPredictionDisplay(reason) {
  currentPrediction = "-";
  currentConfidence = 0;
  predictedLetterEl.innerText = "-";
  confidencePercentEl.innerText = "0%";
  confidenceBarEl.style.width = "0%";
  handStateLabelEl.innerText = reason;
  top3ListEl.innerHTML = `
    <div class="top3-item"><span class="lbl">-</span><span class="prob">-</span></div>
    <div class="top3-item"><span class="lbl">-</span><span class="prob">-</span></div>
    <div class="top3-item"><span class="lbl">-</span><span class="prob">-</span></div>
  `;
}

function setStatus(colorClass, text) {
  statusDot.className = `status-dot dot-${colorClass}`;
  statusText.innerText = text;
}

// ==========================================
// SENTENCE BUILDER & TEXT-TO-SPEECH CONTROLS
// ==========================================
function appendToSentence(text) {
  sentenceDisplayEl.innerText += text;
}

addLetterBtn.addEventListener("click", () => {
  if (currentPrediction !== "-" && currentConfidence > 50) {
    appendToSentence(currentPrediction);
  }
});

spaceBtn.addEventListener("click", () => {
  appendToSentence(" ");
});

backspaceBtn.addEventListener("click", () => {
  const cur = sentenceDisplayEl.innerText;
  if (cur.length > 0) {
    sentenceDisplayEl.innerText = cur.slice(0, -1);
  }
});

clearBtn.addEventListener("click", () => {
  sentenceDisplayEl.innerText = "";
});

speakSentenceBtn.addEventListener("click", () => {
  const text = sentenceDisplayEl.innerText.trim();
  if (text) speakText(text);
});

// ==========================================
// INTERACTIVE ASL DICTIONARY & GUIDE
// ==========================================
const dictModal = document.getElementById("dictModal");
const dictToggleBtn = document.getElementById("dictToggleBtn");
const closeDictBtn = document.getElementById("closeDictBtn");
const dictSearchInput = document.getElementById("dictSearchInput");
const dictCardsGrid = document.getElementById("dictCardsGrid");
const filterBtns = document.querySelectorAll(".filter-btn");

let currentDictCategory = "alphabets";

const ASL_DICTIONARY_DATA = [
  // ALPHABETS
  { title: "A", category: "alphabets", badge: "Letter A", desc: "Form a fist with your thumb resting vertically against the side of your index finger." },
  { title: "B", category: "alphabets", badge: "Letter B", desc: "Open palm facing forward with four fingers extended upward and thumb tucked across palm." },
  { title: "C", category: "alphabets", badge: "Letter C", desc: "Curving all fingers and thumb to form a curved 'C' shape with your hand." },
  { title: "D", category: "alphabets", badge: "Letter D", desc: "Point your index finger straight up while your thumb touches the middle, ring, and pinky tips." },
  { title: "E", category: "alphabets", badge: "Letter E", desc: "Curl all four fingers down so their tips touch the top edge of your thumb." },
  { title: "F", category: "alphabets", badge: "Letter F", desc: "Touch index finger to thumb tip forming a circle; middle, ring, and pinky fingers fan upward." },
  { title: "G", category: "alphabets", badge: "Letter G", desc: "Extend index finger and thumb horizontally parallel to each other pointing left/right." },
  { title: "H", category: "alphabets", badge: "Letter H", desc: "Extend index and middle fingers horizontally side-by-side pointing sideways." },
  { title: "I", category: "alphabets", badge: "Letter I", desc: "Extend your pinky finger straight up while keeping all other fingers folded into a fist." },
  { title: "J", category: "alphabets", badge: "Letter J", desc: "Extend your pinky finger up and draw a 'J' hook trajectory in the air." },
  { title: "K", category: "alphabets", badge: "Letter K", desc: "Point index finger up, middle finger forward, with thumb tucked in between." },
  { title: "L", category: "alphabets", badge: "Letter L", desc: "Extend index finger straight up and thumb outward to form a right-angle 'L' shape." },
  { title: "M", category: "alphabets", badge: "Letter M", desc: "Tuck your thumb beneath the first three fingers (index, middle, and ring)." },
  { title: "N", category: "alphabets", badge: "Letter N", desc: "Tuck your thumb beneath the first two fingers (index and middle)." },
  { title: "O", category: "alphabets", badge: "Letter O", desc: "Touch all four fingertips to the tip of your thumb, forming an 'O' circle." },
  { title: "P", category: "alphabets", badge: "Letter P", desc: "Downward-pointing 'K' handshape with index finger pointing toward the ground." },
  { title: "Q", category: "alphabets", badge: "Letter Q", desc: "Downward-pointing 'G' handshape with index finger and thumb pointing downward." },
  { title: "R", category: "alphabets", badge: "Letter R", desc: "Cross your index finger tightly over your middle finger." },
  { title: "S", category: "alphabets", badge: "Letter S", desc: "Make a tight fist with your thumb folded across the front of your fingers." },
  { title: "T", category: "alphabets", badge: "Letter T", desc: "Tuck your thumb between your index finger and middle finger inside a fist." },
  { title: "U", category: "alphabets", badge: "Letter U", desc: "Extend index and middle fingers straight up held tightly together." },
  { title: "V", category: "alphabets", badge: "Letter V", desc: "Extend index and middle fingers straight up spread apart in a peace sign." },
  { title: "W", category: "alphabets", badge: "Letter W", desc: "Extend index, middle, and ring fingers upward spread apart forming a 'W'." },
  { title: "X", category: "alphabets", badge: "Letter X", desc: "Bend index finger into a hook shape with remaining fingers folded in fist." },
  { title: "Y", category: "alphabets", badge: "Letter Y", desc: "Extend thumb and pinky finger outward while keeping middle three fingers folded." },
  { title: "Z", category: "alphabets", badge: "Letter Z", desc: "Use your index finger to trace the letter 'Z' path in the air." },

  // PHRASES
  { title: "Hello", category: "phrases", badge: "Greeting", desc: "Place your open hand near your forehead temple and move it outward in a gentle wave motion." },
  { title: "Thank You", category: "phrases", badge: "Politeness", desc: "Touch your fingertips to your chin/lips, then move your palm forward towards the person." },
  { title: "Please", category: "phrases", badge: "Politeness", desc: "Rub your open right palm in a smooth circular motion over your chest heart area." },
  { title: "Yes", category: "phrases", badge: "Basic Word", desc: "Make a fist with your dominant hand and nod it up and down like a nodding head." },
  { title: "No", category: "phrases", badge: "Basic Word", desc: "Snap index and middle fingers together against your thumb repeatedly." },
  { title: "Help", category: "phrases", badge: "Emergency", desc: "Place a thumbs-up fist on top of your opposite flat palm and lift both hands upward." },
  { title: "I Love You", category: "phrases", badge: "Expression", desc: "Extend your thumb, index finger, and pinky finger simultaneously." },
  { title: "Water", category: "phrases", badge: "Daily Need", desc: "Make a 'W' handshape with 3 fingers and tap your index finger against your chin." },
  { title: "Eat / Food", category: "phrases", badge: "Daily Need", desc: "Gather all fingertips together touching your thumb and tap against your lips." },

  // NUMBERS
  { title: "1", category: "numbers", badge: "Number 1", desc: "Extend index finger straight up with palm facing inward." },
  { title: "2", category: "numbers", badge: "Number 2", desc: "Extend index and middle fingers straight up spread apart." },
  { title: "3", category: "numbers", badge: "Number 3", desc: "Extend thumb, index, and middle fingers outward." },
  { title: "4", category: "numbers", badge: "Number 4", desc: "Extend four fingers upward with thumb tucked across palm." },
  { title: "5", category: "numbers", badge: "Number 5", desc: "Open palm with all five fingers and thumb extended wide." },
  { title: "6", category: "numbers", badge: "Number 6", desc: "Touch tip of pinky finger to thumb tip with 3 fingers up." },
  { title: "7", category: "numbers", badge: "Number 7", desc: "Touch tip of ring finger to thumb tip with remaining fingers up." },
  { title: "8", category: "numbers", badge: "Number 8", desc: "Touch tip of middle finger to thumb tip with remaining fingers up." },
  { title: "9", category: "numbers", badge: "Number 9", desc: "Touch tip of index finger to thumb tip with 3 fingers up." },
  { title: "10", category: "numbers", badge: "Number 10", desc: "Make a thumbs-up fist and shake it gently side to side." }
];

function renderDictionary() {
  const searchTerm = dictSearchInput.value.toLowerCase().trim();

  const filtered = ASL_DICTIONARY_DATA.filter((item) => {
    const matchesCategory = item.category === currentDictCategory;
    const matchesSearch =
      item.title.toLowerCase().includes(searchTerm) ||
      item.desc.toLowerCase().includes(searchTerm) ||
      item.badge.toLowerCase().includes(searchTerm);
    return matchesCategory && matchesSearch;
  });

  if (filtered.length === 0) {
    dictCardsGrid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-muted)">
        <p style="font-size:18px">No matching sign entries found.</p>
      </div>`;
    return;
  }

  dictCardsGrid.innerHTML = filtered
    .map(
      (item) => `
    <div class="dict-item-card">
      <div class="dict-card-top">
        <span class="dict-card-title">${item.title}</span>
        <span class="dict-card-badge">${item.badge}</span>
      </div>
      <p class="dict-card-desc">${item.desc}</p>
      <div class="dict-card-footer">
        <button class="dict-btn-speak" onclick="speakText('${item.title}: ${item.desc}')">
          🔊 Hear Pronunciation
        </button>
      </div>
    </div>`
    )
    .join("");
}

dictToggleBtn.addEventListener("click", () => {
  dictModal.classList.remove("hidden");
  renderDictionary();
});

closeDictBtn.addEventListener("click", () => {
  dictModal.classList.add("hidden");
});

dictModal.addEventListener("click", (e) => {
  if (e.target === dictModal) dictModal.classList.add("hidden");
});

filterBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentDictCategory = btn.dataset.category;
    renderDictionary();
  });
});

dictSearchInput.addEventListener("input", renderDictionary);


ttsToggleBtn.addEventListener("click", () => {
  ttsEnabled = !ttsEnabled;
  ttsToggleBtn.classList.toggle("active", ttsEnabled);
  ttsToggleBtn.innerText = ttsEnabled ? "🔊 Speech ON" : "🔇 Speech OFF";
});

function speakText(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel(); // stop current utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}
