var ctx = document.getElementById('userActivityChart').getContext('2d');
var chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Active Users',
            data: [1200, 1900, 3000, 5000, 4000, 4500],
            backgroundColor: 'rgba(194, 65, 12, 0.2)',
            borderColor: 'rgba(194, 65, 12, 1)',
            borderWidth: 2,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});