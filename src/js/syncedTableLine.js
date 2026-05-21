// Creating charts
function createDynamicElements(data) {
  const allTopics = [
    ...new Set(data.flatMap((item) => Object.keys(item))),
  ].filter((key) => key !== "timestamp");
  const chartContainer = $("#charts-container");
  const tableHeader = $("#table-header");
  chartContainer.empty();
  tableHeader.empty();
  tableHeader.append("<th>Tempo</th>");
  allTopics.forEach((topic) => {
    chartContainer.append(
      `<div id="container-${topic}" style="height: 400px; min-width: 310px; margin: 20px 0px;"></div>`
    );
    const unit = units[topic] || "";
    tableHeader.append(`<th>${topic} ${unit}</th>`);
  });
  populateTable(data, allTopics, 73);
}
function populateTable(data, topics, maxRows) {
  const tbody = $("#data-table tbody");
  tbody.empty();
  data
    .slice()
    .reverse()
    .slice(0, maxRows)
    .forEach((item) => {
      const formattedTimestamp = formatTimestamp(item.timestamp);
      let row = `<tr><td>${formattedTimestamp}</td>`;
      topics.forEach((topic) => {
        const value = item[topic];
        const displayValue =
          value === undefined || value === null
            ? "---"
            : parseFloat(value).toFixed(3); // Replace undefined or null values with '---'
        row += `<td>${displayValue}</td>`;
      });

      row += "</tr>";
      tbody.append(row);
    });
}
async function createLineCharts(data, maxPoints, session) {
  Highcharts.setOptions({
    global: {
      timezoneOffset: +180, // for GMT -3
    },
  });

  try {
    const topics = await getTopics(session);

    topics.forEach((topic) => {
      const unit = units[topic] || "";
      const seriesData = data.map((item) => [
        new Date(item.timestamp).getTime(),
        item[topic],
      ]);
      Highcharts.stockChart(`container-${topic}`, {
        chart: {
          type: "line",
        },
        rangeSelector: {
          buttons: [
            { count: 1, type: "hour", text: "1h" },
            { count: 12, type: "hour", text: "12h" },
            { count: 24, type: "hour", text: "24h" },
            { type: "all", text: "All" },
          ],
          selected: 2,
        },
        title: {
          text: `${topic} ${unit}`,
        },
        xAxis: {
          type: "datetime",
          dateTimeLabelFormats: {
            minute: "%d/%m/%Y %H:%M",
            hour: "%d/%m/%Y %H:%M",
            day: "%d/%m/%Y %H:%M",
            week: "%d/%m/%Y %H:%M",
            month: "%d/%m/%Y %H:%M",
            year: "%d/%m/%Y %H:%M",
          },
        },
        yAxis: {
          title: {
            text: `Valores para ${topic}`,
          },
        },
        tooltip: {
          shared: true,
          crosshairs: true,
          xDateFormat: "%d/%m/%Y %H:%M",
        },
        series: [
          {
            name: topic,
            data: seriesData,
          },
        ],
      });
    });
  } catch (error) {
    console.error("Error fetching topics:", error);
  }
}

// Download the table data as a CSV file
function downloadTableAsCSV() {
  var csv = [];
  var rows = document.querySelectorAll("#data-table tr");

  for (var i = 0; i < rows.length; i++) {
    var row = [],
      cols = rows[i].querySelectorAll("td, th");

    for (var j = 0; j < cols.length; j++) {
      // Clean the data to prevent CSV injection and formatting issues
      var data = cols[j].innerText
        .replace(/(\r\n|\n|\r)/gm, "")
        .replace(/(\s\s)/gm, " ");
      data = data.replace(/"/g, '""'); // Escape double-quotes
      row.push('"' + data + '"');
    }

    csv.push(row.join(","));
  }

  // Download the CSV file
  downloadCSV(csv.join("\n"));
}
function downloadCSV(csv, filename = "table-data.csv") {
  var csvFile;
  var downloadLink;

  // CSV file
  csvFile = new Blob([csv], { type: "text/csv" });

  // Download link
  downloadLink = document.createElement("a");

  // File name
  downloadLink.download = filename;

  // Create a link to the file
  downloadLink.href = window.URL.createObjectURL(csvFile);

  // Hide download link
  downloadLink.style.display = "none";

  // Add the link to DOM
  document.body.appendChild(downloadLink);

  // Click download link
  downloadLink.click();

  // Clean up and remove the link
  document.body.removeChild(downloadLink);
}
document
  .getElementById("download-table")
  .addEventListener("click", downloadTableAsCSV, false);
