// ===============================
// app.js - STB & Dismantle Reporting
// ===============================

// -------------------------------------------------------
// 🔧 Konfigurasi Frontend → Backend (Vercel rewrites /api)
// -------------------------------------------------------

window.API_BASE = window.API_BASE || '/api';

// -------------------------------
// Fungsi Update Nama File Upload
// -------------------------------
function updateFilename(inputId) {
  const input = document.getElementById(inputId);
  const file = input?.files?.[0];
  const previewBox = document.getElementById(`preview-${inputId}`);
  const filenameSpan = document.getElementById(`filename-${inputId}`);

  if (!previewBox || !filenameSpan) return;

  if (file) {
    filenameSpan.textContent = file.name;
    previewBox.classList.remove("hidden");
  } else {
    filenameSpan.textContent = "";
    previewBox.classList.add("hidden");
  }
}

function removeFile(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const newInput = input.cloneNode(true);
  newInput.value = "";
  newInput.addEventListener("change", () => updateFilename(inputId));
  input.parentNode.replaceChild(newInput, input);

  const preview = document.getElementById(`preview-${inputId}`);
  const nameSpan = document.getElementById(`filename-${inputId}`);
  if (preview) preview.classList.add("hidden");
  if (nameSpan) nameSpan.textContent = "";
}

function clearFile(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const newInput = input.cloneNode(true);
  input.parentNode.replaceChild(newInput, input);
  newInput.addEventListener("change", () => updateFilename(inputId));

  const nameSpan = document.getElementById(`filename-${inputId}`);
  if (nameSpan) nameSpan.textContent = "";
}

// ------------------------------------------------------
// 📸 Fitur Capture Table & Download (PNG) — Peningkatan
// - Skala disesuaikan devicePixelRatio untuk hasil tajam
// - Latar belakang putih agar tidak transparan di PNG
// - useCORS true bila tabel memuat gambar eksternal
// ------------------------------------------------------
function captureTableAndDownload(tableId, fileName) {
  const tableElement = document.getElementById(tableId);
  if (!tableElement) {
    console.error("Tabel tidak ditemukan:", tableId);
    alert("Tabel tidak ditemukan!");
    return;
  }

  // Pastikan table fully visible sebelum capture (opsional, non-destruktif)
  const origOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';

  const scale = Math.min(window.devicePixelRatio || 1.5, 2.5); // batasi agar file tidak terlalu besar
  const opts = {
    backgroundColor: '#ffffff',
    useCORS: true,
    scale
  };

  html2canvas(tableElement, opts)
    .then((canvas) => {
      const link = document.createElement("a");
      link.download = fileName || `${tableId}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    })
    .catch((error) => {
      console.error("Gagal capture tabel:", error);
      alert("Gagal menyimpan gambar tabel. Coba ulangi.");
    })
    .finally(() => {
      document.body.style.overflow = origOverflow;
    });
}

function captureTable(tableId) {
  captureTableAndDownload(tableId, `${tableId}.png`);
}

// -----------------------------------------------------
// Floating Navbar: tampil saat scroll melewati ~5%
// tinggi tabel pertama (disesuaikan dari 1% → 5%)
// + debounce agar hemat performa
// ----------------------------------------------------
(function () {
  const FIRST_TABLE_ID_CANDIDATES = [
    "dismantle_progress",          
    "table-dismantle-progress"     
  ];

  function getFirstTable() {
    for (const id of FIRST_TABLE_ID_CANDIDATES) {
      const el = document.getElementById(id);
      if (el) return el;
    }
    return null;
  }

  function computeTrigger() {
    const firstTable = getFirstTable();
    if (!firstTable) return { navbar: null, triggerPoint: Infinity };

    const tableTop = firstTable.offsetTop || 0;
    const tableHeight = firstTable.offsetHeight || 1;
    // 5% dari tinggi tabel
    const triggerPoint = tableTop + tableHeight * 0.05;
    return { navbar: document.getElementById("floating-navbar"), triggerPoint };
  }
  function debounce(fn, wait = 100) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function _updateVisibility() {
    const { navbar, triggerPoint } = computeTrigger();
    if (!navbar) return;

    if (window.scrollY >= triggerPoint) {
      navbar.classList.remove("hidden");
    } else {
      navbar.classList.add("hidden");
    }
  }

  const updateFloatingNavbarVisibility = debounce(_updateVisibility, 80);

  window.addEventListener("scroll", updateFloatingNavbarVisibility, { passive: true });
  window.addEventListener("resize", updateFloatingNavbarVisibility);
  document.addEventListener("DOMContentLoaded", updateFloatingNavbarVisibility);

  window.addEventListener("load", updateFloatingNavbarVisibility);
})();

function scrollToTable(tableId) {
  const targetTable = document.getElementById(tableId);
  if (!targetTable) {
    console.warn("Elemen tabel tidak ditemukan:", tableId);
    return;
  }
  targetTable.scrollIntoView({ behavior: "smooth", block: "start" });
}


function safeText(v, fallback = "") {
  return (v === null || v === undefined) ? fallback : String(v);
}

function formatNumber(n) {
  try {
    const num = Number(n);
    if (Number.isNaN(num)) return safeText(n);
    return num.toLocaleString("id-ID");
  } catch {
    return safeText(n);
  }
}

(function bindScrollAnchors() {
  function handler(e) {
    const target = e.target.closest("[data-scroll-target]");
    if (!target) return;
    e.preventDefault();
    const id = target.getAttribute("data-scroll-target");
    scrollToTable(id);
  }
  document.addEventListener("click", handler);
})();

window.updateFilename = updateFilename;
window.removeFile = removeFile;
window.clearFile = clearFile;
window.captureTableAndDownload = captureTableAndDownload;
window.captureTable = captureTable;
window.scrollToTable = scrollToTable;
window.safeText = safeText;
window.formatNumber = formatNumber;
