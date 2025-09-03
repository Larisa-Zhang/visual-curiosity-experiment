// ✅ main.js with camera-relative arrow key rotation and STL-style background
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const modelList = [
  'Set_10_elong_glossy_3.glb',
  'Set_10_elong_matte_2.glb',
  'Set_10_orig_glossy_1.glb',
  'Set_10_orig_matte_0.glb',
  'Set_12_elong_glossy_3.glb',
  'Set_12_elong_matte_2.glb',
  'Set_12_orig_glossy_1.glb',
  'Set_12_orig_matte_0.glb',
  'Set_13_elong_glossy_3.glb',
  'Set_13_elong_matte_2.glb',
  'Set_13_orig_glossy_1.glb',
  'Set_13_orig_matte_0.glb',
  'Set_15_elong_glossy_3.glb',
  'Set_15_elong_matte_2.glb',
  'Set_15_orig_glossy_1.glb',
  'Set_15_orig_matte_0.glb',
  'Set_16_elong_glossy_3.glb',
  'Set_16_elong_matte_2.glb',
  'Set_16_orig_glossy_1.glb',
  'Set_16_orig_matte_0.glb',
  'Set_17_elong_glossy_3.glb',
  'Set_17_elong_matte_2.glb',
  'Set_17_orig_glossy_1.glb',
  'Set_17_orig_matte_0.glb',
  'Set_18_elong_glossy_3.glb',
  'Set_18_elong_matte_2.glb',
  'Set_18_orig_glossy_1.glb',
  'Set_18_orig_matte_0.glb',
  'Set_19_elong_glossy_3.glb',
  'Set_19_elong_matte_2.glb',
  'Set_19_orig_glossy_1.glb',
  'Set_19_orig_matte_0.glb',
  'Set_1_elong_glossy_3.glb',
  'Set_1_elong_matte_2.glb',
  'Set_1_orig_glossy_1.glb',
  'Set_1_orig_matte_0.glb',
  'Set_20_elong_glossy_3.glb',
  'Set_20_elong_matte_2.glb',
  'Set_20_orig_glossy_1.glb',
  'Set_20_orig_matte_0.glb',
  'Set_2_elong_glossy_3.glb',
  'Set_2_elong_matte_2.glb',
  'Set_2_orig_glossy_1.glb',
  'Set_2_orig_matte_0.glb',
  'Set_4_elong_glossy_3.glb',
  'Set_4_elong_matte_2.glb',
  'Set_4_orig_glossy_1.glb',
  'Set_4_orig_matte_0.glb',
  'Set_5_elong_glossy_3.glb',
  'Set_5_elong_matte_2.glb',
  'Set_5_orig_glossy_1.glb',
  'Set_5_orig_matte_0.glb',
  'Set_7_elong_glossy_3.glb',
  'Set_7_elong_matte_2.glb',
  'Set_7_orig_glossy_1.glb',
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
let currentModelName = '';
const loader = new GLTFLoader();

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xcfcfcf); 
scene.fog = new THREE.Fog(0x72645b, 2, 15);

// 添加 STL 风格地面
const plane = new THREE.Mesh(
  new THREE.PlaneGeometry(40, 40),
  new THREE.MeshPhongMaterial({ color: 0xcbcbcb, specular: 0x474747 })
);
plane.rotation.x = -Math.PI / 2;
plane.position.y = -100;
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
  directionalLight.castShadow = true;
  const d = 1;
  directionalLight.shadow.camera.left = -d;
  directionalLight.shadow.camera.right = d;
  directionalLight.shadow.camera.top = d;
  directionalLight.shadow.camera.bottom = -d;
  directionalLight.shadow.camera.near = 1;
  directionalLight.shadow.camera.far = 4;
  directionalLight.shadow.bias = -0.002;
  scene.add(directionalLight);
}

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 0, 1);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
renderer.setAnimationLoop(() => {
  renderer.render(scene, camera);
});

function loadModel(path) {
  if (model) {
    scene.remove(model);
    model = null;
  }
  currentModelName = path;
  loader.load(`./models/${path}`, (gltf) => {
    model = gltf.scene;
    model.scale.set(0.4, 0.4, 0.4);
    model.position.set(0, 0, -2);
    //hlutest

    scene.add(model);
    console.log(`✅ 模型 ${path} 加载成功`);
  }, undefined, (err) => {
    console.error(`❌ 模型加载失败:`, err);
  });
}

function loadRandomModel() {
  const randomModel = modelList[Math.floor(Math.random() * modelList.length)];
  loadModel(randomModel);
}

function generateFilename(groupId, suffix) {
  return `${groupId}_${suffix}.png`;
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
  loadModel('Set_1_elong_glossy_3.glb');
});
