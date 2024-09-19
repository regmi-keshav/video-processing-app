// Handle video upload
document.getElementById("upload-form").addEventListener("submit", function (e) {
  e.preventDefault();

  const formData = new FormData(this);
  fetch("/api/upload/", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      alert("Video uploaded successfully!");
      loadVideoList(); // Refresh video list after upload
    })
    .catch((error) => {
      console.error("Error uploading video:", error);
    });
});

// Fetch and display the list of videos
function loadVideoList() {
  fetch("/api/videos/")
    .then((response) => response.json())
    .then((videos) => {
      const videoListDiv = document.getElementById("video-list");
      videoListDiv.innerHTML = "";

      videos.forEach((video) => {
        const videoItem = document.createElement("div");
        videoItem.innerHTML = `<p><a href="#" onclick="playVideo('${video.video_file}', ${video.id}); return false;">${video.title}</a></p>`;
        videoListDiv.appendChild(videoItem);
      });
    })
    .catch((error) => {
      console.error("Error fetching video list:", error);
    });
}

// Play the selected video and load subtitles
function playVideo(videoSrc, videoId) {
  const videoPlayer = document.querySelector("video");
  const videoSource = document.getElementById("video-source");
  const subtitleTrack = document.getElementById("subtitle-track");

  videoSource.src = videoSrc;
  videoPlayer.load(); // Reload video

  // Load subtitles
  fetch(`/api/videos/${videoId}/subtitles/`)
    .then((response) => response.json())
    .then((subtitles) => {
      const subtitleFileUrl = `/media/subtitles/${subtitles.filename}`;
      subtitleTrack.src = subtitleFileUrl;
      subtitleTrack.mode = "showing"; // Display subtitles
      videoPlayer.load();
    });
}

// Search subtitles
document.getElementById("search-button").addEventListener("click", function () {
  const query = document.getElementById("search-query").value;
  const videoId = document.querySelector("video").dataset.videoId; // Get the current video ID

  fetch(`/api/videos/${videoId}/search/?query=${query}`)
    .then((response) => response.json())
    .then((results) => {
      const searchResultsDiv = document.getElementById("search-results");
      searchResultsDiv.innerHTML = "";

      results.forEach((result) => {
        const resultItem = document.createElement("div");
        resultItem.innerHTML = `<p><a href="#" onclick="playFromTimestamp('${result.timestamp}'); return false;">${result.content} - ${result.timestamp}</a></p>`;
        searchResultsDiv.appendChild(resultItem);
      });
    })
    .catch((error) => {
      console.error("Error searching subtitles:", error);
    });
});

// Play video from the specified timestamp
function playFromTimestamp(timestamp) {
  const videoPlayer = document.querySelector("video");
  const timeParts = timestamp.split(":");
  const seconds = +timeParts[0] * 3600 + +timeParts[1] * 60 + +timeParts[2];
  videoPlayer.currentTime = seconds;
  videoPlayer.play();
}

// Load video list when page loads
document.addEventListener("DOMContentLoaded", loadVideoList);
