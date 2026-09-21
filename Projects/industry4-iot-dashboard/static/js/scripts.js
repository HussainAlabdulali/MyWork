let canNotify = true;

// Dashboard pages share this script. Each module polls /api/read and maps the
// latest sensor packet into the UI for one monitoring view.
(function () {
    window.exportFakeLog = function (type) {
        const csvContent = "data:text/csv;charset=utf-8,Time,Event\n" +
            Array.from({length: 5}, (_, i) =>
                `${new Date().toLocaleTimeString()},Sample ${type} Event ${i + 1}`).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `${type}-log.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    /*Tool drop page functions*/
    window.simulateToolDrop = function () {
        let canNotify = true;
        const led = document.getElementById("toolLed");
        const statusText = document.getElementById("ledStatusText");
        const latch = document.getElementById("magLatchLed");
        const soundBar = document.getElementById("soundLevelBar");
        const gif = document.getElementById("toolDropGif");

        let lastMagnitude = null; // Track last value to avoid duplicates

        // Function to format timestamp
        function getTimestamp() {
            const now = new Date();
            return {
                timestamp: now.toISOString(),
                date: now.toLocaleDateString(),
                time: now.toLocaleTimeString()
            };
        }

        // Export function for manual CSV download - fetches from server
        window.exportToolDropCSV = function () {
            const today = new Date().toISOString().split('T')[0];
            const filename = `tool_drop_${today}.csv`;

            // Fetch the CSV file from server
            fetch(`/api/download-csv/${filename}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('No data available for export');
                    }
                    return response.blob();
                })
                .then(blob => {
                    // Create download link
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `tool_drop_export_${today}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                })
                .catch(error => {
                    console.error('Export error:', error);
                    alert('No data available for export yet, or error occurred.');
                });
        };

        setInterval(() => {
            fetch('/api/read')
                .then(res => res.json())
                .then(data => {
                    const magnitude = data.magnitude;
                    updateMagnitude(magnitude);
                    const mag = data.mag;

                    const sound = data.sound;
                    updateSound(sound)


                    // Threshold from user input
                    const threshold = parseFloat(document.getElementById("toolDropThreshold").value);

                    if (mag < 3){
                        magLatchLed.classList.replace("led-green", "led-red");
                    }else{
                        magLatchLed.classList.replace("led-red", "led-green");
                    }
                    if (magnitude >= threshold) {
                        led.classList.replace("led-green", "led-red");
                        statusText.textContent = "Status: Alert!";
                        showNotification("Tool Drop Detected!", "Check the machine.")

                        // Only set GIF src if it's not already set
                        if (!gif.src.includes("tool-drop.gif")) {
                            gif.src = "../static/pics/tool-drop.gif";
                        }
                        gif.style.display = "block";
                    } else {
                        led.classList.replace("led-red", "led-green");
                        statusText.textContent = "Status: Good";

                        // Only set fallback image if it's not already set
                        if (!gif.src.includes("cnc2.png")) {
                            gif.src = "../static/pics/cnc2.png";
                        }
                        gif.style.display = "block";
                    }
                })
                .catch(err => {
                    console.error("Error fetching tool drop data:", err);
                });
        }, 500);
    };

    function updateMagnitude(magnitude) {
        const bar = document.getElementById("dropMagnitudeBar");
        const percent = Math.min(100, Math.floor((magnitude / 10) * 100));
        bar.style.width = percent + "%";
        bar.setAttribute("aria-valuenow", percent);
        bar.textContent = magnitude.toFixed(1);
    }

    function updateSound(sound) {
        const bar = document.getElementById("soundLevelBar");
        const percent = Math.min(100, (sound / 2) * 100);

        bar.style.width = percent.toFixed(2) + "%";
        bar.setAttribute("aria-valuenow", percent.toFixed(2));

        bar.textContent = sound.toFixed(5);
    }

    function showNotification(text, subtext) {
        if (!canNotify) return; // still cooling down, do nothing

        if (Notification.permission === "granted") {
            new Notification(text, {
                body: subtext
            });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    new Notification(text, {
                        body: subtext
                    });
                }
            });
        }

        canNotify = false; // block notifications
        setTimeout(() => {
            canNotify = true; // allow notifications again after 5 seconds
        }, 15000); // cooldown time in milliseconds
    }

    /*Tool drop page functions*/

    /*Vibration page functions*/
    let vibrationChart;
    let timestamps = [];

    window.simulateVibration = function () {
        const canvas = document.getElementById("vibrationChart");
        if (!canvas) {
            console.error("vibrationChart canvas not found!");
            return;
        }

        const ctx = canvas.getContext("2d");

        if (vibrationChart) {
            vibrationChart.destroy();
        }

        // Initialize timestamps for last 10 seconds
        const now = new Date();
        timestamps = Array.from({length: 10}, (_, i) => {
            const d = new Date(now.getTime() - (9 - i) * 1000);
            return d.toLocaleTimeString();
        });

        vibrationChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: "Magnitude",
                        data: Array(10).fill(0),
                        borderColor: "orange",
                        fill: false,
                        borderWidth: 2,
                        tension: 0.3,
                    },
                ],
            },
            options: {
                animation: false,
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Magnitude",
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: "Time",
                        },
                    },
                },
            },
        });

        async function update() {
            try {
                const response = await fetch("/api/read");
                if (!response.ok) throw new Error("Network response was not ok");
                const data = await response.json();
                const mag = data.mag;
                const sound = data.sound;

                let {x_axis, y_axis, z_axis, magnitude, timestamp} = data;

                // Update XYZ text
                document.getElementById("xCoord").textContent = x_axis.toFixed(2);
                document.getElementById("yCoord").textContent = y_axis.toFixed(2);
                document.getElementById("zCoord").textContent = z_axis.toFixed(2);

                updateSound(sound);

                const tilt = document.getElementById("tiltValue");
                tilt.textContent = data.tilt;

                // Reset axis visuals
                ["xAxis", "yAxis", "zAxis"].forEach(id => {
                    document.getElementById(id).setAttribute("stroke-width", "1");
                });

                x_axis = Math.abs(x_axis);
                y_axis = Math.abs(y_axis);
                z_axis = Math.abs(z_axis - 1);

                const maxVal = Math.max(x_axis, y_axis, z_axis);
                if (maxVal === x_axis) document.getElementById("xAxis").setAttribute("stroke-width", "4");
                else if (maxVal === y_axis) document.getElementById("yAxis").setAttribute("stroke-width", "4");
                else document.getElementById("zAxis").setAttribute("stroke-width", "4");

                // Update chart
                const nowTime = timestamp ? new Date(timestamp) : new Date();
                timestamps.push(nowTime.toLocaleTimeString());
                timestamps.shift();

                vibrationChart.data.labels = timestamps;
                vibrationChart.data.datasets[0].data.push(magnitude);
                vibrationChart.data.datasets[0].data.shift();

                vibrationChart.update();
            } catch (error) {
                console.error("Failed to fetch vibration data:", error);
            }
        }

        update();
        setInterval(update, 500);
    };

// Export function for full accelerometer data CSV
    window.exportFullAccelCSV = function () {
        const today = new Date().toISOString().split('T')[0];
        const filename = `full-accel-export-${today}.csv`;

        // First, get the data from your existing /api endpoint
        fetch('/api', {
            method: 'GET'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch data from API');
                }
                return response.json();
            })
            .then(apiData => {
                // Check if full accelerometer data exists
                if (!apiData.full_accel_data || !apiData.full_accel_data.file_exists) {
                    throw new Error('No full accelerometer data available');
                }

                // If data exists, fetch the actual CSV file
                return fetch('/full-accel-data.csv');
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Full accelerometer CSV file not found on server');
                }
                return response.text();
            })
            .then(csvData => {
                // Create and download the CSV file
                const blob = new Blob([csvData], {type: 'text/csv'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a); // Append to body for Firefox compatibility
                a.click();
                document.body.removeChild(a); // Clean up
                URL.revokeObjectURL(url);

                console.log(`Successfully exported: ${filename}`);

                // Optional: Show success message to user
                if (typeof showNotification === 'function') {
                    showNotification('Export Successful', `Downloaded ${filename}`);
                }
            })
            .catch(error => {
                console.error('Export error:', error);
                alert('No full accelerometer data available for export yet, or error occurred: ' + error.message);
            });
    };

    /*Vibration page functions*/

    /*Agv page functions*/
    window.simulateAgvCollision = async function () {
        const ledBall = document.getElementById("ledBall");
        const Ball = document.getElementById("Ball");
        const pitchValue = document.getElementById("pitchValue");
        const rollValue = document.getElementById("rollValue");
        const agvThreshold = parseFloat(document.getElementById("agvThreshold").value);

        try {
            const res = await fetch('/api/read');
            const data = await res.json();

            const x = data.x_axis;
            const y = data.y_axis;
            const z = data.z_axis;
            const fall = data.fall;

            const {pitch, roll} = getTiltAngles(x, y, z);
            const tilt = data.tilt;

            pitchValue.textContent = `${pitch.toFixed(1)}°`;
            rollValue.textContent = `${roll.toFixed(1)}°`;

            if (Math.abs(pitch) > agvThreshold + 10 || Math.abs(roll) > agvThreshold + 10 || tilt > 0.1) {
                Ball.classList.replace("green", "red");
                showNotification("Alert! Tilt Detected", "Check the AGV");

            } else
                Ball.classList.replace("red", "green");

            if (fall === 0) {
                ledBall.classList.replace("green", "red");
                showNotification("Alert! Collision Detected", "Check the AGV");
            } else
                ledBall.classList.replace("red", "green");

        } catch (err) {
            console.error("Error fetching /api/read:", err);
        }
    };

    function getTiltAngles(x, y, z) {
        const pitch = Math.atan2(y, Math.sqrt(x * x + z * z)) * (180 / Math.PI);
        const roll = Math.atan2(x, Math.sqrt(y * y + z * z)) * (180 / Math.PI);
        return {pitch, roll};
    }

    /*Agv page functions*/

    /*Package drop page functions*/
    // Separate lastFallState for package drop functionality
    let packageLastFallState = null;

    window.simulatePackageDrop = async function () {
        const log = document.getElementById("packageLog");
        const gif = document.getElementById("dropGif");
        const severity = document.getElementById("dropSeverity");

        try {
            const res = await fetch('/api/read');
            const data = await res.json();

            const fall = data.fall;        // -1 = safe, 0 or 1 = drop
            const magnitude = data.magnitude;
            const sound = data.sound;

            updateSound(sound);

            const timestamp = new Date().toLocaleString();

            const li = document.createElement("li");
            li.className = "list-group-item";
            li.textContent = `[${timestamp}] Package drop detected - Magnitude: ${magnitude.toFixed(2)}`;
            log.prepend(li);

            // Only update GIF and severity if fall state changes
            if (fall !== packageLastFallState) {
                packageLastFallState = fall;

                if (fall === 0 || fall === 1) {
                    showNotification("Package Drop Detected!", `Impact magnitude: ${magnitude.toFixed(2)}`);
                    gif.src = "../static/pics/package-fall.gif";

                    // Determine gif and severity based on magnitude thresholds
                    if (fall === 1) {
                        severity.textContent = `❌ Dangerous Drop! Magnitude: ${magnitude.toFixed(2)}`;
                        severity.style.color = "red";
                    } else {
                        severity.textContent = `⚠️ Warning Drop, Magnitude: ${magnitude.toFixed(2)}`;
                        severity.style.color = "orange";
                    }
                    gif.style.display = "block";
                } else if (fall === -1) {
                    // Prevent safe state from overriding a recent drop
                    severity.textContent = "✅ No drop detected";
                    severity.style.color = "green";

                    // Only show the safe GIF if the current GIF is not the fall one
                    if (!gif.src.includes("package-fall.gif")) {
                        gif.src = "../static/pics/package-drop.gif";
                        gif.style.display = "block";
                    }
                }
            }
        } catch (err) {
            console.error("Error fetching /api/read:", err);
        }
    };

    /*Package drop page functions*/

    /*Worker page functions*/
    // Separate lastFallState for worker fatigue functionality
    let workerLastFallState = null;
    let workerFallCooldown = false;

    window.simulateFatigue = (function () {
        // Chart setup variables scoped to this function
        let fatigueChart = null;
        const baseColors = [
            'rgba(192, 57, 43, 0.9)',
            'rgba(230, 126, 34, 0.6)',
            'rgba(244, 208, 63, 0.3)'
        ];

        // Initialize chart once when function is first called
        function initChart() {
            if (fatigueChart) return; // Already initialized

            const ctx = document.getElementById("fatigueChart");
            if (!ctx) return; // Chart element not found

            fatigueChart = new Chart(ctx.getContext("2d"), {
                type: 'bar',
                data: {
                    labels: ["Posture", "Motion", "Alertness"],
                    datasets: [{
                        label: 'Fatigue Score',
                        data: [0, 0, 0],
                        backgroundColor: baseColors,
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 10,
                            ticks: {
                                stepSize: 1,
                                callback: function (value) {
                                    return value.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        }

        return async function () {
            initChart(); // Ensure chart is initialized

            const Ball = document.getElementById("Ball");
            const gif = document.getElementById("fatigueGif");
            const light = document.getElementById("light");
            const flameBall = document.getElementById("FlameBall");


            try {
                const res = await fetch('/api/read');
                const data = await res.json();
                const {tilt, y_axis, z_axis, fall} = data;
                light.textContent = data.light.toFixed(1);

                const x = Math.abs(tilt) + 1;
                const y = Math.abs(y_axis) + 3;
                const z = Math.abs(z_axis) + 2;
                const fatigueData = [x, y, z];


                if (data.flame < 3){
                    FlameBall.classList.replace("green", "red");
                }else{
                    FlameBall.classList.replace("red" ,"green");
                }
                // FALL detection logic
                if (fall !== workerLastFallState && !workerFallCooldown) {
                    workerLastFallState = fall;
                    if (fall === 0 || fall === 1) {
                        Ball.classList.replace("green", "red");
                        gif.src = "../static/pics/worker.gif";
                        gif.style.display = "block";
                        showNotification("A worker has fell!", "Please check up on them.")

                        // Prevent immediate reset
                        workerFallCooldown = true;
                        setTimeout(() => {
                            gif.src = "../static/pics/standing.png";
                            Ball.classList.replace("red", "green");
                            workerFallCooldown = false;
                        }, 4000);
                    } else if (fall === -1) {
                        gif.src = "../static/pics/standing.png";
                        gif.style.display = "block";
                        Ball.classList.replace("red", "green");
                    }
                }

                // Update chart if it exists
                if (fatigueChart) {
                    // Sort for bar color emphasis
                    const sortable = fatigueData.map((v, i) => ({value: v, index: i}));
                    sortable.sort((a, b) => b.value - a.value);
                    const sortedIndices = sortable.map(s => s.index);

                    fatigueChart.data.datasets[0].data = fatigueData;
                    fatigueChart.data.datasets[0].backgroundColor = fatigueData.map((_, i) => baseColors[sortedIndices.indexOf(i)]);
                    fatigueChart.update();
                }
            } catch (err) {
                console.error("Error fetching fatigue data:", err);
            }
        };
    })();

    /*Worker page functions*/

})();

window.addEventListener('DOMContentLoaded', () => {
    window.simulateToolDrop();
    window.simulateVibration();
    window.simulateAgvCollision();
    window.simulatePackageDrop();
    window.simulateFatigue();

    setInterval(window.simulateFatigue, 500)
    setInterval(window.simulatePackageDrop, 500);
    setInterval(window.simulateAgvCollision, 500);
});
