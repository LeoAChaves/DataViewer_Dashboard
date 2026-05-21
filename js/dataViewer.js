// Session
function getSessionFromURL() {
  let searchParams = new URLSearchParams(window.location.search);
  if (searchParams.has("session")) {
    return searchParams.get("session");
  }
  return null;
}
let urlSession = getSessionFromURL();
async function checkSessionIsValid(session) {
  try {
    const response = await fetch();
    // To be defined
    if (!response.ok) {
      throw new Error("Session validation failed due to server response.");
    }
    const data = await response.json();
    if (!data.success) {
      throw new Error("Invalid session");
    }
    return true;
  } catch (error) {
    displaySessionError(session, error);
    return false;
  }
}
function displaySessionError(session, error) {
  var sessionError = document.querySelector("#sessionError");
  var p = document.createElement("p");
  var divError = document.querySelector("#divError");
  divError.style.display = "block";

  if (session === null || session === "") {
    p.innerHTML = `A sessão não foi definida:\n<span class="italic">${error.message}</span>.`;
  } else {
    p.innerHTML = `<p>A sessão <span class="bold">${session}</span> não está definida, ou ainda não tem dados. Dentro de alguns minutos, recarregue a página.</p><p class="center">Erro: <span class="italic">${error.message}</span>.</p> `;
  }

  // Clear previous errors
  while (sessionError.firstChild) {
    sessionError.removeChild(sessionError.firstChild);
  }

  sessionError.append(p);
}

// Manipulating data
const units = {
  Velocidade: "[ m/s ]",
  Temperatura: "[ °C ]",
  Pressao: "[ hPa ]",
  Umidade: "[ % ]",
  Ultravioleta: "[ W/m² ]",
  Luminosidade: "[ Lux ]",
  Pluviometro: "[ mm ]",
  CO2: "[ ppm ]",
};
async function getTopics(session) {
  const response = await fetch();
  // To be defined
  const data = await response.json();
  let topics = data.result;
  return topics;
}
async function getData(session, topic) {
  const response =
    await fetch();
    // To be defined
  const data = await response.json();
  let topicData = data.result;
  return topicData;
}
function normalizeData(data, topic) {
  const calculateMedian = (values) => {
    const sortedValues = [...values].sort((a, b) => a - b);
    const midIndex = Math.floor(sortedValues.length / 2);
    const median =
      sortedValues.length % 2 !== 0
        ? sortedValues[midIndex]
        : (sortedValues[midIndex - 1] + sortedValues[midIndex]) / 2;
    return parseFloat(median.toFixed(3));
  };

  // Grouping data by 5-minute intervals
  const groupedData = data.reduce((acc, { timestamp, data }) => {
    const date = new Date(timestamp * 1000);
    date.setMinutes(Math.floor(date.getMinutes() / 5) * 5, 0, 0);
    const key = date.getTime();
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(parseFloat(data));

    return acc;
  }, {});

  // Threshold for deciding if a peak is significant
  const peakThreshold = 1.5; // Adjust this based on your data characteristics

  // Calculating final value for each group
  const result = Object.entries(groupedData).map(([key, values]) => {
    let finalValue;
    if (topic === "Pluviometro") {
      // Summing values for 'Pluviometro'
      finalValue = values.reduce((acc, val) => acc + val, 0);
    } else {
      // Default behavior for other topics
      const medianValue = calculateMedian(values);
      const maxValue = parseFloat(Math.max(...values).toFixed(3));
      finalValue = medianValue; // Default to median

      // Check if the max value is significantly higher than the median
      if (maxValue > medianValue * peakThreshold) {
        finalValue = maxValue; // Using max value in case of significant peak
      }
    }

    return {
      timestamp: parseInt(key),
      [topic]: parseFloat(finalValue.toFixed(3)), // Ensuring finalValue is formatted to three decimal places
    };
  });

  return result.sort((a, b) => a.timestamp - b.timestamp);
}
function formatTimestamp(unixTimestamp) {
  const date = new Date(unixTimestamp);
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const year = date.getFullYear();
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");

  return `${day}/${month}/${year} ${hours}:${minutes}`;
}
function mergeDataByTimestamp(...topicDataArrays) {
  const result = {};

  topicDataArrays.forEach((dataArray) => {
    dataArray.forEach((dataObj) => {
      const { timestamp } = dataObj;

      if (!result[timestamp]) {
        result[timestamp] = { timestamp };
      }

      Object.entries(dataObj).forEach(([key, value]) => {
        if (key !== "timestamp") {
          result[timestamp][key] = value;
        }
      });
    });
  });

  const sortedResults = Object.keys(result)
    .sort((a, b) => a - b)
    .map((timestamp) => ({
      ...result[timestamp],
    }));

  return sortedResults;
}
async function processTopicData(session) {
  try {
    const topics = await getTopics(session);
    const topicDataPromises = topics.map(async (topic) => {
      const rawData = await getData(session, topic);
      return normalizeData(rawData, topic);
    });
    const topicDataArrays = await Promise.all(topicDataPromises);
    const mergedData = mergeDataByTimestamp(...topicDataArrays);
    return mergedData;
  } catch (error) {
    console.error("Error processing topic data:", error);
    throw error;
  }
}

// Initializing Everything
$(document).ready(async function () {
  const validSession = await checkSessionIsValid(urlSession);
  if (validSession) {
    try {
      await processDataAndCreateGauges(urlSession);
      const mergedData = await processTopicData(urlSession);
      createDynamicElements(mergedData);

      await createLineCharts(mergedData, 288, urlSession);
      var downloadButton = document.querySelector("#download-table");
      downloadButton.style.display = "block";
    } catch (error) {
      console.error("Failed to process data:", error);
    }
  }
});
