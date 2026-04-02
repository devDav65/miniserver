// ── Références DOM ───────────────────────────────────────────
const dropZone      = document.getElementById("drop-zone");
const fileInput     = document.getElementById("file-input");
const progressWrap  = document.getElementById("progress-wrapper");
const progressBar   = document.getElementById("progress-bar");
const progressLabel = document.getElementById("progress-label");
const flashContainer= document.getElementById("flash-container");
const fileList      = document.getElementById("file-list");
const fileCards     = document.getElementById("file-cards");

// ── Drag & Drop ──────────────────────────────────────────────
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

["dragleave", "dragend"].forEach((evt) => {
  dropZone.addEventListener(evt, () => dropZone.classList.remove("dragover"));
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  uploadFiles(e.dataTransfer.files);
});

dropZone.addEventListener("click", (e) => {
  if (e.target.classList.contains("btn-upload")) return;
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) uploadFiles(fileInput.files);
});

// ── Upload ────────────────────────────────────────────────────
function uploadFiles(files) {
  if (!files || files.length === 0) return;

  const formData = new FormData();
  for (const file of files) formData.append("file", file);

  const xhr = new XMLHttpRequest();

  xhr.upload.addEventListener("progress", (e) => {
    if (!e.lengthComputable) return;
    setProgress(Math.round((e.loaded / e.total) * 100));
  });

  xhr.addEventListener("load", () => {
    hideProgress();
    try {
      const data = JSON.parse(xhr.responseText);
      if (xhr.status === 200 || xhr.status === 207) {
        data.uploaded.forEach((f) => {
          showFlash(`${f.name} uploadé (${formatSize(f.size)})`, "success");
          addRowToTable(f.name, f.size, f.can_delete);
          addCard(f.name, f.size, f.can_delete);
        });
        if (data.errors) data.errors.forEach((err) => showFlash(err, "error"));
      } else {
        showFlash(data.error || "Erreur lors de l'upload", "error");
      }
    } catch {
      showFlash("Réponse inattendue du serveur", "error");
    }
    fileInput.value = "";
  });

  xhr.addEventListener("error", () => {
    hideProgress();
    showFlash("Erreur réseau — serveur inaccessible", "error");
  });

  xhr.open("POST", "/upload");
  showProgress();
  xhr.send(formData);
}

// ── Suppression ──────────────────────────────────────────────
function deleteFile(filename, btn) {
  if (!confirm(`Supprimer "${filename}" ?`)) return;

  btn.disabled = true;
  btn.textContent = "…";

  fetch(`/delete/${encodeURIComponent(filename)}`, { method: "DELETE" })
    .then((r) => r.json())
    .then((data) => {
      if (data.deleted) {
        // Supprime la ligne ET la carte
        document.querySelectorAll(`[data-name="${CSS.escape(filename)}"]`).forEach((el) => {
          el.style.opacity = "0";
          el.style.transition = "opacity .2s";
          setTimeout(() => { el.remove(); updateBadgeCount(-1); }, 200);
        });
        showFlash(`${filename} supprimé`, "success");
      } else {
        showFlash(data.error || "Erreur suppression", "error");
        btn.disabled = false;
        btn.textContent = "Supprimer";
      }
    })
    .catch(() => {
      showFlash("Erreur réseau", "error");
      btn.disabled = false;
      btn.textContent = "Supprimer";
    });
}

// ── Helpers UI ───────────────────────────────────────────────
function setProgress(pct) {
  progressWrap.hidden = false;
  progressBar.style.setProperty("--pct", pct + "%");
  progressLabel.textContent = pct + "%";
}

function showProgress() { setProgress(0); }
function hideProgress() {
  setTimeout(() => { progressWrap.hidden = true; setProgress(0); }, 600);
}

function showFlash(message, type = "success") {
  const div = document.createElement("div");
  div.className = `flash ${type}`;
  div.textContent = message;
  flashContainer.appendChild(div);
  setTimeout(() => {
    div.style.opacity = "0";
    div.style.transition = "opacity .3s";
    setTimeout(() => div.remove(), 300);
  }, 3500);
}

const FILE_ICON = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <polyline points="14 2 14 8 20 8"/>
</svg>`;

function addRowToTable(name, size, canDelete = true) {
  if (!fileList) return;
  const del = canDelete
    ? `<button class="btn-del" onclick="deleteFile('${escapeHtml(name)}', this)">Supprimer</button>`
    : `<span class="btn-del-locked">Verrouillé</span>`;
  const tr = document.createElement("tr");
  tr.dataset.name = name;
  tr.innerHTML = `
    <td class="file-name">${FILE_ICON}${escapeHtml(name)}</td>
    <td class="file-size">${formatSize(size)}</td>
    <td class="file-date">À l'instant</td>
    <td class="file-actions">
      <a class="btn-dl" href="/download/${encodeURIComponent(name)}">Télécharger</a>
      ${del}
    </td>`;
  fileList.prepend(tr);
  updateBadgeCount(+1);
}

function addCard(name, size, canDelete = true) {
  if (!fileCards) return;
  const del = canDelete
    ? `<button class="btn-del" onclick="deleteFile('${escapeHtml(name)}', this)">Supprimer</button>`
    : `<span class="btn-del-locked">Verrouillé</span>`;
  const card = document.createElement("div");
  card.className = "file-card";
  card.dataset.name = name;
  card.innerHTML = `
    <div class="file-card-name">${FILE_ICON}${escapeHtml(name)}</div>
    <div class="file-card-meta"><span>${formatSize(size)}</span><span>·</span><span>À l'instant</span></div>
    <div class="file-card-actions">
      <a class="btn-dl" href="/download/${encodeURIComponent(name)}">Télécharger</a>
      ${del}
    </div>`;
  fileCards.prepend(card);
}

function updateBadgeCount(delta) {
  const badge = document.querySelector(".badge");
  if (!badge) return;
  badge.textContent = Math.max(0, parseInt(badge.textContent || "0") + delta);
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 ** 2) return (bytes / 1024).toFixed(1) + " KB";
  if (bytes < 1024 ** 3) return (bytes / 1024 ** 2).toFixed(1) + " MB";
  return (bytes / 1024 ** 3).toFixed(2) + " GB";
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}