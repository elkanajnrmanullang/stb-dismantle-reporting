const ctx = document.getElementById('weeklyChart').getContext('2d');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'],
    datasets: [
      {
        label: 'Replacement',
        backgroundColor: '#DC2626',
        data: [20, 35, 40, 30, 60, 50, 70]
      },
      {
        label: 'Dismantle',
        backgroundColor: '#4B5563',
        data: [15, 30, 25, 20, 45, 40, 50]
      }
    ]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero: true }
    }
  }
});
