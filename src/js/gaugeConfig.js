const gaugeContainer = document.getElementById("gauge-container");

function createGaugeContainer(topic) {
  const gauge = document.createElement("div");
  gauge.className = "gauge";
  gauge.id = `gauge-${topic}`; // Use topic as part of the ID to ensure uniqueness
  gaugeContainer.appendChild(gauge);
  return gauge.id;
}
function createGauge(topic, lastReading, maxValue, minValue, containerId) {
  const unit = units[topic] || "";
  Highcharts.chart(containerId, {
    chart: {
      type: "solidgauge",
    },
    title: {
      text: `${topic} ${unit}`, // Set the chart title equal to the topic
      align: "center",
      verticalAlign: "top",
      style: {
        fontSize: "22px",
      },
    },
    pane: {
      center: ["50%", "85%"],
      size: "140%",
      startAngle: -90,
      endAngle: 90,
      background: {
        backgroundColor: "#EEE",
        innerRadius: "60%",
        outerRadius: "100%",
        shape: "arc",
      },
    },
    tooltip: {
      enabled: false,
    },
    yAxis: {
      stops: [
        [0.1, "#ADD8E6"],
        [0.5, "#5474A8"],
        [0.9, "#191970"],
      ],
      min: minValue,
      max: maxValue,
      lineWidth: 0,
      minorTickInterval: null,
      tickPixelInterval: 400,
      tickWidth: 0,
      title: {
        y: -70,
      },
      labels: {
        y: 16,
        style: {
          fontSize: "12px",
        },
      },
      tickPositions: [minValue, maxValue],
    },
    plotOptions: {
      solidgauge: {
        dataLabels: {
          y: 10,
          borderWidth: 0,
          useHTML: true,
        },
      },
    },
    series: [
      {
        name: topic,
        data: [
          {
            color: Highcharts.getOptions().colors[2],
            radius: "100%",
            innerRadius: "60%",
            y: lastReading,
          },
        ],
        dataLabels: {
          format:
            '<div style="text-align:center"><span style="font-size:25px;color:#000000">{y}</span></div>',
        },
      },
    ],
  });
}
async function processDataAndCreateGauges(session) {
  try {
    const topics = await getTopics(session);
    for (const topic of topics) {
      const rawData = await getData(session, topic);
      const normalizedData = normalizeData(rawData, topic);
      let lastReading;
      let sumReading;
      if (topic === "Pluviometro") {
        // Sum of the last 288 readings (24h)
        lastReading = normalizedData
          .slice(-288)
          .reduce((acc, data) => acc + data[topic], 0);
        // Sum of all readings for 'Pluviometro'
        sumReading = normalizedData
          .slice(-2016)
          .reduce((acc, data) => acc + data[topic], 0);
      } else {
        // Default behavior for other topics
        lastReading = normalizedData[normalizedData.length - 1][topic];
        sumReading = Math.max(...normalizedData.map((data) => data[topic])); // This is equivalent to 'max'
      }

      const weekReading = normalizedData
        .slice(-2016)
        .map((data) => data[topic]);

      const max =
        topic === "Pluviometro" ? sumReading : Math.max(...weekReading);
      const min = Math.min(...weekReading);
      const containerId = createGaugeContainer(topic);
      createGauge(topic, lastReading, max, min, containerId);
    }
  } catch (error) {
    console.error("Error processing session data and creating gauges:", error);
  }
}
