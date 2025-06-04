// Initialize the heatmap
const cal = new CalHeatmap();

// Function to load and display data
async function loadHeatmapData() {
//    try {
    // Fetch heatmap data
    const response = await fetch('/dashboard/score-data/');
    const json_response = await response.json();
//    console.log(json_response);
    const data = json_response.data
//    console.log(data)

    // Fetch stats data
//        const statsResponse = await fetch('/heatmap-stats/');
//        const stats = await statsResponse.json();

    // Update stats display
//        document.getElementById('total-days').textContent = stats.total_days;
//        document.getElementById('avg-score').textContent = (stats.avg_score * 100).toFixed(1) + '%';
//        document.getElementById('max-score').textContent = (stats.max_score * 100).toFixed(1) + '%';

    cal.on('click', (event, timestamp, value) =>{
        const dt = new Date(timestamp);
        const dt_formatted = (
            dt.getUTCFullYear() + '-' +
            (dt.getUTCMonth() + 1).toString().padStart(2, '0') + '-' +
            dt.getUTCDate().toString().padStart(2, '0')
        );
        if (value !== null) {
            location.href = `/todo/${dt_formatted}`;
        }
    });

    cal.on('mouseover', (event, timestamp, value) => {
        if (value !== null) {
            event.target.style.cursor = 'pointer';
        }
    });

    // Clear loading message
    document.getElementById('cal-heatmap').innerHTML = '';

    const today = new Date();
    const firstOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);

    cal.paint(
        {
            data: {
                source: data,
                type: 'json',
                x: 'date',
                y: 'score',
                defaultValue: null,
            },
            verticalOrientation: false,
            range: 2,
            date: { start: firstOfLastMonth },
            scale: {
                color: {
                    scheme: 'RdYlGn',
                    domain: [0, 100],
                    type: 'linear',
                },
            },
            domain: {
                type: 'month',
                padding: [10, 10, 10, 10],
                label: { position: 'top' },
            },
            subDomain: { type: 'xDay', radius: 2, width: 15, height: 15, label: 'D' },
        },
        [
            [
                Tooltip,
                {
                    text: function (date, value, dayjsDate) {
                        if (value !== null) {
                            return (value + '%' + ' on ' + dayjsDate.format('LL'));
                        }
                    },
                },
            ],
        ],
    );

    // Initialize Cal-Heatmap
//    cal.paint({
//        // Basic configuration
//        domain: "month",
//        subDomain: "day",
//        range: 12, // Show 12 months
//        cellSize: 12,
//        cellPadding: 2,
//
//        // Data
//        data: data,
//
//        // Styling
//        legend: false, // We'll use our custom legend
//        legendColors: {
//            min: "#ebedf0",
//            max: "#216e39",
//            empty: "#ebedf0"
//        },
//
//        // Scale: 0-25-50-75-100
//        scale: {
//            0: "#ebedf0",
//            25: "#9be9a8",
//            50: "#40c463",
//            75: "#30a14e",
//            100: "#216e39"
//        },
//
//        // Date formatting
//        start: new Date(new Date().getFullYear() - 1, new Date().getMonth()),
//
//        // Tooltip
//        tooltip: true,
//        onClick: function(date, nb) {
//            if (nb !== null) {
//                const percentage = (nb / 100).toFixed(2);
//                alert(`Date: ${date.toDateString()}\nScore: ${percentage}% (${nb}/100)`);
//            }
//        },
//
//        // Labels
//        label: {
//            position: "top",
//            width: 30
//        },
//
//        // Navigation
//        browsePastTime: true,
//        browseFutureTime: false
//    });

//    } catch (error) {
//        console.error('Error loading heatmap data:', error);
//        document.getElementById('cal-heatmap').innerHTML =
//            '<div class="loading">Error loading heatmap data. Please try again.</div>';
//    }
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadHeatmapData);