document.getElementById("search-button").addEventListener("click", function () {
  const query = document.getElementById("search-query").value;
  const videoId = 1; // Replace with actual video ID

  fetch(`/videos/${videoId}/search/?q=${query}`)
    .then((response) => response.json())
    .then((data) => {
      const resultsDiv = document.getElementById("results");

      resultsDiv.innerHTML = "";
      data.results.forEach((result) => {
        const div = document.createElement("div");
        div.innerHTML = `<a href="#" onclick="playFromTimestamp('${result.timestamp}'); return false;">${result.timestamp}</a>: ${result.content}`;
        resultsDiv.appendChild(div);
      });
    })
    .catch((error) => {
      console.error("Error fetching search results:", error);
      const resultsDiv = document.getElementById("results");
      resultsDiv.innerHTML =
        "<p>Error fetching search results. Please try again.</p>";
    });
});

function playFromTimestamp(timestamp) {
  const video = document.querySelector("video");
  if (video) {
    const timeParts = timestamp.split(":").map(Number);
    const seconds = timeParts[0] * 3600 + timeParts[1] * 60 + timeParts[2];
    video.currentTime = seconds;
    video.play();
  } else {
    console.error("Video element not found.");
  }
}
