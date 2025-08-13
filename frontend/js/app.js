// ===============================
// app.js - STB & Dismantle Reporting
// ===============================

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

// -------------------------------------------
// 📸 Fitur Capture Table & Download (PNG)
// -------------------------------------------
function captureTableAndDownload(tableId, fileName) {
  const tableElement = document.getElementById(tableId);
  if (!tableElement) {
    console.error("Tabel tidak ditemukan:", tableId);
    alert("Tabel tidak ditemukan!");
    return;
  }

  html2canvas(tableElement)
    .then((canvas) => {
      const link = document.createElement("a");
      link.download = fileName || `${tableId}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    })
    .catch((error) => {
      console.error("Gagal capture tabel:", error);
    });
}

function captureTable(tableId) {
  captureTableAndDownload(tableId, `${tableId}.png`);
}

// -------------------------------------------
// Floating Navbar: tampil saat scroll >= 5%
// dari tinggi tabel pertama
// -------------------------------------------
(function () {
  // Kandidat ID tabel pertama (agar tahan terhadap perubahan penamaan)
  const FIRST_TABLE_ID_CANDIDATES = [
    "dismantle_progress",          // umumnya dipakai di subtable_dismantle_progress.html
    "table-dismantle-progress"     // fallback jika memakai kebab-case
  ];

  function getFirstTable() {
    for (const id of FIRST_TABLE_ID_CANDIDATES) {
      const el = document.getElementById(id);
      if (el) return el;
    }
    return null;
  }

  function updateFloatingNavbarVisibility() {
    const navbar = document.getElementById("floating-navbar");
    if (!navbar) return;

    const firstTable = getFirstTable();
    if (!firstTable) {
      // Jika tabel belum dirender, sembunyikan navbar
      navbar.classList.add("hidden");
      return;
    }

    const tableTop = firstTable.offsetTop;
    const tableHeight = firstTable.offsetHeight || 1;
    const triggerPoint = tableTop + tableHeight * 0.01; 

    if (window.scrollY >= triggerPoint) {
      navbar.classList.remove("hidden");
    } else {
      navbar.classList.add("hidden");
    }
  }

  // Dengarkan scroll & resize, dan sync saat DOM siap
  window.addEventListener("scroll", updateFloatingNavbarVisibility, { passive: true });
  window.addEventListener("resize", updateFloatingNavbarVisibility);
  document.addEventListener("DOMContentLoaded", updateFloatingNavbarVisibility);
})();

// -------------------------------------------
// Smooth Scroll ke Tabel (by ID)
// -------------------------------------------
function scrollToTable(tableId) {
  const targetTable = document.getElementById(tableId);
  if (!targetTable) {
    console.warn("Elemen tabel tidak ditemukan:", tableId);
    return;
  }
  targetTable.scrollIntoView({ behavior: "smooth", block: "start" });
}
