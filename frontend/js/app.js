// Fungsi Ambil Data Kartu Ringkasan
// document.addEventListener("DOMContentLoaded", () => {
//   fetch("/api/card-summary")
//     .then(res => res.json())
//     .then(data => {
//       if (data.success) {
//         document.getElementById("replace-count").innerText = data.total_replace;
//         document.getElementById("dismantle-count").innerText = data.total_dismantle;
//       } else {
//         document.getElementById("replace-count").innerText = "⚠️";
//         document.getElementById("dismantle-count").innerText = "⚠️";
//       }
//     })
//     .catch(err => {
//       console.error("Error:", err);
//       document.getElementById("replace-count").innerText = "❌";
//       document.getElementById("dismantle-count").innerText = "❌";
//     });
// });

// Fungsi Update Nama File Upload
function updateFilename(inputId) {
  const input = document.getElementById(inputId);
  const file = input.files[0];
  const previewBox = document.getElementById(`preview-${inputId}`);
  const filenameSpan = document.getElementById(`filename-${inputId}`);

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
  const newInput = input.cloneNode(true);
  newInput.value = "";
  newInput.addEventListener("change", () => updateFilename(inputId));
  input.parentNode.replaceChild(newInput, input);

  document.getElementById(`preview-${inputId}`).classList.add("hidden");
  document.getElementById(`filename-${inputId}`).textContent = "";
}

// Capture Table
function captureTable(tableId) {
  const tableElement = document.getElementById(tableId);
  if (!tableElement) {
    console.error("Tabel tidak ditemukan:", tableId);
    return;
  }

  html2canvas(tableElement)
    .then((canvas) => {
      const link = document.createElement("a");
      link.download = `${tableId}.png`;
      link.href = canvas.toDataURL();
      link.click();
    })
    .catch((error) => {
      console.error("Gagal capture tabel:", error);
    });
}

function clearFile(inputId) {
  const input = document.getElementById(inputId);
  const newInput = input.cloneNode(true);
  input.parentNode.replaceChild(newInput, input);
  newInput.addEventListener("change", () => updateFilename(inputId));
  document.getElementById(`filename-${inputId}`).innerHTML = "";
}

// 📸 Fitur Capture Table & Download
function captureTableAndDownload(tableId, fileName) {
  const tableElement = document.getElementById(tableId);
  if (!tableElement) return alert("Tabel tidak ditemukan!");

  html2canvas(tableElement).then((canvas) => {
    const link = document.createElement("a");
    link.download = fileName;
    link.href = canvas.toDataURL("image/png");
    link.click();
  });
}

function captureTable(tableId) {
  const tableElement = document.getElementById(tableId);
  if (!tableElement) {
    console.error("Tabel tidak ditemukan:", tableId);
    return;
  }

  html2canvas(tableElement)
    .then((canvas) => {
      const link = document.createElement("a");
      link.download = `${tableId}.png`;
      link.href = canvas.toDataURL();
      link.click();
    })
    .catch((error) => {
      console.error("Gagal capture tabel:", error);
    });
}
