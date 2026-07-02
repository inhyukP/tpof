const appConfig = window.APP_CONFIG || {};
const state = {
  main: null,
  models: [],
  products: [],
};
const editors = new Map();
let nextImageId = 1;

const $ = (id) => document.getElementById(id);
const els = {};

function imageRecord(name, dataUrl) {
  return {
    id: `img-${nextImageId++}`,
    name,
    originalData: dataUrl,
    croppedData: dataUrl,
  };
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function showStatus(message, kind = "") {
  els.status.textContent = message;
  els.status.className = `status${kind ? ` ${kind}` : ""}`;
  els.status.classList.toggle("hidden", !message);
}

function setBusy(isBusy) {
  els.generateButton.disabled = isBusy;
  els.generateButton.textContent = isBusy ? "생성 중..." : "상세페이지 생성";
}

function makeButton(label, onClick, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  if (className) button.className = className;
  button.addEventListener("click", onClick);
  return button;
}

function initItemOptions() {
  const options = appConfig.itemOptions || ["NECKLACE", "EARRING", "RING", "BRACELET", "ANKLET", "직접입력"];
  els.itemSelect.replaceChildren();
  for (const option of options) {
    const node = document.createElement("option");
    node.value = option;
    node.textContent = option;
    els.itemSelect.appendChild(node);
  }
  els.itemSelect.value = "NECKLACE";
  toggleCustomItem();
}

function toggleCustomItem() {
  els.customItemWrap.classList.toggle("hidden", els.itemSelect.value !== "직접입력");
}

function getFields() {
  const selectedItem = els.itemSelect.value;
  return {
    product_name: els.productName.value,
    item_text: selectedItem === "직접입력" ? els.customItem.value : selectedItem,
    material_text: els.materialText.value,
    size_text: els.sizeText.value,
    pendant_text: els.pendantText.value,
    thickness_text: els.thicknessText.value,
    weight_text: els.weightText.value,
    extra_text: els.extraText.value,
  };
}

function setFields(fields = {}) {
  els.productName.value = fields.product_name || "";
  els.materialText.value = fields.material_text ?? "S925";
  els.sizeText.value = fields.size_text || "";
  els.pendantText.value = fields.pendant_text || "";
  els.thicknessText.value = fields.thickness_text || "";
  els.weightText.value = fields.weight_text || "";
  els.extraText.value = fields.extra_text || "";

  const itemText = fields.item_text || "NECKLACE";
  const optionValues = [...els.itemSelect.options].map((option) => option.value);
  if (optionValues.includes(itemText)) {
    els.itemSelect.value = itemText;
    els.customItem.value = "";
  } else {
    els.itemSelect.value = "직접입력";
    els.customItem.value = itemText;
  }
  toggleCustomItem();
}

function canvasLimits(type) {
  if (type === "main") return { maxWidth: 1720, maxHeight: 1960 };
  if (type === "model") return { maxWidth: 1720, maxHeight: 2112 };
  return { maxWidth: 1720, maxHeight: 2200 };
}

function findImage(id) {
  if (state.main?.id === id) return state.main;
  return [...state.models, ...state.products].find((item) => item.id === id) || null;
}

function removeImage(type, id) {
  const editor = editors.get(id);
  if (editor?.cropper) editor.cropper.destroy();
  editors.delete(id);

  if (type === "main") {
    state.main = null;
  } else if (type === "model") {
    state.models = state.models.filter((item) => item.id !== id);
  } else {
    state.products = state.products.filter((item) => item.id !== id);
  }
  renderAllEditors();
}

function applyEditor(id) {
  const editor = editors.get(id);
  const item = findImage(id);
  if (!editor?.cropper || !item) return false;

  const canvas = editor.cropper.getCroppedCanvas({
    fillColor: "#f5f5f5",
    imageSmoothingEnabled: true,
    imageSmoothingQuality: "high",
    ...canvasLimits(editor.type),
  });
  if (!canvas) return false;
  item.croppedData = canvas.toDataURL("image/png");
  return true;
}

function applyAllEditors() {
  for (const id of editors.keys()) {
    applyEditor(id);
  }
}

function rotateEditor(id, degrees) {
  const editor = editors.get(id);
  if (!editor?.cropper) return;
  editor.cropper.rotate(degrees);
}

function resetEditor(id) {
  const editor = editors.get(id);
  const item = findImage(id);
  if (!editor?.cropper || !item) return;
  editor.cropper.reset();
  item.croppedData = item.originalData;
}

function editorEmptyText(type) {
  if (type === "main") return "Main 사진 1장을 선택하세요.";
  if (type === "model") return "모델컷 사진을 여러 장 선택하세요.";
  return "제품컷 사진을 여러 장 선택하세요.";
}

function renderImageList(container, items, type, aspectRatio) {
  container.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = editorEmptyText(type);
    container.appendChild(empty);
    return;
  }

  for (const item of items) {
    const card = document.createElement("article");
    card.className = "image-editor";

    const toolbar = document.createElement("div");
    toolbar.className = "editor-toolbar";

    const title = document.createElement("div");
    title.className = "editor-title";
    title.textContent = item.name;

    const actions = document.createElement("div");
    actions.className = "editor-actions";
    actions.appendChild(
      makeButton("크롭 적용", () => {
        if (applyEditor(item.id)) showStatus(`${item.name} 크롭을 적용했습니다.`);
      })
    );
    actions.appendChild(
      makeButton("초기화", () => {
        resetEditor(item.id);
        showStatus(`${item.name} 편집을 초기화했습니다.`);
      })
    );
    if (type === "product") {
      actions.appendChild(makeButton("↺ 1°", () => rotateEditor(item.id, -1)));
      actions.appendChild(makeButton("↻ 1°", () => rotateEditor(item.id, 1)));
      actions.appendChild(makeButton("↺ 90°", () => rotateEditor(item.id, -90)));
      actions.appendChild(makeButton("↻ 90°", () => rotateEditor(item.id, 90)));
    }
    actions.appendChild(makeButton("삭제", () => removeImage(type, item.id), "danger"));

    toolbar.appendChild(title);
    toolbar.appendChild(actions);

    const cropArea = document.createElement("div");
    cropArea.className = "crop-area";
    const image = document.createElement("img");
    image.alt = item.name;
    image.src = item.originalData;
    cropArea.appendChild(image);

    card.appendChild(toolbar);
    card.appendChild(cropArea);
    container.appendChild(card);

    if (!window.Cropper) {
      showStatus("Cropper.js를 불러오지 못했습니다. 인터넷 연결 또는 CDN 접근을 확인해 주세요.", "error");
      continue;
    }

    const editor = { cropper: null, type, item };
    const cropper = new Cropper(image, {
      aspectRatio,
      autoCropArea: 0.9,
      background: false,
      checkOrientation: false,
      dragMode: "move",
      responsive: true,
      rotatable: type === "product",
      viewMode: 1,
      zoomOnWheel: false,
    });
    editor.cropper = cropper;
    editors.set(item.id, editor);
  }
}

function renderAllEditors() {
  for (const editor of editors.values()) {
    if (editor.cropper) editor.cropper.destroy();
  }
  editors.clear();

  renderImageList(els.mainEditor, state.main ? [state.main] : [], "main", 43 / 49);
  renderImageList(els.modelEditors, state.models, "model", 211 / 259);
  renderImageList(els.productEditors, state.products, "product", NaN);
}

function normalizeDownloadFilename(filename, fallback = "detail_page_config.json", extension = ".json") {
  const rawName = (filename || fallback).trim().split(/[\\/]/).pop() || fallback;
  let cleaned = rawName === "." || rawName === ".." ? fallback : rawName;
  if (!cleaned.toLowerCase().endsWith(extension)) cleaned += extension;
  return cleaned;
}

function downloadTextFile(filename, text, mime) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function buildConfig() {
  applyAllEditors();
  return {
    version: appConfig.configVersion || 1,
    fields: getFields(),
    main_img: state.main?.croppedData || null,
    model_imgs: state.models.map((item) => item.croppedData),
    product_imgs: state.products.map((item) => item.croppedData),
  };
}

async function handleImageFiles(files, type) {
  const records = [];
  for (const file of files) {
    records.push(imageRecord(file.name, await readFileAsDataUrl(file)));
  }

  if (type === "main") {
    state.main = records[0] || null;
  } else if (type === "model") {
    state.models = records;
  } else {
    state.products = records;
  }
  renderAllEditors();
}

async function handleConfigFile(file) {
  const text = await file.text();
  const config = JSON.parse(text);
  setFields(config.fields || {});

  state.main = config.main_img ? imageRecord("config-main.png", config.main_img) : null;
  state.models = (config.model_imgs || []).map((dataUrl, index) =>
    imageRecord(`config-model-${index + 1}.png`, dataUrl)
  );
  state.products = (config.product_imgs || []).map((dataUrl, index) =>
    imageRecord(`config-product-${index + 1}.png`, dataUrl)
  );

  els.configSaveName.value = file.name || "detail_page_config.json";
  renderAllEditors();
  showStatus("Config를 불러왔습니다.");
}

async function generateDetailPage() {
  if (!state.main) {
    showStatus("Main 사진 1장은 반드시 필요합니다.", "error");
    return;
  }

  applyAllEditors();
  setBusy(true);
  showStatus("상세페이지를 생성하고 있습니다.");

  try {
    const payload = {
      fields: getFields(),
      main_img: state.main.croppedData,
      model_imgs: state.models.map((item) => item.croppedData),
      product_imgs: state.products.map((item) => item.croppedData),
    };

    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "상세페이지 생성에 실패했습니다.");

    els.resultImage.src = data.imageData;
    els.resultImage.classList.remove("hidden");
    els.downloadResult.href = data.imageData;
    els.downloadResult.download = data.fileName || "detail_page.jpg";
    els.downloadResult.classList.remove("hidden");
    els.resultMeta.textContent = `${data.width}px × ${data.height}px`;
    showStatus("상세페이지 생성 완료");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    setBusy(false);
  }
}

function bindEvents() {
  els.itemSelect.addEventListener("change", toggleCustomItem);
  els.mainFile.addEventListener("change", async (event) => {
    await handleImageFiles([...event.target.files], "main");
    event.target.value = "";
  });
  els.modelFiles.addEventListener("change", async (event) => {
    await handleImageFiles([...event.target.files], "model");
    event.target.value = "";
  });
  els.productFiles.addEventListener("change", async (event) => {
    await handleImageFiles([...event.target.files], "product");
    event.target.value = "";
  });
  els.configFile.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      await handleConfigFile(file);
    } catch (error) {
      showStatus(`Config를 불러오지 못했습니다: ${error.message}`, "error");
    } finally {
      event.target.value = "";
    }
  });
  els.saveConfigButton.addEventListener("click", () => {
    const config = buildConfig();
    const filename = normalizeDownloadFilename(els.configSaveName.value);
    downloadTextFile(filename, JSON.stringify(config, null, 2), "application/json;charset=utf-8");
    showStatus("현재 config를 저장했습니다.");
  });
  els.generateButton.addEventListener("click", generateDetailPage);
}

function collectElements() {
  for (const id of [
    "status",
    "generateButton",
    "configFile",
    "configSaveName",
    "saveConfigButton",
    "productName",
    "itemSelect",
    "customItemWrap",
    "customItem",
    "materialText",
    "sizeText",
    "pendantText",
    "thicknessText",
    "weightText",
    "extraText",
    "mainFile",
    "modelFiles",
    "productFiles",
    "mainEditor",
    "modelEditors",
    "productEditors",
    "downloadResult",
    "resultImage",
    "resultMeta",
  ]) {
    els[id] = $(id);
  }
}

function showStartupWarnings() {
  const warnings = [];
  if (!appConfig.fontReady) warnings.push(appConfig.fontNotice);
  if (!appConfig.postBoxExists) warnings.push("고정 박스 사진 파일이 없습니다: assets/postfix_box_lot.JPG");
  if (!window.Cropper) warnings.push("Cropper.js를 불러오지 못했습니다. 인터넷 연결 또는 CDN 접근을 확인해 주세요.");
  if (warnings.length) showStatus(warnings.join(" "), "warning");
}

function init() {
  collectElements();
  initItemOptions();
  bindEvents();
  renderAllEditors();
  showStartupWarnings();
}

init();
