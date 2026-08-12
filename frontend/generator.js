// ==========================================================================
// SIGN0 TEXT-TO-SIGN DIFFUSION ANIMATION RENDERER (v4.0)
// ==========================================================================

const promptInput = document.getElementById("promptInput");
const generateBtn = document.getElementById("generateBtn");
const animCanvas = document.getElementById("animCanvas");
const ctx = animCanvas.getContext("2d");

const playPauseBtn = document.getElementById("playPauseBtn");
const loopBtn = document.getElementById("loopBtn");
const speedSelect = document.getElementById("speedSelect");
const playerStatus = document.getElementById("playerStatus");

const LOCAL_HOSTS = ["127.0.0.1", "localhost"];
const LOCAL_PORTS = [8000, 8005, 8001, 8080];
const REMOTE_API_BASE = "https://asl-prediction-v2.onrender.com";
let activeApiBaseUrl = "http://127.0.0.1:8000";
let apiReady = false;

// MediaPipe Hand Connection Pairs
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
  [0, 5], [5, 6], [6, 7], [7, 8],       // Index
  [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
  [9, 13], [13, 14], [14, 15], [15, 16],// Ring
  [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
  [0, 17]                               // Palm base
];

let currentAnimation = null; // Array of 3D frames (Time, 21, 3)
let currentFrameIndex = 0;
let isPlaying = false;
let isLooping = true;
let animTimer = null;
let playbackSpeed = 1.0;

// Drag-to-Rotate interaction parameters
let rotationX = -0.3; // pitch
let rotationY = 0.2;  // yaw
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;

// JWT Token
let authToken = null;

// Auto-detect working local backend (tests 127.0.0.1 and localhost across ports)
async function checkBackendConnection() {
  for (const host of LOCAL_HOSTS) {
    for (const port of LOCAL_PORTS) {
      try {
        const url = `http://${host}:${port}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 800);
        const res = await fetch(`${url}/`, { method: "GET", signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          activeApiBaseUrl = url;
          apiReady = true;
          return;
        }
      } catch (err) {}
    }
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${REMOTE_API_BASE}/`, { method: "GET", signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      activeApiBaseUrl = REMOTE_API_BASE;
      apiReady = true;
      return;
    }
  } catch (err) {
    apiReady = false;
  }
}

function setPrompt(val) {
  promptInput.value = val;
  document.querySelectorAll("[data-prompt]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.prompt.toLowerCase() === val.toLowerCase());
  });
  generateAnimation();
}

async function generateAnimation() {
  const promptText = promptInput.value.trim();
  if (!promptText) return;

  playerStatus.innerText = "Synthesizing keypoints...";
  playerStatus.style.color = "#38bdf8";

  try {
    if (!apiReady) {
      await checkBackendConnection();
    }

    if (!apiReady) {
      throw new Error("Backend API unavailable");
    }

    const headers = { "Content-Type": "application/json" };
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    }

    const res = await fetch(`${activeApiBaseUrl}/synthesize_sign`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ prompt: promptText }),
    });

    if (!res.ok) throw new Error(`API HTTP ${res.status}`);

    const data = await res.json();
    currentAnimation = data.keypoints_3d;
    currentFrameIndex = 0;

    const infoStr = data.words_synthesized ? data.words_synthesized.join(", ") : data.prompt;
    playerStatus.innerText = `Generated ${data.num_frames} frames [${infoStr}]`;
    playerStatus.style.color = "#22c55e";

    startPlayback();
  } catch (err) {
    console.warn("Backend API notice, generating local dynamic trajectory:", err);
    apiReady = false;
    currentAnimation = generateLocalTrajectory(promptText);
    currentFrameIndex = 0;
    playerStatus.innerText = `Local 3D trajectory (${promptText})`;
    playerStatus.style.color = "#a855f7";
    startPlayback();
  }
}

function startPlayback() {
  if (animTimer) clearInterval(animTimer);
  isPlaying = true;
  playPauseBtn.innerText = "Pause Animation";

  const frameIntervalMs = 70 / playbackSpeed;
  animTimer = setInterval(() => {
    if (!currentAnimation || currentAnimation.length === 0) return;

    renderFrame(currentAnimation[currentFrameIndex]);
    currentFrameIndex++;

    if (currentFrameIndex >= currentAnimation.length) {
      if (isLooping) {
        currentFrameIndex = 0;
      } else {
        stopPlayback();
      }
    }
  }, frameIntervalMs);
}

function stopPlayback() {
  isPlaying = false;
  if (animTimer) clearInterval(animTimer);
  playPauseBtn.innerText = "Play Animation";
}

function renderFrame(frame3D) {
  const W = animCanvas.width;
  const H = animCanvas.height;
  const cx = W / 2;
  const cy = H / 2 + 20;

  ctx.clearRect(0, 0, W, H);

  // Background Grid Glow
  ctx.strokeStyle = "rgba(56, 189, 248, 0.05)";
  ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }
  for (let y = 0; y < H; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }

  if (!frame3D || frame3D.length < 21) return;

  const wristX = frame3D[0][0];
  const wristY = frame3D[0][1];
  const wristZ = frame3D[0][2];

  const centered = frame3D.map(([x, y, z]) => [x - wristX, y - wristY, z - wristZ]);

  // Rotate coordinates using Pitch (rotationX) and Yaw (rotationY)
  const cosY = Math.cos(rotationY);
  const sinY = Math.sin(rotationY);
  const cosX = Math.cos(rotationX);
  const sinX = Math.sin(rotationX);

  const rotated = centered.map(([x, y, z]) => {
    // Y-rotation (Yaw)
    const x1 = x * cosY - z * sinY;
    const z1 = x * sinY + z * cosY;
    // X-rotation (Pitch)
    const y2 = y * cosX - z1 * sinX;
    return [x1, y2];
  });

  // Scale coordinates dynamically
  let maxDist = 0;
  for (const [x, y] of rotated) {
    const dist = Math.sqrt(x * x + y * y);
    if (dist > maxDist) maxDist = dist;
  }
  if (maxDist < 1e-6) maxDist = 1.0;

  const scale = 160 / maxDist; // Fit inside canvas

  const coords2D = rotated.map(([x, y]) => [cx + x * scale, cy + y * scale]);

  // Draw 3D Connectors
  ctx.lineWidth = 4.0;
  ctx.strokeStyle = "#38bdf8"; // Neon Cyan
  ctx.shadowColor = "#38bdf8";
  ctx.shadowBlur = 12;

  for (const [i, j] of HAND_CONNECTIONS) {
    const [x1, y1] = coords2D[i];
    const [x2, y2] = coords2D[j];
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  // Draw Joint Spheres
  ctx.shadowBlur = 0;
  for (let i = 0; i < coords2D.length; i++) {
    const [x, y] = coords2D[i];
    ctx.beginPath();
    ctx.arc(x, y, i === 0 ? 8 : 4.5, 0, 2 * Math.PI);
    ctx.fillStyle = i === 0 ? "#ef4444" : "#22c55e"; // Red wrist, green joints
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  // Frame Counter & Pitch/Yaw text info
  ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctx.font = "11px monospace";
  ctx.fillText(`Frame ${currentFrameIndex + 1} / ${currentAnimation.length}`, 16, 28);
  ctx.fillText(`Pitch: ${(rotationX * 180 / Math.PI).toFixed(0)}° Yaw: ${(rotationY * 180 / Math.PI).toFixed(0)}°`, 16, 44);
}

// Local trajectory generation fallback
function generateLocalTrajectory(promptText) {
  const words = promptText.toLowerCase().trim().split(/\s+/);
  const frames = [];

  const basePalm = [
    [0.0, 0.0, 0.0], [0.08, -0.05, 0.0], [0.14, -0.12, 0.0], [0.18, -0.18, 0.0], [0.22, -0.22, 0.0],
    [0.05, -0.25, 0.0], [0.07, -0.35, 0.0], [0.08, -0.42, 0.0], [0.09, -0.48, 0.0],
    [0.0, -0.26, 0.0], [0.0, -0.37, 0.0], [0.0, -0.45, 0.0], [0.0, -0.52, 0.0],
    [-0.05, -0.24, 0.0], [-0.07, -0.34, 0.0], [-0.08, -0.41, 0.0], [-0.09, -0.47, 0.0],
    [-0.10, -0.21, 0.0], [-0.13, -0.29, 0.0], [-0.15, -0.35, 0.0], [-0.17, -0.40, 0.0]
  ];

  for (const word of words) {
    const hashVal = word.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const waveFreq = 1.0 + (hashVal % 3) * 0.5;

    for (let t = 0; t < 20; t++) {
      const progress = t / 20.0;
      const wave = Math.sin(progress * Math.PI * 2 * waveFreq) * 0.07;
      const lift = Math.sin(progress * Math.PI) * 0.09;
      
      const frame = basePalm.map(pt => {
        const copy = [...pt];
        copy[0] += wave;
        copy[1] -= lift;
        return copy;
      });
      frames.push(frame);
    }
  }
  return frames;
}

// Setup canvas click/drag handlers to rotate
function setupCanvasDragControls() {
  animCanvas.addEventListener("mousedown", (e) => {
    isDragging = true;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
  });
  animCanvas.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const deltaX = e.clientX - lastMouseX;
    const deltaY = e.clientY - lastMouseY;

    rotationY += deltaX * 0.01;
    rotationX += deltaY * 0.01;

    lastMouseX = e.clientX;
    lastMouseY = e.clientY;

    if (!isPlaying && currentAnimation && currentAnimation.length > 0) {
      renderFrame(currentAnimation[currentFrameIndex]);
    }
  });
  window.addEventListener("mouseup", () => {
    isDragging = false;
  });

  // Touch Support
  animCanvas.addEventListener("touchstart", (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      lastMouseX = e.touches[0].clientX;
      lastMouseY = e.touches[0].clientY;
    }
  });
  animCanvas.addEventListener("touchmove", (e) => {
    if (!isDragging || e.touches.length !== 1) return;
    const deltaX = e.touches[0].clientX - lastMouseX;
    const deltaY = e.touches[0].clientY - lastMouseY;

    rotationY += deltaX * 0.01;
    rotationX += deltaY * 0.01;

    lastMouseX = e.touches[0].clientX;
    lastMouseY = e.touches[0].clientY;

    if (!isPlaying && currentAnimation && currentAnimation.length > 0) {
      renderFrame(currentAnimation[currentFrameIndex]);
    }
  });
  animCanvas.addEventListener("touchend", () => {
    isDragging = false;
  });
}

// Gating checker
function checkAuthorizationGates() {
  const token = localStorage.getItem("sign0_token");
  const userStr = localStorage.getItem("sign0_user");
  
  if (token && userStr) {
    authToken = token;
    const user = JSON.parse(userStr);
    const plan = user.plan || "free";
    if (plan !== "developer") {
      document.getElementById("lock-overlay-generator").style.display = "flex";
    } else {
      document.getElementById("lock-overlay-generator").style.display = "none";
    }
  } else {
    document.getElementById("lock-overlay-generator").style.display = "flex";
  }
}

// UI triggers
generateBtn.addEventListener("click", generateAnimation);
playPauseBtn.addEventListener("click", () => {
  if (isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
});
loopBtn.addEventListener("click", () => {
  isLooping = !isLooping;
  loopBtn.classList.toggle("active", isLooping);
  loopBtn.innerText = isLooping ? "Loop: ON" : "Loop: OFF";
});
speedSelect.addEventListener("change", (e) => {
  playbackSpeed = parseFloat(e.target.value);
  if (isPlaying) startPlayback();
});
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => setPrompt(chip.dataset.prompt));
});

// Init
async function init() {
  checkAuthorizationGates();
  setupCanvasDragControls();
  await checkBackendConnection();
  generateAnimation();
}
init();
