async function populateCSVDropdown() {
    const response = await fetch("/api/csv-files");
    const csvFiles = await response.json();

    const selector = document.getElementById("csvSelector");
    selector.innerHTML = "";
    csvFiles.forEach(file => {
        const option = document.createElement("option");
        option.value = file;
        option.textContent = file;
        selector.appendChild(option);
    });
}

function parseCSV(csvText) {
    const lines = csvText.trim().split("\n");
    const result = [];

    for (let i = 1; i < lines.length; i++) {
        const [date, open, high, low, close] = lines[i].split(",");
        result.push({
            time: Math.floor(new Date(date).getTime() / 1000),
            open: parseFloat(open),
            high: parseFloat(high),
            low: parseFloat(low),
            close: parseFloat(close)
        });
    }

    return result;
}

function drawChart(data) {
    document.getElementById("chart").innerHTML = "";
    const chart = LightweightCharts.createChart(document.getElementById("chart"), {
        width: 800,
        height: 400
    });

    const candlestickSeries = chart.addCandlestickSeries();
    candlestickSeries.setData(data);
}

document.getElementById("csvSelector").addEventListener("change", async function () {
    const selectedFile = this.value;
    if (!selectedFile) return;
    const response = await fetch(`/data/${selectedFile}`);
    const text = await response.text();
    const parsedData = parseCSV(text);
    drawChart(parsedData);
});

populateCSVDropdown();
