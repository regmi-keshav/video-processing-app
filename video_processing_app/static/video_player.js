// Handle video upload
document.getElementById("upload-form").addEventListener("submit", function (e) {
  e.preventDefault();

  const formData = new FormData(this);
  fetch("/api/upload/", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Error uploading video: " + response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      alert("Video uploaded successfully!");
      loadVideoList(); // Refresh video list after upload
    })
    .catch((error) => {
      console.error("Error uploading video:", error);
      alert("Failed to upload video: " + error.message);
    });
});

// Fetch and display the list of videos
function loadVideoList() {
  fetch("/api/videos/")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Error fetching video list: " + response.statusText);
      }
      return response.json();
    })
    .then((videos) => {
      const videoListDiv = document.getElementById("video-list");
      videoListDiv.innerHTML = ""; // Clear the existing list

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
  const videoPlayer = document.getElementById("video-player");
  const videoSource = document.getElementById("video-source");

  videoSource.src = videoSrc;
  videoPlayer.load(); // Reload video with the new source

  // Clear previous search results when a new video is selected
  document.getElementById("search-results").innerHTML = "";

  // Set the videoId as a data attribute on the video element
  videoPlayer.dataset.videoId = videoId; // Set video ID here

  // Remove existing subtitle tracks from the video player
  const tracks = videoPlayer.querySelectorAll("track");
  tracks.forEach((track) => track.remove());

  // Load subtitles from the backend
  fetch(`/api/videos/${videoId}/languages/`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Error loading subtitles: " + response.statusText);
      }
      return response.json();
    })
    .then((languages) => {
      const videoBaseName = videoSrc.split("/").pop().split("_stream")[0];

      // Create and append a <track> element for each subtitle
      languages.forEach((language) => {
        const trackElement = document.createElement("track");
        trackElement.kind = "subtitles";
        trackElement.label = language.name;
        trackElement.srclang = language.code;
        trackElement.src = `/media/videos/${videoBaseName}_stream_${language.code}.vtt`; // Correct subtitle file path
        console.log("Subtitle file:", trackElement.src);
        if (language.is_default) {
          trackElement.default = true;
        }
        videoPlayer.appendChild(trackElement);
      });

      videoPlayer.load(); // Reload the video to apply new tracks
    })
    .catch((error) => {
      console.error("Error loading subtitles:", error);
    });
}

// Search subtitles with multilingual support
document.getElementById("search-button").addEventListener("click", function () {
  const query = document.getElementById("search-query").value.toLowerCase();
  const videoId = document.querySelector("video").dataset.videoId; // Get the current video ID

  fetch(
    `/api/videos/${videoId}/subtitles/search/?query=${encodeURIComponent(
      query
    )}`
  )
    .then((response) => {
      if (!response.ok) {
        throw new Error("Error searching subtitles: " + response.statusText);
      }
      return response.json();
    })
    .then((results) => {
      const searchResultsDiv = document.getElementById("search-results");
      searchResultsDiv.innerHTML = ""; // Clear previous search results

      if (results.length === 0) {
        searchResultsDiv.innerHTML = "<p>No subtitles found for the query.</p>";
        return;
      }

      results.forEach((result) => {
        const resultItem = document.createElement("div");
        resultItem.innerHTML = `<p><a href="#" onclick="playFromTimestamp('${result.timestamp_start}'); return false;">${result.content} - ${result.timestamp_start}</a></p>`;
        searchResultsDiv.appendChild(resultItem);
      });
    })
    .catch((error) => {
      console.error("Error searching subtitles:", error);
    });
});

// Play from the timestamp based on search results
function playFromTimestamp(timestamp) {
  const videoPlayer = document.getElementById("video-player");
  console.log("Trying to play from timestamp:", timestamp); // Log the timestamp

  let timeParts = timestamp.split(":");
  let hours = 0,
    minutes = 0,
    seconds = 0;

  if (timeParts.length === 2) {
    [minutes, seconds] = timeParts;
  } else if (timeParts.length === 3) {
    [hours, minutes, seconds] = timeParts;
  }
  seconds = seconds.replace(",", "."); // Handle both ',' and '.' separators

  const totalSeconds = +hours * 3600 + +minutes * 60 + parseFloat(seconds);
  if (isNaN(totalSeconds)) {
    console.error("Invalid timestamp format:", timestamp);
    return;
  }

  const seekVideo = () => {
    console.log("Setting video to time:", totalSeconds); // Log the target time
    videoPlayer.currentTime = totalSeconds;
    videoPlayer.play(); // Start playing from the given timestamp
  };

  // Ensure the video has loaded its metadata before seeking
  if (videoPlayer.readyState >= 1) {
    seekVideo(); // If metadata is already loaded, set the time directly
  } else {
    videoPlayer.addEventListener(
      "loadedmetadata",
      function () {
        seekVideo(); // When metadata is loaded, seek to the time
      },
      { once: true }
    );
  }

  // Listen for the canplay event to ensure the video can start playing after seek
  videoPlayer.addEventListener(
    "canplay",
    function () {
      console.log("Video is ready to play at the specified time");
    },
    { once: true }
  );
}

// Load video list when page loads
document.addEventListener("DOMContentLoaded", loadVideoList);
