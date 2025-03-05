document.addEventListener("DOMContentLoaded", () => {
  const sendBtn = document.getElementById("send-btn");
  const userInput = document.getElementById("user-input");
  const chatWindow = document.getElementById("chat-window");

  const moodBtn = document.getElementById("mood-btn");
  const moodInput = document.getElementById("mood-input");
  const moodList = document.getElementById("mood-list");

  let moodChart = null; // We'll store the Chart.js instance here

  // 1. Existing Chat Code
  function appendMessage(text, sender) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    msgDiv.textContent = text;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;  // auto-scroll
  }

  function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Display user message
    appendMessage(message, "user");
    userInput.value = "";

    // Send to backend
    fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
      // Display bot response
      const botResponse = data.response;
      appendMessage(botResponse, "bot");

      // Debug logs (optional)
      console.log("Intent:", data.intent);
      console.log("Similarity:", data.similarity);
      console.log("Sentiment (compound):", data.sentiment_compound);
    })
    .catch(error => {
      console.error("Error:", error);
      appendMessage("Sorry, something went wrong.", "bot");
    });
  }

  // 2. Existing Mood Logging Code
  function logMood() {
    const mood = moodInput.value.trim();
    if (!mood) return;
    
    fetch("/mood", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ mood: mood })
    })
    .then(response => response.json())
    .then(data => {
      console.log(data.message);
      moodInput.value = "";
      // After logging, fetch updated mood list
      fetchMoods();
    })
    .catch(error => {
      console.error("Error logging mood:", error);
    });
  }

  function fetchMoods() {
    fetch("/moods")
      .then(response => response.json())
      .then(data => {
        // Display all moods as text
        moodList.innerHTML = ""; // clear existing
        data.forEach(item => {
          const moodEntry = document.createElement("div");
          const timestamp = new Date(item.timestamp).toLocaleString();
          moodEntry.textContent = `Mood: ${item.mood}, Date: ${timestamp}`;
          moodList.appendChild(moodEntry);
        });

        // Also update the chart
        updateMoodChart(data);
      })
      .catch(error => {
        console.error("Error fetching moods:", error);
      });
  }

  // 3. Converting Moods to Numeric Values
  //    (Example approach: parse integer or map known words)
  function moodToNumber(moodStr) {
    // Try to parse as integer
    const parsed = parseInt(moodStr, 10);
    if (!isNaN(parsed)) {
      return parsed;
    }
    // Otherwise map a few known words
    // You can customize this mapping as needed
    const moodMap = {
      "happy": 4,
      "stressed": 2,
      "sad": 1,
      "neutral": 3
    };
    // default to 3 if not recognized
    return moodMap[moodStr.toLowerCase()] || 3;
  }

  // 4. Render or Update the Chart
  function updateMoodChart(moodData) {
    // Sort moods by timestamp ascending
    moodData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // Prepare chart labels & data
    const labels = moodData.map(item => new Date(item.timestamp).toLocaleDateString() 
                         + " " + new Date(item.timestamp).toLocaleTimeString());
    const dataPoints = moodData.map(item => moodToNumber(item.mood));

    // If the chart already exists, destroy it before re-creating
    if (moodChart) {
      moodChart.destroy();
    }

    // Create new chart
    const ctx = document.getElementById("moodChart").getContext("2d");
    moodChart = new Chart(ctx, {
      type: "line", // or 'bar', 'radar', etc.
      data: {
        labels: labels,
        datasets: [{
          label: "Mood Over Time",
          data: dataPoints,
          borderColor: "rgba(75,192,192,1)",
          backgroundColor: "rgba(75,192,192,0.2)",
          fill: true
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Mood Level"
            }
          },
          x: {
            title: {
              display: true,
              text: "Date/Time"
            }
          }
        }
      }
    });
  }

  // 5. Event Listeners
  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  moodBtn.addEventListener("click", logMood);

  // On page load, fetch existing moods to populate list & chart
  fetchMoods();
});
