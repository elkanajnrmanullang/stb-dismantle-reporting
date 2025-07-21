document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("weeklyChart").getContext("2d");

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: ["25", "26", "27", "28", "29", "30", "1", "2", "3"],
      datasets: [
        {
          label: "Total Aktivitas",
          data: [12, 19, 3, 5, 2, 3, 7, 9, 4],
          borderColor: "rgb(239, 68, 68)",
          fill: false,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: {
          display: true,
          text: "Aktivitas Mingguan",
        },
      },
    },
  });
});
