// ✅ main.js with camera-relative arrow key rotation and STL-style background
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';

const modelList = [
  'Set_10_elong_matte_2.glb',
  'Set_10_orig_matte_0.glb',
  'Set_12_elong_matte_2.glb',
  'Set_12_orig_glossy_1.glb',
  'Set_12_orig_matte_0.glb',
  'Set_13_elong_glossy_3.glb',
  'Set_13_orig_glossy_1.glb',
  'Set_13_orig_matte_0.glb',
  'Set_15_elong_glossy_3.glb',
  'Set_15_orig_matte_0.glb',
  'Set_16_elong_glossy_3.glb',
  'Set_17_elong_glossy_3.glb',
  'Set_17_orig_glossy_1.glb',
  'Set_18_orig_glossy_1.glb',
  'Set_18_orig_matte_0.glb',
  'Set_19_elong_matte_2.glb',
  'Set_19_orig_glossy_1.glb',
  'Set_1_elong_glossy_3.glb',
  'Set_1_orig_glossy_1.glb',
  'Set_1_orig_matte_0.glb',
  'Set_20_elong_matte_2.glb',
  'Set_20_orig_glossy_1.glb',
  'Set_20_orig_matte_0.glb',
  'Set_2_elong_glossy_3.glb',
  'Set_2_elong_matte_2.glb',
  'Set_2_orig_glossy_1.glb',
  'Set_2_orig_matte_0.glb',
  'Set_4_elong_matte_2.glb',
  'Set_4_orig_glossy_1.glb',
  'Set_4_orig_matte_0.glb',
  'Set_5_elong_glossy_3.glb',
  'Set_5_orig_glossy_1.glb',
  'Set_5_orig_matte_0.glb',
  'Set_7_elong_glossy_3.glb',
  'Set_7_orig_matte_0.glb',
  'Set_8_elong_glossy_3.glb',
  'Set_8_elong_matte_2.glb',
  'Set_8_orig_glossy_1.glb',
  'Set_8_orig_matte_0.glb',
  'Set_9_elong_glossy_3.glb',
  'Set_9_elong_matte_2.glb',
  'Set_9_orig_glossy_1.glb',
  'Set_9_orig_matte_0.glb',
];
let model = null;
let countdown = 60;
let countdownInterval = null;
let autoSwitchTimeout = null;
let currentModelName = '';
const loader = new GLTFLoader();
let interactionCount = 0;
const maxInteractions = 10;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xcfcfcf); 
//scene.fog = new THREE.Fog(0x72645b, 2, 15);
let modelSequence = [];
let currentIndex = 0;

function resetModelSequence() {
  // 创建一个新的随机序列
  modelSequence = [...modelList];
  for (let i = modelSequence.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [modelSequence[i], modelSequence[j]] = [modelSequence[j], modelSequence[i]];
  }
  currentIndex = 0;
}

function loadNextModel() {
  if (currentIndex > 10) {
    console.log('🎯 已完成 10 个模型，跳转结束界面');
    if (window.switchModule) {
      window.switchModule('end');
    }
    return;
  }
  const nextModel = modelSequence[currentIndex];
  currentIndex++;
  loadModel(nextModel);
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
renderer.outputColorSpace = THREE.SRGBColorSpace;   // correct gamma curve for displays
renderer.toneMapping = THREE.ACESFilmicToneMapping; // cinematic filmic curve
renderer.toneMappingExposure = 1.0; 
renderer.shadowMap.enabled = true;// Shadow settings (soft, nicer looking)
renderer.shadowMap.type = THREE.PCFSoftShadowMap; // softer edges                // adjust brightness (try 0.9–1.5)
renderer.setAnimationLoop(() => {
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

  const top10 = modelSequence.slice(0, 10); // 实际展示过的模型
  const all10 = [...top10]; // 你也可以混合别的图形成干扰项

  // 打乱顺序（如果你想加干扰项就 push 一些没展示过的模型）
  for (let i = all10.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [all10[i], all10[j]] = [all10[j], all10[i]];
  }

  imageEl.innerHTML = `
    <form id="guess-form">
      <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
        ${all10.map((name, index) => {
          const imgName = name.replace('.glb', '.png');
          return `
            <div class="guess-block" data-model="${name}" style="flex: 0 1 calc(20% - 10px); text-align: center;">
              <img src="./images/${imgName}" style="width: 100%; max-width: 200px;" />
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
function loadModel(path) {
  scene.children
    .filter(obj => obj.userData.isModel)
    .forEach(obj => scene.remove(obj));
  currentModelName = path;
  loader.load(`./models/${path}`, (gltf) => {
    model = gltf.scene;
    model.scale.set(0.5, 0.5, 0.5);
    model.position.set(0, 0, -2.5);
    //hlutest


    const hashX = hashString(path);
    const rotationsX = hashX % (360/5);
    const angleRadX = THREE.MathUtils.degToRad(rotationsX * 5);


    
    const hashY = hashString('/'+path);
    const rotationsY = hashY % (360/5);
    const angleRadY = THREE.MathUtils.degToRad(rotationsY * 5);

    model.rotation.set(angleRadX,angleRadY, 0); // 绕 Y 轴转
    model.userData.isModel = true;
    interactionCount++;
    console.log(`👉 当前已交互 ${interactionCount} 次`);

    if (interactionCount > maxInteractions) {
      interactionCount = 0;
      if (window.showModelList) window.showModelList();
      if (window.switchModule) {
        window.switchModule('end');
      }
      return;
    }

    model.traverse(obj => {
      if (obj.isMesh) {
        obj.castShadow = true;    // model drops shadows onto floor / itself
        // obj.receiveShadow = true; // model can receive its own/self shadows
      }
    });

    scene.add(model);
    console.log(`✅ 模型 ${path} 加载成功`);
    startModelTimer();
  }, undefined, (err) => {
    console.error(`❌ 模型加载失败:`, err);
  });
}

function loadRandomModel() {
  loadNextModel();
}

window.resetMainModule = () => {
  resetModelSequence();        // 重置模型顺序和 index
  interactionCount = 0;        // 重置交互次数
  clearInterval(countdownInterval);
  clearTimeout(autoSwitchTimeout);
};

function generateFilename(groupId, suffix) {
  return `${groupId}_${suffix}.png`;
}


function startModelTimer() {
  clearInterval(countdownInterval);
  clearTimeout(autoSwitchTimeout);

  countdown = 10;
  updateCountdownUI();

  countdownInterval = setInterval(() => {
    countdown--;
    updateCountdownUI();
    if (countdown <= 0) clearInterval(countdownInterval);
  }, 1000);

  autoSwitchTimeout = setTimeout(() => {
    console.log("⏱️ 1分钟到，自动切换模型");
    loadRandomModel();
  }, 10000);
}

function updateCountdownUI() {
  const el = document.getElementById('countdown-timer');
  if (el) el.textContent = `${countdown}s`;
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

  isProcessing = true;

  const modelName = currentModelName;
  const timestamp = Date.now();
  const rand = Math.floor(Math.random() * 1e6);
  const groupId = `${timestamp}-${rand}`;

  const s_t_img = generateFilename(groupId, 'before');
  const imgData1 = renderer.domElement.toDataURL('image/png');

  const { cameraRight, cameraUp } = getCameraRelativeAxes();
  const step = THREE.MathUtils.degToRad(5);

  switch (actionId) {
    case 0: model.rotateOnWorldAxis(cameraRight, -step); break; // Up
    case 1: model.rotateOnWorldAxis(cameraRight, step); break;  // Down
    case 2: model.rotateOnWorldAxis(cameraUp, -step); break;    // Left
    case 3: model.rotateOnWorldAxis(cameraUp, step); break;     // Right
  }

  await new Promise(resolve => setTimeout(resolve, 50));

  const s_t1_img = generateFilename(groupId, 'after');
  const imgData2 = renderer.domElement.toDataURL('image/png');

  try {
    const res = await fetch('http://127.0.0.1:5000/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelName, s_t_img, s_t1_img, actionId, imgData1, imgData2 })
    });

    if (!res.ok) throw new Error('Upload failed');

    console.log(`✅ Recorded: ${modelName}, ${s_t_img}, ${actionId}, ${s_t1_img}`);
  } catch (e) {
    console.error('❌ Recording failed:', e);
  } finally {
    isProcessing = false;  // 解锁
  }
}

document.addEventListener('keydown', (event) => {
  switch (event.key) {
    case 'ArrowUp': recordStepAndAct(0); break;
    case 'ArrowDown': recordStepAndAct(1); break;
    case 'ArrowLeft': recordStepAndAct(2); break;
    case 'ArrowRight': recordStepAndAct(3); break;
  }
});

window.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('load-random-model');
  if (button) {
    button.addEventListener('click', loadRandomModel);
  }
  const button2 = document.getElementById('start-button');
  if (button2) {
    button2.addEventListener('click', loadRandomModel);
  }
  resetModelSequence();
});
document.body.addEventListener('submit', (e) => {
  if (e.target.id === 'guess-form') {
    e.preventDefault();

    const top10 = modelSequence.slice(0, 10); // 实际展示过的

    const blocks = document.querySelectorAll('.guess-block');
    blocks.forEach(block => {
      const modelName = block.dataset.model;
      const checkbox = block.querySelector('input[type=checkbox]');
      const resultEl = block.querySelector('.result-text');

      const guessed = checkbox.checked;
      const actuallySeen = top10.includes(modelName);

      if (guessed === actuallySeen) {
        resultEl.textContent = '✅ Correct';
        resultEl.style.color = 'green';
      } else {
        resultEl.textContent = '❌ Incorrect';
        resultEl.style.color = 'red';
      }
    });
  }
});