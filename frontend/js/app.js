document.addEventListener("DOMContentLoaded", () => {
  fetch("/api/card-summary")
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        document.getElementById("replace-count").innerText = data.total_replace;
        document.getElementById("dismantle-count").innerText = data.total_dismantle;
      } else {
        document.getElementById("replace-count").innerText = "⚠️";
        document.getElementById("dismantle-count").innerText = "⚠️";
      }
    })
    .catch(err => {
      console.error("Error:", err);
      document.getElementById("replace-count").innerText = "❌";
      document.getElementById("dismantle-count").innerText = "❌";
    });
});
