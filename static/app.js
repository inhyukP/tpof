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

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

class LocalCropper {
  constructor(image, options = {}) {
    this.image = image;
    this.options = options;
    this.aspectRatio = Number.isFinite(options.aspectRatio) ? options.aspectRatio : null;
    this.autoCropArea = options.autoCropArea || 0.9;
    this.rotation = 0;
    this.ready = false;
    this.crop = { x: 0, y: 0, width: 0, height: 0 };
    this.drag = null;

    this.host = document.createElement("div");
    this.host.className = "local-cropper";
    this.canvas = document.createElement("canvas");
    this.canvas.className = "local-cropper-canvas";
    this.cropBox = document.createElement("div");
    this.cropBox.className = "crop-box";
    for (const direction of ["n", "e", "s", "w", "ne", "nw", "se", "sw"]) {
      const handle = document.createElement("span");
      handle.className = `crop-handle crop-handle-${direction}`;
      handle.dataset.direction = direction;
      this.cropBox.appendChild(handle);
    }

    this.host.append(this.canvas, this.cropBox);
    this.image.replaceWith(this.host);

    this.onPointerDown = this.onPointerDown.bind(this);
    this.onPointerMove = this.onPointerMove.bind(this);
    this.onPointerUp = this.onPointerUp.bind(this);
    this.onResize = this.onResize.bind(this);
    this.onLoad = () => this.rebuild(true);

    this.cropBox.addEventListener("pointerdown", this.onPointerDown);
    window.addEventListener("resize", this.onResize);

    if (this.image.complete && this.image.naturalWidth) {
      this.rebuild(true);
    } else {
      this.image.addEventListener("load", this.onLoad, { once: true });
    }
  }

  destroy() {
    this.cropBox.removeEventListener("pointerdown", this.onPointerDown);
    window.removeEventListener("pointermove", this.onPointerMove);
    window.removeEventListener("pointerup", this.onPointerUp);
    window.removeEventListener("resize", this.onResize);
    this.image.removeEventListener("load", this.onLoad);
    if (this.host.parentNode) this.host.replaceWith(this.image);
  }

  reset() {
    this.rotation = 0;
    this.rebuild(true);
  }

  rotate(degrees) {
    this.rotation = (this.rotation + degrees) % 360;
    this.rebuild(true);
  }

  getCroppedCanvas(options = {}) {
    if (!this.ready || !this.sourceCanvas) return null;
    const sourceScale = this.sourceCanvas.width / this.displayWidth;
    const sx = clamp(Math.round(this.crop.x * sourceScale), 0, this.sourceCanvas.width - 1);
    const sy = clamp(Math.round(this.crop.y * sourceScale), 0, this.sourceCanvas.height - 1);
    const sw = clamp(Math.round(this.crop.width * sourceScale), 1, this.sourceCanvas.width - sx);
    const sh = clamp(Math.round(this.crop.height * sourceScale), 1, this.sourceCanvas.height - sy);
    const limitScale = Math.min(
      options.maxWidth ? options.maxWidth / sw : 1,
      options.maxHeight ? options.maxHeight / sh : 1,
      1
    );
    const output = document.createElement("canvas");
    output.width = Math.max(1, Math.round(sw * limitScale));
    output.height = Math.max(1, Math.round(sh * limitScale));
    const ctx = output.getContext("2d");
    ctx.fillStyle = options.fillColor || "#ffffff";
    ctx.fillRect(0, 0, output.width, output.height);
    ctx.imageSmoothingEnabled = options.imageSmoothingEnabled !== false;
    ctx.imageSmoothingQuality = options.imageSmoothingQuality || "high";
    ctx.drawImage(this.sourceCanvas, sx, sy, sw, sh, 0, 0, output.width, output.height);
    return output;
  }

  rebuild(resetCrop = false) {
    if (!this.image.naturalWidth || !this.image.naturalHeight) return;
    this.buildSourceCanvas();
    this.drawDisplayCanvas();
    if (resetCrop || !this.crop.width || !this.crop.height) this.setInitialCrop();
    this.crop = this.fitCrop(this.crop);
    this.renderCropBox();
    this.ready = true;
  }

  buildSourceCanvas() {
    const angle = ((this.rotation % 360) + 360) % 360;
    const radians = (angle * Math.PI) / 180;
    const width = this.image.naturalWidth;
    const height = this.image.naturalHeight;
    const rotatedWidth = Math.ceil(Math.abs(width * Math.cos(radians)) + Math.abs(height * Math.sin(radians)));
    const rotatedHeight = Math.ceil(Math.abs(width * Math.sin(radians)) + Math.abs(height * Math.cos(radians)));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, rotatedWidth);
    canvas.height = Math.max(1, rotatedHeight);
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.rotate(radians);
    ctx.drawImage(this.image, -width / 2, -height / 2);
    this.sourceCanvas = canvas;
  }

  drawDisplayCanvas() {
    const parentWidth = this.host.parentElement?.clientWidth || this.sourceCanvas.width;
    const maxWidth = Math.max(240, Math.min(parentWidth - 24, 960));
    const maxHeight = 620;
    const scale = Math.min(maxWidth / this.sourceCanvas.width, maxHeight / this.sourceCanvas.height, 1);
    this.displayWidth = Math.max(1, Math.round(this.sourceCanvas.width * scale));
    this.displayHeight = Math.max(1, Math.round(this.sourceCanvas.height * scale));
    this.canvas.width = this.displayWidth;
    this.canvas.height = this.displayHeight;
    this.host.style.width = `${this.displayWidth}px`;
    this.host.style.height = `${this.displayHeight}px`;
    const ctx = this.canvas.getContext("2d");
    ctx.clearRect(0, 0, this.displayWidth, this.displayHeight);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(this.sourceCanvas, 0, 0, this.displayWidth, this.displayHeight);
  }

  setInitialCrop() {
    const area = clamp(this.autoCropArea, 0.1, 1);
    let width = this.displayWidth * area;
    let height = this.displayHeight * area;
    if (this.aspectRatio) {
      height = width / this.aspectRatio;
      if (height > this.displayHeight * area) {
        height = this.displayHeight * area;
        width = height * this.aspectRatio;
      }
    }
    this.crop = {
      x: (this.displayWidth - width) / 2,
      y: (this.displayHeight - height) / 2,
      width,
      height,
    };
  }

  fitCrop(crop) {
    const minSize = 36;
    let { x, y, width, height } = crop;
    if (this.aspectRatio) {
      if (width > this.displayWidth) {
        width = this.displayWidth;
        height = width / this.aspectRatio;
      }
      if (height > this.displayHeight) {
        height = this.displayHeight;
        width = height * this.aspectRatio;
      }
      width = clamp(width, Math.min(minSize, this.displayWidth), this.displayWidth);
      height = width / this.aspectRatio;
      if (height > this.displayHeight) {
        height = this.displayHeight;
        width = height * this.aspectRatio;
      }
    } else {
      width = clamp(width, Math.min(minSize, this.displayWidth), this.displayWidth);
      height = clamp(height, Math.min(minSize, this.displayHeight), this.displayHeight);
    }
    x = clamp(x, 0, Math.max(0, this.displayWidth - width));
    y = clamp(y, 0, Math.max(0, this.displayHeight - height));
    return { x, y, width, height };
  }

  renderCropBox() {
    Object.assign(this.cropBox.style, {
      left: `${this.crop.x}px`,
      top: `${this.crop.y}px`,
      width: `${this.crop.width}px`,
      height: `${this.crop.height}px`,
    });
  }

  onResize() {
    if (!this.ready) return;
    const oldWidth = this.displayWidth;
    const oldHeight = this.displayHeight;
    const oldCrop = { ...this.crop };
    this.drawDisplayCanvas();
    this.crop = this.fitCrop({
      x: oldCrop.x * (this.displayWidth / oldWidth),
      y: oldCrop.y * (this.displayHeight / oldHeight),
      width: oldCrop.width * (this.displayWidth / oldWidth),
      height: oldCrop.height * (this.displayHeight / oldHeight),
    });
    this.renderCropBox();
  }

  onPointerDown(event) {
    event.preventDefault();
    const direction = event.target.dataset.direction || "";
    this.drag = {
      direction,
      mode: direction ? "resize" : "move",
      startX: event.clientX,
      startY: event.clientY,
      crop: { ...this.crop },
    };
    window.addEventListener("pointermove", this.onPointerMove);
    window.addEventListener("pointerup", this.onPointerUp);
  }

  onPointerMove(event) {
    if (!this.drag) return;
    event.preventDefault();
    const dx = event.clientX - this.drag.startX;
    const dy = event.clientY - this.drag.startY;
    if (this.drag.mode === "move") {
      this.crop = this.fitCrop({
        ...this.drag.crop,
        x: this.drag.crop.x + dx,
        y: this.drag.crop.y + dy,
      });
    } else {
      this.crop = this.resizeCrop(this.drag.crop, dx, dy, this.drag.direction);
    }
    this.renderCropBox();
  }

  onPointerUp() {
    this.drag = null;
    window.removeEventListener("pointermove", this.onPointerMove);
    window.removeEventListener("pointerup", this.onPointerUp);
  }

  resizeCrop(start, dx, dy, direction) {
    if (this.aspectRatio) {
      return this.resizeFixedAspect(start, dx, dy, direction);
    }
    let left = start.x;
    let top = start.y;
    let right = start.x + start.width;
    let bottom = start.y + start.height;
    const minSize = 36;
    if (direction.includes("w")) left = clamp(left + dx, 0, right - minSize);
    if (direction.includes("e")) right = clamp(right + dx, left + minSize, this.displayWidth);
    if (direction.includes("n")) top = clamp(top + dy, 0, bottom - minSize);
    if (direction.includes("s")) bottom = clamp(bottom + dy, top + minSize, this.displayHeight);
    return this.fitCrop({ x: left, y: top, width: right - left, height: bottom - top });
  }

  resizeFixedAspect(start, dx, dy, direction) {
    const minSize = 36;
    const fromWest = direction.includes("w");
    const fromNorth = direction.includes("n");
    const horizontal = direction.includes("e") || fromWest;
    let width = horizontal ? start.width + (fromWest ? -dx : dx) : (start.height + (fromNorth ? -dy : dy)) * this.aspectRatio;
    width = Math.max(minSize, width);
    let height = width / this.aspectRatio;
    if (height < minSize) {
      height = minSize;
      width = height * this.aspectRatio;
    }

    let x = fromWest ? start.x + start.width - width : start.x;
    let y = fromNorth ? start.y + start.height - height : start.y;
    if (!direction.includes("n") && !direction.includes("s")) {
      y = start.y + (start.height - height) / 2;
    }
    if (!horizontal) {
      x = start.x + (start.width - width) / 2;
    }
    return this.fitCrop({ x, y, width, height });
  }
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

    const editor = { cropper: null, type, item };
    const cropper = new LocalCropper(image, {
      aspectRatio,
      autoCropArea: 0.9,
      rotatable: type === "product",
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
