import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';


// === Heatmap ===
function toDegNorm(rad) {
  const deg = THREE.MathUtils.radToDeg(rad);
  return (deg % 360 + 360) % 360; // 0..360
}
function wrap180(deg) { // 350 -> -10, 91 -> -179, etc.
  return ((deg + 180) % 360 + 360) % 360 - 180;
}
// World-frame yaw/pitch (Euler order YXZ)
function getWorldYPRDeg(obj) {
  const q = new THREE.Quaternion();
  obj.getWorldQuaternion(q);
  const e = new THREE.Euler(0, 0, 0, 'YXZ'); // yaw=Y, pitch=X, roll=Z
  e.setFromQuaternion(q, 'YXZ');
  return { yaw: toDegNorm(e.y), pitch: toDegNorm(e.x), roll: toDegNorm(e.z) };
}


/* =========================
   YPR CONTROL (new)
   - setWorldYPR(): set object's WORLD yaw/pitch/roll (deg)
   - makeYPRPanel(): small UI panel (Apply + A/B roll toggle)
   - 'L' key: quick prompt for yaw,pitch,roll
========================= */
const d2r = THREE.MathUtils.degToRad;

function quatFromYPRDeg(yawDeg, pitchDeg, rollDeg) {
  const e = new THREE.Euler(d2r(pitchDeg), d2r(yawDeg), d2r(rollDeg), 'YXZ');
  const q = new THREE.Quaternion();
  q.setFromEuler(e);
  return q;
}

function setWorldYPR(obj, yawDeg, pitchDeg, rollDeg) {
  const qTargetWorld = quatFromYPRDeg(yawDeg, pitchDeg, rollDeg);
  const qParentWorld = new THREE.Quaternion();
  if (obj.parent) obj.parent.getWorldQuaternion(qParentWorld);
  const qLocal = qParentWorld.clone().invert().multiply(qTargetWorld);
  obj.quaternion.copy(qLocal);
}

// build once
let __yprPanelBuilt = false;
function makeYPRPanel(targetObj) {
  if (__yprPanelBuilt) return;
  __yprPanelBuilt = true;

  const panel = document.createElement('div');
  panel.style.cssText = `
    position:fixed; top:12px; left:12px; z-index:9999;
    background:#111c; color:#fff; padding:10px 12px; border-radius:10px;
    font:12px/1.2 system-ui, sans-serif; backdrop-filter: blur(6px);
    display:flex; gap:8px; align-items:center;
  `;
  panel.innerHTML = `
    <span style="opacity:.8">Yaw:</span><input id="y_in" type="number" value="0" step="1" style="width:60px">
    <span style="opacity:.8">Pitch:</span><input id="p_in" type="number" value="0" step="1" style="width:60px">
    <span style="opacity:.8">Roll:</span><input id="r_in" type="number" value="0" step="1" style="width:60px">
    <button id="apply_btn">Apply</button>
    <span style="margin-left:6px; opacity:.8">A/B Roll:</span>
    <input id="rA_in" type="number" value="0" step="1" style="width:60px">
    <input id="rB_in" type="number" value="90" step="1" style="width:60px">
    <button id="toggle_btn">Toggle</button>
  `;
  document.body.appendChild(panel);

  const yawEl   = panel.querySelector('#y_in');
  const pitchEl = panel.querySelector('#p_in');
  const rollEl  = panel.querySelector('#r_in');
  const rAEl    = panel.querySelector('#rA_in');
  const rBEl    = panel.querySelector('#rB_in');

  panel.querySelector('#apply_btn').onclick = () => {
    const yaw = parseFloat(yawEl.value) || 0;
    const pitch = parseFloat(pitchEl.value) || 0;
    const roll = parseFloat(rollEl.value) || 0;
    if (targetObj) setWorldYPR(targetObj, yaw, pitch, roll);
  };

  let useA = true;
  panel.querySelector('#toggle_btn').onclick = () => {
    const yaw = parseFloat(yawEl.value) || 0;
    const pitch = parseFloat(pitchEl.value) || 0;
    const rA = parseFloat(rAEl.value) || 0;
    const rB = parseFloat(rBEl.value) || 0;
    const r = useA ? rA : rB;
    if (targetObj) setWorldYPR(targetObj, yaw, pitch, r);
    rollEl.value = r;
    useA = !useA;
  };

  // keep the panel from stealing arrow keys focus
  panel.addEventListener('focusin', () => renderer?.domElement?.focus?.());
}

window.addEventListener('keydown', (e) => {
  if (e.key.toLowerCase() === 'l' && model) {
    const s = prompt('Enter yaw,pitch,roll (deg):', '0,0,0');
    if (!s) return;
    const [yaw, pitch, roll] = s.split(',').map(v => parseFloat(v.trim()) || 0);
    setWorldYPR(model, yaw, pitch, roll);
  }
});
/* ===== end YPR CONTROL ===== */



// One id to group this run (persistent across the whole experiment)
let sessionId = localStorage.getItem('sessionId') || `RUN-${Date.now()}`;
localStorage.setItem('sessionId', sessionId);

function getOrCreateSessionId() {
  let id = localStorage.getItem('sessionId');
  if (!id) {
    // Ask experimenter or participant
    id = prompt("Enter Session ID (e.g., P001, TestA, etc.):");
    if (!id) {
      // fallback if user just presses cancel
      id = `run-${Date.now()}`;
    }
    localStorage.setItem('sessionId', id);
  }
  return id;
}



// 🔄 Auto-discover all GLB models under /public/models
const modules = import.meta.glob('/public/models/*.glb', { as: 'url', eager: true });
const discoveredModels = Object.entries(modules).map(([path, url]) => {
  const name = path.split('/').pop();
  return { name, url };
});
const nameToUrl = new Map(discoveredModels.map(m => [m.name, m.url]));
const modelList = discoveredModels.map(m => m.name);
console.log(`✅ Discovered ${modelList.length} models:`, modelList[1]);


const modules_screenshot = import.meta.glob('/public/output_pngs/*.png', { as: 'url', eager: true });
const discoveredModels_screenshot = Object.entries(modules_screenshot).map(([path, url]) => {
  const name = path.split('/').pop();
  return { name, url };
});
const nameToUrl_screenshot = new Map(discoveredModels_screenshot.map(m => [m.name, m.url]));
const modelList_screenshot = discoveredModels_screenshot.map(m => m.name);
console.log(`✅ Discovered ${modelList_screenshot.length} models:`, modelList_screenshot[1]);


let model = null;
let countdown = 1000000000;
let countdownInterval = null;
let autoSwitchTimeout = null;
let currentModelName = '';
const loader = new GLTFLoader();
let interactionCount = 0;
const maxInteractions = 16;
let memoryTestRound = 1;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xcfcfcf);
//scene.fog = new THREE.Fog(0x72645b, 2, 15);
let modelSequence = [];
let seenModels = [];
let testModels = modelList.filter(m => m.startsWith('Foil'));
let currentIndex = 0;

//Show an axes helper on the model and update the HUD
let axesHelper = null;
let showAxes = false;
let lastDeltaForHud = { yaw: null, pitch: null, roll: null };

function resetModelSequence() {
  // 创建一个新的随机序列
  const remainingModels = modelList.filter(m => !seenModels.includes(m) && !m.startsWith('Foil'));
  modelSequence = [...remainingModels].slice(0, 16);
  for (let i = modelSequence.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [modelSequence[i], modelSequence[j]] = [modelSequence[j], modelSequence[i]];
  }
  currentIndex = 0;
  updateObjectsLeftUI();
}

function updateObjectsLeftUI() {
  const el = document.getElementById('objects-left');
  if (!el) return;

  // modelSequence is your shuffled 16 for this round
  const total = Math.min(16, modelSequence.length || 16);
  const left = Math.max(0, total - currentIndex);

  el.textContent = `${left} object${left === 1 ? '' : 's'} left`;
  // only show during the main module
  const mainVisible = document.getElementById('module-main')?.style.display !== 'none';
  el.style.display = mainVisible ? 'block' : 'none';
}



// 添加 STL 风格地面
const plane = new THREE.Mesh(
  new THREE.PlaneGeometry(40, 40),
  new THREE.MeshPhongMaterial({ color: 0xcbcbcb, specular: 0x474747 })
);
plane.rotation.x = -Math.PI / 2;
plane.position.y = -20;
plane.receiveShadow = true;
scene.add(plane);
scene.add(new THREE.HemisphereLight(0xffffff, 0xe0e0e0, 0.8));  // 柔和的天空光
// 天光 + 柔和地面反光

// 主阳光：来自摄像头左后上方
addShadowedLight(-10, 2, 3, 0xffffff, 2.8); // 阳光：白光，强度适中

// 补光：来自右后方
addShadowedLight(2, 1, 2, 0xffffff, 1.5); // 冷白弱补光



function addShadowedLight(x, y, z, color, intensity) {
  const directionalLight = new THREE.DirectionalLight(color, intensity);
  directionalLight.position.set(x, y, z);

  // ✅ enable shadow casting
  directionalLight.castShadow = true;

  // ✅ bigger shadow map = sharper, cleaner shadows
  directionalLight.shadow.mapSize.set(2048, 2048); // try 1024 on weaker GPUs

  // ✅ widen the shadow camera so shadows don’t get cut off
  const d = 10;  // much larger than before
  directionalLight.shadow.camera.left   = -d;
  directionalLight.shadow.camera.right  =  d;
  directionalLight.shadow.camera.top    =  d;
  directionalLight.shadow.camera.bottom = -d;
  directionalLight.shadow.camera.near   = 0.1;
  directionalLight.shadow.camera.far    = 50;

  // ✅ reduce shadow acne
  directionalLight.shadow.bias = -0.0005;

  scene.add(directionalLight);
  return directionalLight;
}

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 0, 1);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });//antialias: true (smooth jaggies)
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

renderer.domElement.tabIndex = 0;
renderer.domElement.style.outline = 'none'; // purely cosmetic
renderer.outputColorSpace = THREE.SRGBColorSpace;   // correct gamma curve for displays
renderer.toneMapping = THREE.ACESFilmicToneMapping; // cinematic filmic curve
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;// Shadow settings (soft, nicer looking)
renderer.shadowMap.type = THREE.PCFSoftShadowMap; // softer edges                // adjust brightness (try 0.9–1.5)

renderer.setAnimationLoop(() => {
  // live angles HUD
  if (showAxes && model) {
    const ang = getWorldYPRDeg(model);
    const yawEl   = document.getElementById('hud-yaw');
    const pitchEl = document.getElementById('hud-pitch');
    const rollEl  = document.getElementById('hud-roll');
    const dyEl    = document.getElementById('hud-dyaw');
    const dpEl    = document.getElementById('hud-dpitch');
    const drEl    = document.getElementById('hud-droll');

    if (yawEl)   yawEl.textContent   = ang.yaw.toFixed(2);
    if (pitchEl) pitchEl.textContent = ang.pitch.toFixed(2);
    if (rollEl)  rollEl.textContent  = ang.roll.toFixed(2);

    if (dyEl && lastDeltaForHud.yaw   !== null) dyEl.textContent = lastDeltaForHud.yaw.toFixed(2);
    if (dpEl && lastDeltaForHud.pitch !== null) dpEl.textContent = lastDeltaForHud.pitch.toFixed(2);
    if (drEl && lastDeltaForHud.roll  !== null) drEl.textContent = lastDeltaForHud.roll.toFixed(2); // ✅ fixed
  }

  renderer.render(scene, camera);
});

const pmrem = new THREE.PMREMGenerator(renderer);
pmrem.compileEquirectangularShader();

new EXRLoader()
  .setDataType(THREE.FloatType)
  .setPath('/hdrs/')
  .load('table_mountain_1_puresky_4k.exr', (exrTex) => {
    const envMap = pmrem.fromEquirectangular(exrTex).texture;
    scene.environment = envMap;
    scene.background = envMap;
    exrTex.dispose();
  }, undefined, (err) => {
    console.error('❌ exr 加载失败:', err);
  });


function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) >>> 0; // 保证正整数
  }
  return hash;
}

window.showModelList = () => {
  const listEl = document.getElementById('shown-models-list');
  const imageEl = document.getElementById('shown-models-images');
  if (!listEl || !imageEl) return;

  const topModels = modelSequence.slice(0, 16); // 实际展示过的模型（你展示了16个）
  const unseenModels = modelList.filter(name => !topModels.includes(name)); // 剩下的模型

  // 随机选 4 个 seen
  const seenSubset = [...topModels]
    .sort(() => Math.random() - 0.5)
    .slice(0, 4);

  // 随机选 4 个 unseen
  const unseenSubset = [...unseenModels]
    .sort(() => Math.random() - 0.5)
    .slice(0, 4);

  // 合并并打乱
  const testSet = [...seenSubset, ...unseenSubset]
    .sort(() => Math.random() - 0.5);

  imageEl.innerHTML = `
    <form id="guess-form">
      <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
        ${testSet.map((name, index) => {
          const imgName = name.replace('.glb', '.png');
          return `
            <div class="guess-block" data-model="${name}" style="flex: 0 1 calc(20% - 10px); text-align: center;">
              <img src="./public/output_pngs/${imgName}" style="width: 100%; max-width: 400px;" />
              <div style="margin-top: 5px;">
                <label>
                  <input type="checkbox" name="guess-${index}" />
                  I have seen this
                </label>
              </div>
              <div class="result-text" style="margin-top: 4px; height: 18px;"></div>
            </div>
          `;
        }).join('')}
      </div>
      <div style="text-align:center; margin-top: 10px;">
        <button type="submit">Submit</button>
      </div>
    </form>
  `;
};
async function sendInitRow(name, init) {
  try {
    const res = await fetch('api/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId,
        modelName: name,
        actionId: -1,
        initialAngles: { yaw: init.yaw, pitch: init.pitch },
        s_t_img: '',
        s_t1_img: '',
        imgData1: 'data:image/png;base64,',
        imgData2: 'data:image/png;base64,'
      })
    });

    if (!res.ok) throw new Error('Upload failed');
  } catch (e) {
    console.warn('Init row POST failed (non-fatal):', e);
  }
}


function loadModel(name) {
  // Remove old model(s)
  scene.children
    .filter(obj => obj.userData?.isModel)
    .forEach(obj => scene.remove(obj));

  currentModelName = name;                      // <-- this is what backend will log
  const url = nameToUrl.get(name);              // resolve the actual fetchable URL
  if (!url) {
    console.error('❌ URL not found for model:', name);
    return;
  }

  loader.load(url, (gltf) => {
    model = gltf.scene;
    model.userData.isModel = true;
    model.scale.set(0.5, 0.5, 0.5);
    model.position.set(0, 0, -2.5);
    // (keep your deterministic starting code if you like)
    const hashX = hashString('test'+name);
    const rotationsX = Math.floor(hashX % (360/5)*5);
    const angleRadX = THREE.MathUtils.degToRad(rotationsX);

    const hashY = hashString('test/' + name);
    const rotationsY = Math.floor(hashY % (360/5)*5);
    const angleRadY = THREE.MathUtils.degToRad(rotationsY);

    model.rotation.set(angleRadX, angleRadY, 0);

    // Cache initial Y/P and send a one-time init row (actionId = -1)
    const init = getWorldYPRDeg(model);
    model.userData.initialAngles = { yaw: init.yaw, pitch: init.pitch }; // (roll optional)

    sendInitRow(name, init); // ✅ 不需要 await，这只是 fire-and-forget

    scene.children
      .filter(obj => obj.userData?.isModel)
      .forEach(obj => scene.remove(obj));

    scene.add(model);

    // --- ✅ axes helper (object-local), sized to model, always on top ---
    model.updateWorldMatrix(true, true);
    const box = new THREE.Box3().setFromObject(model);
    const sz = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(sz.x, sz.y, sz.z) || 1;
    const axesLen = Math.max(1, maxDim * 0.8);
    axesHelper = new THREE.AxesHelper(axesLen);
    axesHelper.renderOrder = 9999;
    const mats = Array.isArray(axesHelper.material) ? axesHelper.material : [axesHelper.material];
    mats.forEach(m => { if (m) m.depthTest = false; });
    model.add(axesHelper);
    axesHelper.visible = showAxes;

    // --- ✅ build YPR panel once (points to current `model`) ---
    makeYPRPanel(model);

  }, undefined, (err) => {
    console.error('❌ 模型加载失败:', err);
  });
}



function loadRandomModel() {
  if (currentIndex >= maxInteractions) {
    currentIndex = 0;
    if (window.showModelList) window.showModelList();
    if (window.switchModule) {
      setTimeout(() => {
        window.switchModule('end');
        if (window.showModelList) window.showModelList();
        renderMemoryTest();  // ✅ 调用 memory test 展示函数
      }, 500);
    }
    return;
  }
  if (currentIndex >= modelSequence.length) {
    console.warn("📛 modelSequence 已经全部加载完");
    window.switchModule('model-run-out');

    return;
  }

  const name = modelSequence[currentIndex];
  console.warn(currentIndex, name);
  currentIndex++;
  updateObjectsLeftUI();
  countdown =10000001; // reset countdown
  updateStepCountdownUI();
  loadModel(name);
  seenModels.push(name);
  console.warn(findScreenShot(name));
}


window.resetMainModule = () => {
  resetModelSequence();        // 重置模型顺序和 index
  interactionCount = 0;
  currentIndex = 0        // 重置交互次数
  countdown = 10000001;             // 重置倒计时
  updateStepCountdownUI();
  loadRandomModel();          // 加载第一个模型
  clearInterval(countdownInterval);
  clearTimeout(autoSwitchTimeout);
};

function generateFilename(groupId, suffix) {
  return `${groupId}_${suffix}.png`;
}

//Test use (temporary show button)
const TEST_MODE = true;

function updateStepCountdownUI() {
  const nextButton = document.getElementById('load-random-model');
  if (countdown <= 1) {
    nextButton.style.display = 'block';  // ✅ 显示按钮
  } else {
    nextButton.style.display = 'none';   // ✅ 隐藏按钮
  }
  const el = document.getElementById('countdown-timer');
  if (countdown <= 0) {
    el.textContent = `${countdown} steps remaining`;
    return;
  } else {
    countdown--;
    if (el) el.textContent = `${countdown} steps remaining`;
  }

}


function getCameraRelativeAxes() {
  const direction = new THREE.Vector3();
  camera.getWorldDirection(direction);
  const worldUp = new THREE.Vector3(0, 1, 0);
  const cameraRight = new THREE.Vector3().crossVectors(direction, worldUp).normalize();
  const cameraUp = new THREE.Vector3().crossVectors(cameraRight, direction).normalize();
  return { cameraRight, cameraUp };
}

let isProcessing = false;

async function recordStepAndAct(actionId) {
  if (!model || isProcessing) return;
  if (countdown <= 0) return;
  isProcessing = true;

  try {
    const t_start_ms = Date.now();

    // BEFORE
    const before = getWorldYPRDeg(model);

    // BEFORE screenshot (disabled)
    const modelName = currentModelName;
    const timestamp = Date.now();
    const rand = Math.floor(Math.random() * 1e6);
    const groupId = `${timestamp}-${rand}`;
    const s_t_img = `${groupId}_before.png`;
    const imgData1 = "";

    // ROTATE
    const { cameraRight, cameraUp } = getCameraRelativeAxes();
    const step = THREE.MathUtils.degToRad(5);
    switch (actionId) {
      case 0: model.rotateOnWorldAxis(cameraRight, -step); break; // Up
      case 1: model.rotateOnWorldAxis(cameraRight,  step); break; // Down
      case 2: model.rotateOnWorldAxis(cameraUp,    -step); break; // Left
      case 3: model.rotateOnWorldAxis(cameraUp,     step); break; // Right
    }

    await new Promise(r => setTimeout(r, 50));

    // AFTER
    const after = getWorldYPRDeg(model);
    const delta = {
      yaw:   wrap180(after.yaw   - before.yaw),
      pitch: wrap180(after.pitch - before.pitch),
      roll:  wrap180(after.roll  - before.roll) // optional: track roll delta too
    };

    // ✅ update HUD delta here
    lastDeltaForHud = { yaw: delta.yaw, pitch: delta.pitch, roll: delta.roll };

    // AFTER screenshot (disabled)
    const s_t1_img = `${groupId}_after.png`;
    const imgData2 = "";

    const t_end_ms = Date.now();
    const duration_ms = t_end_ms - t_start_ms;

    // POST
    const res = await fetch('api/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId,
        modelName: currentModelName,
        actionId,
        s_t_img, s_t1_img, imgData1, imgData2,
        afterAngles: { yaw: after.yaw, pitch: after.pitch },
        deltaAngles: { yaw: delta.yaw, pitch: delta.pitch },
        t_start_ms, t_end_ms, duration_ms
      })
    });

    updateStepCountdownUI();
    if (!res.ok) throw new Error('Upload failed');

    console.log(`✅ Recorded: ${modelName}, ${s_t_img}, ${actionId}, ${s_t1_img}`);
  } catch (e) {
    console.error('❌ recordStepAndAct error:', e);
  } finally {
    // ✅ always clear lock so keys work again even after an error
    isProcessing = false;
  }
}


// 2) Only register the action when the key is released
document.addEventListener('keydown', (e) => {
  switch (e.key) {
    case 'ArrowUp':    recordStepAndAct(0); break;
    case 'ArrowDown':  recordStepAndAct(1); break;
    case 'ArrowLeft':  recordStepAndAct(2); break;
    case 'ArrowRight': recordStepAndAct(3); break;
  }
});


window.addEventListener('DOMContentLoaded', () => {
  countdown = 1000000000
  const button = document.getElementById('load-random-model');
  if (button) {
    button.addEventListener('click', loadRandomModel);
    updateObjectsLeftUI();
  }

  const chk = document.getElementById('show-axes');
  const hud = document.getElementById('angles-hud');
  if (chk && hud) {
    chk.addEventListener('change', () => {
      showAxes = chk.checked;
      hud.style.display = showAxes ? 'block' : 'none';
      if (axesHelper) axesHelper.visible = showAxes;

      // ✅ give the keyboard back to the canvas so Arrow keys keep working
      chk.blur();
      renderer.domElement.focus();
    });
  }
});


function findScreenShot(name) {
  // 把文件名前缀取出来（去掉 .后缀）
  const prefix = name.split('.')[0];
  for (let obj of modelList_screenshot) {
    if (obj.startsWith(prefix)) {
      return obj;
    }
  }
  return null;
}
function renderMemoryTest() {
  const topModels = modelSequence.slice(0, 16); // 展示过的模型
  const unseenModels = modelList.filter(name => !topModels.includes(name)); // 没看过的

  const seenSubset = [...topModels].sort(() => Math.random() - 0.5).slice(0, 4);
  const unseenSubset = [...unseenModels].sort(() => Math.random() - 0.5).slice(0, 4);
  const testSubSet = [...unseenModels].sort(() => Math.random() - 0.5).slice(0, 4);
  const testSet = [...seenSubset, ...testSubSet].sort(() => Math.random() - 0.5);

  const imageEl = document.getElementById('shown-models-images');
  if (!imageEl) return;

  imageEl.innerHTML = `
    <form id="guess-form">
      <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
        ${testSet.map((name, index) => {
          const imgName = findScreenShot(name);

          return `
            <div class="guess-block" data-model="${name}" style="flex: 0 1 calc(20% - 10px); text-align: center;">
              <img src="./public/output_pngs/${imgName}" style="width: 100%; max-width: 400px;" />
              <div style="margin-top: 5px;">
                <label>
                  <input type="checkbox" name="guess-${index}" />
                  I have seen this
                </label>
              </div>
              <div class="result-text" style="margin-top: 4px; height: 18px;"></div>
            </div>
          `;
        }).join('')}
      </div>
<div style="text-align: center; margin-top: 20px;">
  <button type="submit" id="submit-btn" style="margin-right: 20px;">Submit</button>
  <button type="button" id="next-memory-btn" style="display: none;">
    ${memoryTestRound === 1 ? 'Start Next Memory Test' : 'Start Next Round'}
  </button>
</div>


    </form>
  `;

  const nextBtn = document.getElementById('next-memory-btn');
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      // 清除所有 checkbox 勾选
      document.querySelectorAll('#guess-form input[type="checkbox"]').forEach(cb => cb.checked = false);
      // 清除结果显示
      document.querySelectorAll('.result-text').forEach(el => el.textContent = '');

      console.log('✅ Memory test next button clicked');

      if (memoryTestRound === 1) {
        memoryTestRound++;
        renderMemoryTest(); // 第二轮开始
      } else {
        memoryTestRound = 1;
        switchModule('main'); // 回到主界面
        window.resetMainModule && window.resetMainModule(); // 重置模型测试
      }
    });
  }
}

document.body.addEventListener('submit', (e) => {
  const submitBtn = document.getElementById('submit-btn');
  const nextBtn = document.getElementById('next-memory-btn');

  if (submitBtn) submitBtn.style.display = 'none';
  if (nextBtn) nextBtn.style.display = 'inline-block';
  if (e.target.id === 'guess-form') {
    e.preventDefault();

    const blocks = document.querySelectorAll('.guess-block');
    const results = [];

    blocks.forEach(block => {
      const modelName = block.dataset.model;
      const checkbox = block.querySelector('input[type=checkbox]');
      const resultEl = block.querySelector('.result-text');

      const guessed = checkbox.checked;
      const actuallySeen = modelSequence.includes(modelName);

      // UI 显示结果
      if (guessed === actuallySeen) {
        resultEl.textContent = '✅ Correct';
        resultEl.style.color = 'green';
      } else {
        resultEl.textContent = '❌ Incorrect';
        resultEl.style.color = 'red';
      }


      // ⬇️ 收集结果用于上传
      results.push({
        modelName,
        guessed,
        actuallySeen,
        correct: guessed === actuallySeen,
        memoryTestRound,
        timestamp: Date.now()
      });
    });

    // ⬆️ 发送到后端保存
    fetch('api/memory_result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId, results })
    }).then(res => {
      if (!res.ok) throw new Error('Failed to save memory results');
      console.log('✅ Memory test results uploaded');
    }).catch(err => {
      console.error('❌ Upload failed:', err);
    });
  }
});
