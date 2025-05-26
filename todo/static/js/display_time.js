let userSelectedTimezone;
let updateInterval;

function getSelectedTimezone() {
    const region = document.getElementById("id_region-region").value;
    const location = document.getElementById("id_location-location").value;
    let selectedStrTz;
    if (location != "") {
        selectedStrTz = region.concat("/", location);
    } else {
        selectedStrTz = region;
    }
    return selectedStrTz
}

function getCurrentTime(timezone) {
    try {
        const now = new Date();
        const options = {
            timeZone: timezone,
            hour12: true,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        };

        const dateOptions = {
            timeZone: timezone,
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };

        const timeString = now.toLocaleTimeString('en-US', options);
        const dateString = now.toLocaleDateString('en-US', dateOptions);

        return { time: timeString, date: dateString, error: null };
    } catch (error) {
        return { time: null, date: null, error: error.message };
    }
}

function updateTimeDisplay(selectedTz) {
    const result = getCurrentTime(userSelectedTimezone);
    const timeDisplay = document.getElementById('timeDisplay');
    const dateDisplay = document.getElementById('dateDisplay');
    const errorMessage = document.getElementById('errorMessage');

    if (result.error) {
        timeDisplay.textContent = '--:--:--';
        dateDisplay.textContent = '';
        errorMessage.textContent = `Error: Invalid timezone "${selectedTz}"`;
    } else {
        timeDisplay.textContent = result.time;
        dateDisplay.textContent = result.date;
        errorMessage.textContent = '';
    }
}

function updateTimezone() {
    const newTimezone = getSelectedTimezone();

    if (!newTimezone) {
        document.getElementById('errorMessage').textContent = 'Please select a timezone';
        return;
    }

    // Test if the timezone is valid
    const testResult = getCurrentTime(newTimezone);
    if (testResult.error) {
        document.getElementById('errorMessage').textContent = `Invalid timezone: ${newTimezone}`;
        return;
    }

    userSelectedTimezone = newTimezone;
    document.getElementById('currentTimezone').textContent = `Local time in ${userSelectedTimezone}`;
    document.getElementById('errorMessage').textContent = '';

    // Clear existing interval and start new one
    if (updateInterval) {
        clearInterval(updateInterval);
    }

    updateTimeDisplay();
    updateInterval = setInterval(updateTimeDisplay, 1000);
}

// When region form changes it fires an HTMX request which causes below to fire
document.addEventListener('htmx:afterRequest', function(e) {
    updateTimezone();
});
// when location form changes it causes below to fire
document.getElementById('location-form-div').addEventListener('change', function(e) {
    updateTimezone();
});

updateTimezone();