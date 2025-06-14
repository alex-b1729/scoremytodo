// Initialize the heatmap
const cal = new CalHeatmap();

// Function to load and display data
async function loadHeatmapData() {
    // Fetch heatmap data
    const response = await fetch('/dashboard/score-data/');
    const json_response = await response.json();
    const data = json_response.data

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
                padding: [5, 5, 5, 5],
                label: { position: 'top' },
            },
            subDomain: { type: 'xDay', radius: 4, width: 30, height: 30, label: 'D' },
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
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadHeatmapData);