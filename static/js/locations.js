const US_LOCATIONS = {
    "OH": ["Akron", "Cincinnati", "Cleveland", "Columbus", "Dayton", "Toledo", "Youngstown", "Canton", "Parma", "Lorain"],
    "CA": ["Los Angeles", "San Diego", "San Jose", "San Francisco", "Fresno", "Sacramento", "Long Beach", "Oakland", "Bakersfield", "Anaheim"],
    "TX": ["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth", "El Paso", "Arlington", "Corpus Christi", "Plano", "Lubbock"],
    "FL": ["Jacksonville", "Miami", "Tampa", "Orlando", "St. Petersburg", "Hialeah", "Port St. Lucie", "Tallahassee", "Cape Coral", "Fort Lauderdale"],
    "NY": ["New York City", "Buffalo", "Rochester", "Yonkers", "Syracuse", "Albany", "New Rochelle", "Mount Vernon", "Schenectady", "Utica"]
};

const STATE_NAMES = {
    "OH": "Ohio",
    "CA": "California",
    "TX": "Texas",
    "FL": "Florida",
    "NY": "New York"
};

function initLocationSelectors() {
    const stateSelectors = document.querySelectorAll('.state-selector');
    const citySelectors = document.querySelectorAll('.city-selector');

    stateSelectors.forEach((stateSel, index) => {
        const citySel = citySelectors[index];
        if (!citySel) return;

        // Populate States
        stateSel.innerHTML = '<option value="">Select State</option>';
        for (const [code, name] of Object.entries(STATE_NAMES)) {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = name;
            // Handle pre-selected value
            if (stateSel.dataset.selected === code) {
                option.selected = true;
            }
            stateSel.appendChild(option);
        }

        // Handle Change
        stateSel.addEventListener('change', function () {
            const stateCode = this.value;
            updateCities(citySel, stateCode);
        });

        // Initial populate if state is pre-selected
        if (stateSel.value) {
            updateCities(citySel, stateSel.value, citySel.dataset.selected);
        }
    });
}

function updateCities(citySel, stateCode, selectedCity = "") {
    citySel.innerHTML = '<option value="">Select City</option>';
    if (stateCode && US_LOCATIONS[stateCode]) {
        US_LOCATIONS[stateCode].sort().forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            if (selectedCity === city) {
                option.selected = true;
            }
            citySel.appendChild(option);
        });
    }
}

document.addEventListener('DOMContentLoaded', initLocationSelectors);
