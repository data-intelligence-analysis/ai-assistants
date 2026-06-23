document.addEventListener('DOMContentLoaded', function () {
  const ctx = document.getElementById('trendChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: trendLabels,
      datasets: [{
        label: 'Total Leads',
        data: trendValues,
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13,110,253,0.05)',
        tension: 0.3,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: {legend:{display:false}},
      scales: {
        x: {grid:{display:false}},
        y: {grid:{color:'#f1f3f6'}}
      }
    }
  });
});
