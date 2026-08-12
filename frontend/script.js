// ==========================================================================
// SIGN0 REAL-TIME ASL RECOGNITION ENGINE (CLIENT-SIDE JS v4.0)
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
const LOCAL_HOSTS = ["127.0.0.1", "localhost"];
const LOCAL_PORTS = [8000, 8005, 8001, 8080];
const REMOTE_API_BASE = "https://asl-prediction-v2.onrender.com";
let activeApiBaseUrl = "http://127.0.0.1:8000";
let activeApiUrl = `${activeApiBaseUrl}/predict`;

let ttsEnabled = true;
let selectedModelMode = "mlp"; // 'mlp' or 'transformer'
let currentPrediction = "-";
let currentConfidence = 0;
let stablePrediction = "-";
let stableConfidence = 0;
let lastSpokenLetter = "";
let lastSentTime = 0;
let lastBackendCheckTime = 0;
const SEND_INTERVAL_MS = 250;
const BACKEND_RECHECK_MS = 6000;
const PREDICTION_HISTORY_LIMIT = 8;
const MIN_STABLE_CONFIDENCE = 65;
const MIN_STABLE_VOTES = 4;
const predictionHistory = [];
const sequenceBuffer = [];

// ==========================================
// AUTH & SUBSCRIPTION STATE
// ==========================================
let currentUser = null;
let authToken = null;

// ==========================================
// MOCK WEB AUDIO FX SYNTH
// ==========================================
const SoundFX = {
  ctx: null,
  init() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
  },
  playClick() {
    this.init();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(800, this.ctx.currentTime);
    gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.05);
  },
  playSuccess() {
    this.init();
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    
    // Pleasant arpeggio: C5 (523.25Hz) -> E5 (659.25Hz) -> G5 (783.99Hz)
    const notes = [523.25, 659.25, 783.99];
    notes.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, t + idx * 0.1);
      gain.gain.setValueAtTime(0.08, t + idx * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.001, t + idx * 0.1 + 0.25);
      osc.start(t + idx * 0.1);
      osc.stop(t + idx * 0.1 + 0.25);
    });
  },
  playFailure() {
    this.init();
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(220, this.ctx.currentTime);
    osc.frequency.linearRampToValueAtTime(110, this.ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.3);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.3);
  }
};

// ==========================================
// GAMIFIED PRACTICE STATE
// ==========================================
let practiceMode = false;
let currentChallenge = "A";
let practiceScore = 0;
let practiceStreak = 0;
let challengeMatchCounter = 0;

const CHALLENGES_POOL = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "U", "V", "W", "Y", "Yes", "No", "Water", "Hello", "1", "2", "3", "5"];

// ==========================================
// API DETECTOR & WEBHOOK CHECKOUT HANDLER
// ==========================================
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
          activeApiUrl = `${activeApiBaseUrl}/${selectedModelMode === "transformer" ? "predict_sequence" : "predict"}`;
          backendPillEl.innerText = `Local API (${host}:${port})`;
          backendPillEl.className = "val text-blue";
          return;
        }
      } catch (err) {}
    }
  }

  activeApiBaseUrl = REMOTE_API_BASE;
  activeApiUrl = `${activeApiBaseUrl}/${selectedModelMode === "transformer" ? "predict_sequence" : "predict"}`;
  backendPillEl.innerText = "Production Render API";
  backendPillEl.className = "val text-blue";
}

function getAuthHeaders() {
  const headers = { "Content-Type": "application/json" };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
}

// Intercept checkout session callbacks from Stripe Sandbox
async function handlePaymentRedirect() {
  const params = new URLSearchParams(window.location.search);
  const payment = params.get("payment");
  const plan = params.get("plan");
  const savedToken = localStorage.getItem("sign0_token");
  const savedUser = localStorage.getItem("sign0_user");

  if (payment === "success" && plan && savedToken && savedUser) {
    authToken = savedToken;
    currentUser = JSON.parse(savedUser);
    
    // Simulate webhook arrival on backend API
    try {
      const resp = await fetch(`${activeApiBaseUrl}/payment/webhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "checkout.session.completed",
          data: {
            object: {
              client_reference_id: currentUser.username,
              metadata: { plan }
            }
          }
        })
      });
      if (resp.ok) {
        // Strip parameters from URL
        window.history.replaceState({}, document.title, window.location.pathname);
        showToast(`Checkout complete! Subscribed to ${plan} successfully.`, "success");
        SoundFX.playSuccess();
        
        // Refresh session
        await loadMe();
      }
    } catch (err) {
      showToast("Billing synchronization failed.", "error");
    }
  }
}

// ==========================================
// AUTH DIALOG & PROFILE MODALS
// ==========================================
const authModal = document.getElementById("authModal");
const profileModal = document.getElementById("profileModal");
const subscriptionModal = document.getElementById("subscriptionModal");
const loginBtn = document.getElementById("loginBtn");
const userChipBtn = document.getElementById("userChipBtn");

function showAuthModal() {
  authModal.classList.add("active");
  switchAuthTab("login");
}
window.closeAuthModal = function() {
  authModal.classList.remove("active");
};

function switchAuthTab(tab) {
  document.getElementById("authTabLogin").classList.toggle("active", tab === "login");
  document.getElementById("authTabRegister").classList.toggle("active", tab === "register");
  document.getElementById("authPaneLogin").classList.toggle("active", tab === "login");
  document.getElementById("authPaneRegister").classList.toggle("active", tab === "register");
  document.getElementById("authMsg").style.display = "none";
}

function showToast(msg, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add("removing"), 3000);
  setTimeout(() => toast.remove(), 3400);
}

// Handle Form Submissions
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value.trim().lower();
  const password = document.getElementById("loginPassword").value;
  const msgEl = document.getElementById("authMsg");

  try {
    const res = await fetch(`${activeApiBaseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem("sign0_token", authToken);
      localStorage.setItem("sign0_user", JSON.stringify(currentUser));
      
      closeAuthModal();
      updateUserUI();
      showToast("Authentication successful!", "success");
      SoundFX.playSuccess();
      loadMe(); // Pull quotas
    } else {
      msgEl.innerText = data.message || "Failed to sign in.";
      msgEl.className = "auth-msg error";
    }
  } catch (err) {
    msgEl.innerText = "Cannot reach server.";
    msgEl.className = "auth-msg error";
  }
});

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("regUsername").value.trim().lower();
  const email = document.getElementById("regEmail").value.trim();
  const fullname = document.getElementById("regFullname").value.trim();
  const role = document.getElementById("regRole").value;
  const password = document.getElementById("regPassword").value;
  const msgEl = document.getElementById("authMsg");

  try {
    const res = await fetch(`${activeApiBaseUrl}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, full_name: fullname, role, password })
    });
    const data = await res.json();
    if (data.success) {
      msgEl.innerText = data.message;
      msgEl.className = "auth-msg success";
      setTimeout(() => switchAuthTab("login"), 1200);
    } else {
      msgEl.innerText = data.message || "Registration failed.";
      msgEl.className = "auth-msg error";
    }
  } catch (err) {
    msgEl.innerText = "Connection error.";
    msgEl.className = "auth-msg error";
  }
});

async function loadMe() {
  if (!authToken) return;
  try {
    const res = await fetch(`${activeApiBaseUrl}/auth/me`, { headers: getAuthHeaders() });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      localStorage.setItem("sign0_user", JSON.stringify(currentUser));
      updateUserUI();
    }
  } catch (e) {
    console.error("Session sync failed:", e);
  }
}

function updateUserUI() {
  if (currentUser) {
    loginBtn.style.display = "none";
    userChipBtn.style.display = "flex";
    
    // Set avatar
    const initials = currentUser.full_name ? currentUser.full_name.substring(0, 2).toUpperCase() : currentUser.username.substring(0, 2).toUpperCase();
    document.getElementById("sidebarAvatar").innerText = initials;
    document.getElementById("sidebarUsername").innerText = currentUser.full_name || currentUser.username;
    
    const plan = currentUser.plan || "free";
    const badge = document.getElementById("sidebarPlanBadge");
    badge.innerText = plan;
    badge.className = `plan-badge ${plan}`;

    // Apply feature locks
    const isPro = plan === "pro" || plan === "developer";
    document.getElementById("lock-overlay-transformer").style.display = isPro ? "none" : "flex";
    
    // Sidebar quotas
    const usage = currentUser.usage;
    if (usage) {
      const dailyRemaining = usage.daily_quota === 999999 ? "∞" : usage.daily_remaining;
      const progress = usage.daily_quota === 999999 ? 0 : (usage.queries_today / usage.daily_quota) * 100;
      showNotifQuota(usage.queries_today, usage.daily_quota, progress);
    }
  } else {
    loginBtn.style.display = "flex";
    userChipBtn.style.display = "none";
    document.getElementById("lock-overlay-transformer").style.display = "flex";
  }
}

function showNotifQuota(used, quota, progress) {
  // Can render sidebar quota info if elements exist
}

window.doLogout = function() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem("sign0_token");
  localStorage.removeItem("sign0_user");
  updateUserUI();
  closeProfileModal();
  showToast("Logged out successfully.", "info");
  SoundFX.playClick();
};

// ==========================================
// PROFILE TABS & DETAILS
// ==========================================
window.openProfileModal = function() {
  if (!currentUser) return;
  profileModal.classList.add("active");
  switchProfileTab("info");
  loadProfileModalData();
};
window.closeProfileModal = function() {
  profileModal.classList.remove("active");
};

window.switchProfileTab = function(tab) {
  document.querySelectorAll(".profile-tab").forEach(t => t.classList.toggle("active", t.dataset.ptab === tab));
  document.querySelectorAll(".profile-pane").forEach(p => p.classList.toggle("active", p.id === "ptab-" + tab));

  if (tab === "usage") loadUsageTab();
  if (tab === "activity") loadActivityTab();
};

function loadProfileModalData() {
  document.getElementById("pfFullname").value = currentUser.full_name || "";
  document.getElementById("pfEmail").value = currentUser.email || "";
  
  const initials = currentUser.full_name ? currentUser.full_name.substring(0, 2).toUpperCase() : currentUser.username.substring(0, 2).toUpperCase();
  document.getElementById("profileAvatarLarge").innerText = initials;
  document.getElementById("profileHeaderName").innerText = currentUser.full_name || currentUser.username;
  document.getElementById("profileRoleTag").innerText = currentUser.role || "learner";
  
  const pb = document.getElementById("profilePlanBadge");
  pb.innerText = currentUser.plan || "free";
  pb.className = `plan-badge ${currentUser.plan || "free"}`;
}

window.saveProfileInfo = async function() {
  const fullName = document.getElementById("pfFullname").value.trim();
  const email = document.getElementById("pfEmail").value.trim();
  const infoMsg = document.getElementById("profileInfoMsg");

  try {
    const res = await fetch(`${activeApiBaseUrl}/auth/profile/update`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ full_name: fullName, email })
    });
    const data = await res.json();
    if (data.success) {
      currentUser = { ...currentUser, ...data.user };
      localStorage.setItem("sign0_user", JSON.stringify(currentUser));
      updateUserUI();
      loadProfileModalData();
      infoMsg.innerText = "Account info updated successfully.";
      infoMsg.className = "auth-msg success";
    }
  } catch (err) {
    infoMsg.innerText = "Failed to update profile.";
    infoMsg.className = "auth-msg error";
  }
};

async function loadUsageTab() {
  if (!currentUser) return;
  const usage = currentUser.usage || { queries_today: 0, daily_quota: 20, daily_remaining: 20 };
  
  document.getElementById("pfQueriesToday").innerText = usage.queries_today;
  document.getElementById("pfDailyRemaining").innerText = usage.daily_quota === 999999 ? "∞" : usage.daily_remaining;
  document.getElementById("pfDailyLabel").innerText = usage.daily_quota === 999999 ? `${usage.queries_today} / ∞` : `${usage.queries_today} / ${usage.daily_quota}`;
  
  const progress = usage.daily_quota === 999999 ? 0 : (usage.queries_today / usage.daily_quota) * 100;
  document.getElementById("pfDailyBar").style.width = `${progress}%`;
  
  // Show keygen box for developer tier
  const apiBox = document.getElementById("apiKeySection");
  if (currentUser.plan === "developer") {
    apiBox.style.display = "block";
    document.getElementById("apiKeyVal").innerText = currentUser.api_key || "No key generated. Click to generate.";
  } else {
    apiBox.style.display = "none";
  }

  // Toggle Stripe portal button visibility
  const portalBox = document.getElementById("stripePortalSection");
  if (currentUser.plan !== "free") {
    portalBox.style.display = "block";
  } else {
    portalBox.style.display = "none";
  }
}

window.openStripePortal = async function() {
  try {
    showToast("Redirecting to Stripe Billing Portal...", "info");
    SoundFX.playClick();
    const res = await fetch(`${activeApiBaseUrl}/payment/portal`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ return_url: window.location.href })
    });
    const data = await res.json();
    if (data.success && data.portal_url) {
      setTimeout(() => {
        window.location.href = data.portal_url;
      }, 800);
    } else {
      showToast(data.detail || "Failed to open billing portal.", "error");
    }
  } catch (err) {
    showToast("Billing portal currently offline.", "error");
  }
};


async function loadActivityTab() {
  const container = document.getElementById("profileActivityContent");
  try {
    const res = await fetch(`${activeApiBaseUrl}/auth/activity`, { headers: getAuthHeaders() });
    const data = await res.json();
    if (data.success && data.activity.length > 0) {
      container.innerHTML = `
        <table style="width:100%;text-align:left;border-collapse:collapse">
          <tr style="color:var(--text-dim)"><th style="padding:6px">Endpoint</th><th style="padding:6px">Timestamp</th></tr>
          ${data.activity.map(a => `
            <tr style="border-top:1px solid var(--glass-border)">
              <td style="padding:6px"><code>${a.endpoint}</code></td>
              <td style="padding:6px">${new Date(a.timestamp).toLocaleTimeString()}</td>
            </tr>
          `).join("")}
        </table>`;
    } else {
      container.innerText = "No recent endpoint transactions recorded.";
    }
  } catch (err) {
    container.innerText = "Activity logs unavailable.";
  }
}

window.generateApiKey = async function() {
  try {
    const res = await fetch(`${activeApiBaseUrl}/auth/profile/generate-apikey`, {
      method: "POST",
      headers: getAuthHeaders()
    });
    const data = await res.json();
    if (data.success) {
      currentUser.api_key = data.api_key;
      localStorage.setItem("sign0_user", JSON.stringify(currentUser));
      document.getElementById("apiKeyVal").innerText = data.api_key;
      showToast("New API Key generated successfully.", "success");
      SoundFX.playSuccess();
    }
  } catch (e) {
    showToast("Failed to generate key.", "error");
  }
};

// ==========================================
// SUBSCRIPTION CARD RENDERING & BILLING
// ==========================================
window.openSubscriptionModal = function() {
  subscriptionModal.classList.add("active");
  renderPlansGrid();
};
window.closeSubscriptionModal = function() {
  subscriptionModal.classList.remove("active");
};

function renderPlansGrid() {
  const grid = document.getElementById("plansGrid");
  const userPlan = currentUser ? currentUser.plan : "free";

  const plans = [
    {
      id: "free",
      name: "Free Sandbox",
      price: "$0",
      desc: "For basic ASL learning & webcam letter prediction",
      features: ["20 static sign queries/day", "TTS voice playback engine", "Web visual dictionary", "No 3D canvas player"]
    },
    {
      id: "pro",
      name: "Pro Learner",
      price: "$9",
      desc: "For intermediate signers needing sequence models",
      features: ["500 queries/day", "Spatial-Temporal Transformer", "3D Dictionary visual player", "Drag-to-rotate hand views"]
    },
    {
      id: "developer",
      name: "Developer",
      price: "$49",
      desc: "For engineers needing unlimited API key generation",
      features: ["Unlimited queries/day", "DDPM Diffusion Synthesizer", "Custom Landmark Recorder", "Secure REST API key provisioning"]
    }
  ];

  grid.innerHTML = plans.map(p => {
    const isActive = p.id === userPlan;
    let btnHtml = "";
    if (isActive) {
      btnHtml = `<button class="pricing-btn current" disabled>Active Tier</button>`;
    } else {
      btnHtml = `<button class="pricing-btn upgrade" onclick="triggerCheckout('${p.id}')">Subscribe to ${p.name}</button>`;
    }
    return `
      <div class="pricing-card${isActive ? ' active' : ''}">
        <h3 class="pricing-title">${p.name}</h3>
        <div class="pricing-price">${p.price}<span>/month</span></div>
        <p class="pricing-desc">${p.desc}</p>
        <ul class="pricing-features">
          ${p.features.map(f => `<li>${f}</li>`).join("")}
        </ul>
        ${btnHtml}
      </div>`;
  }).join("");
}

window.triggerCheckout = async function(plan) {
  if (!currentUser) {
    closeSubscriptionModal();
    showAuthModal();
    showToast("Please sign in to upgrade subscription.", "warning");
    return;
  }
  try {
    const res = await fetch(`${activeApiBaseUrl}/payment/checkout`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ plan })
    });
    const data = await res.json();
    if (data.success && data.checkout_url) {
      showToast("Redirecting to Mock Stripe sandbox...", "info");
      SoundFX.playClick();
      // Redirect to simulated Stripe redirect url
      setTimeout(() => {
        window.location.href = data.checkout_url;
      }, 800);
    }
  } catch (err) {
    showToast("Stripe sandbox offline.", "error");
  }
};

// ==========================================
// GAMIFIED PRACTICE ENGINE (CHALLENGE LOOP)
// ==========================================
const practiceModeToggleBtn = document.getElementById("practiceModeToggleBtn");
const practiceCard = document.getElementById("practiceCard");
const challengeTargetEl = document.getElementById("challengeTarget");
const challengeTipBtn = document.getElementById("challengeTipBtn");
const practiceScoreEl = document.getElementById("practiceScore");
const practiceStreakEl = document.getElementById("practiceStreak");
const skipChallengeBtn = document.getElementById("skipChallengeBtn");

practiceModeToggleBtn.addEventListener("click", () => {
  // Check authorization gate
  if (currentUser) {
    const plan = currentUser.plan || "free";
    if (plan === "free") {
      showToast("Upgrade to Pro or Developer to unlock Practice Challenges!", "warning");
      openSubscriptionModal();
      return;
    }
  } else {
    showAuthModal();
    showToast("Please sign in to practice.", "warning");
    return;
  }

  practiceMode = !practiceMode;
  practiceCard.style.display = practiceMode ? "block" : "none";
  practiceModeToggleBtn.classList.toggle("active", practiceMode);
  practiceModeToggleBtn.innerText = practiceMode ? "Exit Practice" : "Practice Mode";
  
  if (practiceMode) {
    practiceScore = 0;
    practiceStreak = 0;
    challengeMatchCounter = 0;
    updatePracticeStats();
    loadNextChallenge();
    showToast("Practice Mode started!", "success");
    SoundFX.playClick();
  }
});

function loadNextChallenge() {
  const old = currentChallenge;
  let next = old;
  while (next === old) {
    next = CHALLENGES_POOL[Math.floor(Math.random() * CHALLENGES_POOL.length)];
  }
  currentChallenge = next;
  challengeTargetEl.innerText = currentChallenge;
  challengeMatchCounter = 0;
}

function updatePracticeStats() {
  practiceScoreEl.innerText = practiceScore;
  practiceStreakEl.innerText = `🔥 ${practiceStreak}`;
}

skipChallengeBtn.addEventListener("click", () => {
  loadNextChallenge();
  practiceStreak = 0;
  updatePracticeStats();
  showToast("Skipped challenge.", "info");
  SoundFX.playClick();
});

challengeTipBtn.addEventListener("click", () => {
  // Simulate clicking the visualize button in dictionary
  openDictionaryAndAnimate(currentChallenge);
});

function checkPracticeMatch(predictionLabel) {
  if (!practiceMode) return;
  
  if (predictionLabel.toUpperCase() === currentChallenge.toUpperCase()) {
    challengeMatchCounter++;
    if (challengeMatchCounter >= 3) { // 3 consecutive matches to complete
      practiceScore += 10;
      practiceStreak++;
      updatePracticeStats();
      
      // Trigger success flash
      const flash = document.getElementById("successFlash");
      flash.classList.add("active");
      setTimeout(() => flash.classList.remove("active"), 700);
      
      SoundFX.playSuccess();
      showToast(`Correct! +10 points`, "success");
      loadNextChallenge();
    }
  } else {
    challengeMatchCounter = 0;
  }
}

// ==========================================
// EMBEDDED 3D DICTIONARY PREVIEW PLAYER
// ==========================================
const dictVisualizerBox = document.getElementById("dictVisualizerBox");
const dictPlayPauseBtn = document.getElementById("dictPlayPauseBtn");
const dictCloseVisBtn = document.getElementById("dictCloseVisBtn");
const dictCanvas = document.getElementById("dictCanvas");
const dctx = dictCanvas.getContext("2d");

let dictAnimFrames = [];
let dictFrameIndex = 0;
let dictIsPlaying = false;
let dictTimer = null;

// Projection Rotation values
let rotationX = -0.3; // pitch
let rotationY = 0.2;  // yaw
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;

// Setup Drag-to-Rotate handlers
function setup3DDragControls(canvas) {
  canvas.addEventListener("mousedown", (e) => {
    isDragging = true;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
  });
  canvas.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const deltaX = e.clientX - lastMouseX;
    const deltaY = e.clientY - lastMouseY;
    
    rotationY += deltaX * 0.01;
    rotationX += deltaY * 0.01;
    
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
    
    if (!dictIsPlaying && dictAnimFrames.length > 0) {
      render3DFrame(dictCanvas, dctx, dictAnimFrames[dictFrameIndex]);
    }
  });
  window.addEventListener("mouseup", () => {
    isDragging = false;
  });
  
  // Touch support
  canvas.addEventListener("touchstart", (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      lastMouseX = e.touches[0].clientX;
      lastMouseY = e.touches[0].clientY;
    }
  });
  canvas.addEventListener("touchmove", (e) => {
    if (!isDragging || e.touches.length !== 1) return;
    const deltaX = e.touches[0].clientX - lastMouseX;
    const deltaY = e.touches[0].clientY - lastMouseY;
    
    rotationY += deltaX * 0.01;
    rotationX += deltaY * 0.01;
    
    lastMouseX = e.touches[0].clientX;
    lastMouseY = e.touches[0].clientY;
    
    if (!dictIsPlaying && dictAnimFrames.length > 0) {
      render3DFrame(dictCanvas, dctx, dictAnimFrames[dictFrameIndex]);
    }
  });
  canvas.addEventListener("touchend", () => {
    isDragging = false;
  });
}
setup3DDragControls(dictCanvas);

// Projection formula for 3D landmarks
function render3DFrame(canvas, ctxNode, frame3D) {
  const W = canvas.width;
  const H = canvas.height;
  const cx = W / 2;
  const cy = H / 2 + 10;
  
  ctxNode.clearRect(0, 0, W, H);
  
  // Render grid background
  ctxNode.strokeStyle = "rgba(168, 85, 247, 0.05)";
  ctxNode.lineWidth = 1;
  for (let x = 0; x < W; x += 30) {
    ctxNode.beginPath(); ctxNode.moveTo(x, 0); ctxNode.lineTo(x, H); ctxNode.stroke();
  }
  for (let y = 0; y < H; y += 30) {
    ctxNode.beginPath(); ctxNode.moveTo(0, y); ctxNode.lineTo(W, y); ctxNode.stroke();
  }
  
  if (!frame3D || frame3D.length < 21) return;
  
  const wristX = frame3D[0][0];
  const wristY = frame3D[0][1];
  const wristZ = frame3D[0][2];
  
  const centered = frame3D.map(([x, y, z]) => [x - wristX, y - wristY, z - wristZ]);
  
  // Rotate around Y-axis (Yaw)
  const cosY = Math.cos(rotationY);
  const sinY = Math.sin(rotationY);
  // Rotate around X-axis (Pitch)
  const cosX = Math.cos(rotationX);
  const sinX = Math.sin(rotationX);
  
  const rotated = centered.map(([x, y, z]) => {
    // Y-rotation
    const x1 = x * cosY - z * sinY;
    const z1 = x * sinY + z * cosY;
    // X-rotation
    const y2 = y * cosX - z1 * sinX;
    return [x1, y2];
  });
  
  // Calculate scaling
  let maxDist = 0;
  for (const [x, y] of rotated) {
    const dist = Math.sqrt(x * x + y * y);
    if (dist > maxDist) maxDist = dist;
  }
  if (maxDist < 1e-6) maxDist = 1.0;
  
  const scale = 80 / maxDist;
  const coords2D = rotated.map(([x, y]) => [cx + x * scale, cy + y * scale]);
  
  // Draw connectors
  ctxNode.lineWidth = 3.0;
  ctxNode.strokeStyle = "#a855f7"; // Neon purple
  ctxNode.shadowColor = "#a855f7";
  ctxNode.shadowBlur = 8;
  
  for (const [i, j] of HAND_CONNECTIONS) {
    const [x1, y1] = coords2D[i];
    const [x2, y2] = coords2D[j];
    ctxNode.beginPath();
    ctxNode.moveTo(x1, y1);
    ctxNode.lineTo(x2, y2);
    ctxNode.stroke();
  }
  
  // Draw joints
  ctxNode.shadowBlur = 0;
  for (let i = 0; i < coords2D.length; i++) {
    const [x, y] = coords2D[i];
    ctxNode.beginPath();
    ctxNode.arc(x, y, i === 0 ? 6 : 3.5, 0, 2 * Math.PI);
    ctxNode.fillStyle = i === 0 ? "#ef4444" : "#22c55e";
    ctxNode.fill();
    ctxNode.strokeStyle = "#fff";
    ctxNode.lineWidth = 1;
    ctxNode.stroke();
  }
  
  // Display text rotated values
  ctxNode.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctxNode.font = "9px monospace";
  ctxNode.fillText(`Pitch: ${(rotationX*180/Math.PI).toFixed(0)}° Yaw: ${(rotationY*180/Math.PI).toFixed(0)}°`, 10, 18);
}

// MediaPipe Connection Pairs
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
  [0, 5], [5, 6], [6, 7], [7, 8],       // Index
  [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
  [9, 13], [13, 14], [14, 15], [15, 16],// Ring
  [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
  [0, 17]                               // Palm base
];

async function animateDictionarySign(word) {
  // Check authorization gate
  if (currentUser) {
    const plan = currentUser.plan || "free";
    if (plan === "free") {
      showToast("Upgrade to Pro to animate signs inside the dictionary!", "warning");
      openSubscriptionModal();
      return;
    }
  } else {
    showAuthModal();
    showToast("Please sign in to animate signs.", "warning");
    return;
  }

  dictVisualizerBox.style.display = "flex";
  dictIsPlaying = false;
  if (dictTimer) clearInterval(dictTimer);
  
  try {
    const res = await fetch(`${activeApiBaseUrl}/synthesize_sign`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ prompt: word })
    });
    if (!res.ok) throw new Error("API Offline");
    const data = await res.json();
    dictAnimFrames = data.keypoints_3d;
    dictFrameIndex = 0;
    playDictFrames();
  } catch (err) {
    // Local fallback trajectory generator
    dictAnimFrames = generateLocalTrajectoryFallback(word);
    dictFrameIndex = 0;
    playDictFrames();
  }
}

function playDictFrames() {
  dictIsPlaying = true;
  dictPlayPauseBtn.innerText = "Pause";
  
  dictTimer = setInterval(() => {
    if (dictAnimFrames.length === 0) return;
    render3DFrame(dictCanvas, dctx, dictAnimFrames[dictFrameIndex]);
    dictFrameIndex = (dictFrameIndex + 1) % dictAnimFrames.length;
  }, 75);
}

dictPlayPauseBtn.addEventListener("click", () => {
  if (dictIsPlaying) {
    dictIsPlaying = false;
    dictPlayPauseBtn.innerText = "Play";
    if (dictTimer) clearInterval(dictTimer);
  } else {
    playDictFrames();
  }
  SoundFX.playClick();
});

dictCloseVisBtn.addEventListener("click", () => {
  dictVisualizerBox.style.display = "none";
  dictIsPlaying = false;
  if (dictTimer) clearInterval(dictTimer);
  SoundFX.playClick();
});

function openDictionaryAndAnimate(word) {
  dictModal.classList.remove("hidden");
  dictSearchInput.value = word;
  renderDictionary();
  animateDictionarySign(word);
}

function generateLocalTrajectoryFallback(word) {
  // Generates wave-like palm animation in JS for standalone preview
  const frames = [];
  const basePalm = [
    [0.0, 0.0, 0.0], [0.08, -0.05, 0.0], [0.14, -0.12, 0.0], [0.18, -0.18, 0.0], [0.22, -0.22, 0.0],
    [0.05, -0.25, 0.0], [0.07, -0.35, 0.0], [0.08, -0.42, 0.0], [0.09, -0.48, 0.0],
    [0.0, -0.26, 0.0], [0.0, -0.37, 0.0], [0.0, -0.45, 0.0], [0.0, -0.52, 0.0],
    [-0.05, -0.24, 0.0], [-0.07, -0.34, 0.0], [-0.08, -0.41, 0.0], [-0.09, -0.47, 0.0],
    [-0.10, -0.21, 0.0], [-0.13, -0.29, 0.0], [-0.15, -0.35, 0.0], [-0.17, -0.40, 0.0]
  ];
  const hash = word.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const freq = 1.0 + (hash % 3) * 0.5;
  for (let t = 0; t < 20; t++) {
    const progress = t / 20.0;
    const frame = basePalm.map(pt => [...pt]);
    const wave = Math.sin(progress * Math.PI * 2 * freq) * 0.06;
    const lift = Math.sin(progress * Math.PI) * 0.08;
    for (let i = 0; i < frame.length; i++) {
      frame[i][0] += wave;
      if (i >= 5) frame[i][1] -= lift;
    }
    frames.push(frame);
  }
  return frames;
}

// Hook auth trigger buttons
document.getElementById("loginBtn").addEventListener("click", () => {
  showAuthModal();
  SoundFX.playClick();
});
userChipBtn.addEventListener("click", () => {
  openProfileModal();
  SoundFX.playClick();
});

// ==========================================
// RESILIENT CAMERA INITIALIZATION
// ==========================================
async function startCamera() {
  if (!hands) {
    setStatus("red", "MediaPipe failed to load");
    if (videoOverlay) {
      videoOverlay.classList.remove("hidden");
      const messageEl = videoOverlay.querySelector(".overlay-msg");
      if (messageEl) {
        messageEl.innerText = "MediaPipe scripts could not load. Check your internet connection.";
      }
    }
    return;
  }

  setStatus("yellow", "Requesting Camera Access...");

  if (typeof Camera !== "undefined") {
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
  }

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
    if (videoOverlay) {
      videoOverlay.classList.remove("hidden");
      const messageEl = videoOverlay.querySelector(".overlay-msg");
      if (messageEl) {
        messageEl.innerText = "Camera permission denied or webcam unavailable.";
      }
    }
  }
}

// ==========================================
// CUSTOM CANVAS LANDMARK VISUALIZER
// ==========================================
function drawStyledLandmarks(ctx, landmarks) {
  const w = canvasElement.width;
  const h = canvasElement.height;

  // Draw connectors
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
// LANDMARK NORMALIZATION (MUST MATCH PYTHON)
// ==========================================
function normalizeKeypoints(landmarks) {
  const kp = [];
  for (let i = 0; i < 21; i++) {
    kp.push(landmarks[i].x, landmarks[i].y, landmarks[i].z);
  }

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

  const normalized = [];
  for (let i = 0; i < translated.length; i++) {
    normalized.push(translated[i] / maxDist);
  }
  return normalized;
}

// ==========================================
// BACKEND PREDICTION FETCH
// ==========================================
async function sendToBackend(keypoints) {
  // Check authorization
  if (!authToken) {
    resetPredictionDisplay("Sign In to recognize signs");
    return;
  }

  const startTime = performance.now();
  
  sequenceBuffer.push(keypoints);
  if (sequenceBuffer.length > 16) {
    sequenceBuffer.shift();
  }

  const isSeqMode = selectedModelMode === "transformer";
  
  const payload = isSeqMode
    ? { sequence: sequenceBuffer.length >= 16 ? sequenceBuffer : Array(16).fill(keypoints) }
    : { keypoints };
  
  try {
    const res = await fetch(activeApiUrl, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (res.status === 401) {
      doLogout();
      showToast("Session expired. Please sign in again.", "warning");
      return;
    }
    if (res.status === 403) {
      showToast("Upgrade required for sequence recognition.", "warning");
      openSubscriptionModal();
      return;
    }
    if (res.status === 429) {
      showToast("Daily prediction limit reached! Please upgrade your plan.", "error");
      openSubscriptionModal();
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const roundtripLatency = Math.round(performance.now() - startTime);

    updatePredictionDisplay(data, roundtripLatency);
    setStatus("green", `Tracking Active (${data.model || "AI Model"})`);
    
    // Check practice mode target match
    if (practiceMode && data.prediction) {
      checkPracticeMatch(data.prediction);
    }
  } catch (err) {
    setStatus("yellow", "API Offline...");
    latencyPillEl.innerText = "-";
    const now = Date.now();
    if (now - lastBackendCheckTime > BACKEND_RECHECK_MS) {
      lastBackendCheckTime = now;
      checkBackendConnection();
    }
  }
}

// ==========================================
// UI DISPLAY UPDATER
// ==========================================
function updatePredictionDisplay(data, latencyMs) {
  const smoothed = smoothPrediction(data);
  currentPrediction = smoothed.label;
  currentConfidence = smoothed.confidence;
  stablePrediction = smoothed.isStable ? smoothed.label : "-";
  stableConfidence = smoothed.isStable ? smoothed.confidence : 0;

  predictedLetterEl.innerText = smoothed.isStable ? stablePrediction : currentPrediction;
  confidencePercentEl.innerText = `${currentConfidence}%`;
  confidenceBarEl.style.width = `${currentConfidence}%`;
  handStateLabelEl.innerText = smoothed.isStable
    ? "Stable Letter Detected"
    : "Tracking... hold sign steady";
  latencyPillEl.innerText = `${latencyMs} ms`;

  if (smoothed.top3 && smoothed.top3.length > 0) {
    top3ListEl.innerHTML = smoothed.top3
      .map(
        (c) => `
      <div class="top3-item">
        <span class="lbl">${c.label}</span>
        <span class="prob">${c.probability.toFixed(1)}%</span>
      </div>`
      )
      .join("");
  }

  // Audio Speech Synthesis for changes with high confidence (>80%)
  if (ttsEnabled && smoothed.isStable && stableConfidence >= 80 && stablePrediction !== lastSpokenLetter) {
    speakText(stablePrediction);
    lastSpokenLetter = stablePrediction;
  }
}

function smoothPrediction(data) {
  const candidates = Array.isArray(data.top_3) && data.top_3.length > 0
    ? data.top_3
    : [{ label: data.prediction, probability: data.confidence }];

  predictionHistory.push(candidates.map((item) => ({
    label: item.label,
    probability: Number(item.probability) || 0
  })));

  if (predictionHistory.length > PREDICTION_HISTORY_LIMIT) {
    predictionHistory.shift();
  }

  const scoreByLabel = new Map();
  const voteByLabel = new Map();

  for (const frameCandidates of predictionHistory) {
    const best = frameCandidates[0];
    if (best) {
      voteByLabel.set(best.label, (voteByLabel.get(best.label) || 0) + 1);
    }

    for (const candidate of frameCandidates) {
      scoreByLabel.set(
        candidate.label,
        (scoreByLabel.get(candidate.label) || 0) + candidate.probability
      );
    }
  }

  const ranked = Array.from(scoreByLabel.entries())
    .map(([label, score]) => ({
      label,
      probability: (score / predictionHistory.length) * 100,
      votes: voteByLabel.get(label) || 0
    }))
    .sort((a, b) => b.probability - a.probability)
    .slice(0, 3);

  const best = ranked[0] || {
    label: data.prediction || "-",
    probability: (Number(data.confidence) || 0) * 100,
    votes: 0
  };

  const isStable =
    best.probability >= MIN_STABLE_CONFIDENCE &&
    best.votes >= MIN_STABLE_VOTES;

  return {
    label: best.label,
    confidence: Math.round(best.probability),
    top3: ranked,
    isStable
  };
}

function resetPredictionDisplay(reason) {
  currentPrediction = "-";
  currentConfidence = 0;
  stablePrediction = "-";
  stableConfidence = 0;
  predictionHistory.length = 0;
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
  const target = (stablePrediction !== "-") ? stablePrediction : (currentPrediction !== "-" ? currentPrediction : "");
  if (target) {
    appendToSentence(target);
    SoundFX.playClick();
  }
});
spaceBtn.addEventListener("click", () => { appendToSentence(" "); SoundFX.playClick(); });
backspaceBtn.addEventListener("click", () => {
  const cur = sentenceDisplayEl.innerText;
  if (cur.length > 0) {
    sentenceDisplayEl.innerText = cur.slice(0, -1);
  }
  SoundFX.playClick();
});
clearBtn.addEventListener("click", () => { sentenceDisplayEl.innerText = ""; SoundFX.playClick(); });
speakSentenceBtn.addEventListener("click", () => {
  const text = sentenceDisplayEl.innerText.trim();
  if (text) {
    speakText(text);
    SoundFX.playClick();
  }
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
      <div class="dict-card-footer" style="display:flex;gap:8px">
        <button class="dict-btn-speak" type="button" data-speak="${escapeHtml(`${item.title}: ${item.desc}`)}">
          Pronounce
        </button>
        <button class="dict-btn-speak" type="button" style="background:var(--accent-purple);border-color:rgba(168,85,247,0.3)" onclick="animateDictionarySign('${escapeHtml(item.title)}')">
          Visualize 3D
        </button>
      </div>
    </div>`
    )
    .join("");

  dictCardsGrid.querySelectorAll("[data-speak]").forEach((btn) => {
    btn.addEventListener("click", () => speakText(btn.dataset.speak));
  });
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

if (dictToggleBtn && dictModal) {
  dictToggleBtn.addEventListener("click", () => {
    dictModal.classList.remove("hidden");
    renderDictionary();
    SoundFX.playClick();
  });
}

if (closeDictBtn && dictModal) {
  closeDictBtn.addEventListener("click", () => {
    dictModal.classList.add("hidden");
    SoundFX.playClick();
  });
}

if (dictModal) {
  dictModal.addEventListener("click", (e) => {
    if (e.target === dictModal) {
      dictModal.classList.add("hidden");
    }
  });
}

filterBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentDictCategory = btn.dataset.category;
    renderDictionary();
    SoundFX.playClick();
  });
});

if (dictSearchInput) {
  dictSearchInput.addEventListener("input", renderDictionary);
}

ttsToggleBtn.addEventListener("click", () => {
  ttsEnabled = !ttsEnabled;
  ttsToggleBtn.classList.toggle("active", ttsEnabled);
  ttsToggleBtn.innerText = ttsEnabled ? "Speech ON" : "Speech OFF";
  SoundFX.playClick();
});

const modelModeSelect = document.getElementById("modelModeSelect");
if (modelModeSelect) {
  modelModeSelect.addEventListener("change", (e) => {
    selectedModelMode = e.target.value;
    
    // Plan Gate check for sequence transformer
    if (selectedModelMode === "transformer" && currentUser) {
      const plan = currentUser.plan || "free";
      if (plan === "free") {
        showToast("Spatial-Temporal Transformer requires Pro subscription.", "warning");
        openSubscriptionModal();
        modelModeSelect.value = "mlp";
        selectedModelMode = "mlp";
        return;
      }
    } else if (selectedModelMode === "transformer" && !currentUser) {
      showAuthModal();
      showToast("Sign in to unlock Spatial-Temporal Transformer.", "warning");
      modelModeSelect.value = "mlp";
      selectedModelMode = "mlp";
      return;
    }

    activeApiUrl = `${activeApiBaseUrl}/${selectedModelMode === "transformer" ? "predict_sequence" : "predict"}`;
    setStatus("yellow", `Switched to ${selectedModelMode === "transformer" ? "Spatial-Temporal Transformer" : "Static MLP"} Model`);
    SoundFX.playClick();
  });
}

function speakText(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

// MediaPipe Hands loader
let hands = null;
if (typeof Hands !== "undefined") {
  hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
  });
  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.6,
    minTrackingConfidence: 0.6,
  });
  hands.onResults(onResults);
}

// Initialize
async function init() {
  await checkBackendConnection();
  
  // Restore authentication session
  const savedToken = localStorage.getItem("sign0_token");
  const savedUser = localStorage.getItem("sign0_user");
  if (savedToken && savedUser) {
    authToken = savedToken;
    currentUser = JSON.parse(savedUser);
    updateUserUI();
    loadMe();
  }

  // Check mock checkout callback parameters
  await handlePaymentRedirect();

  startCamera();
}

init();
