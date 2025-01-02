(async function () {
  // Prevent duplicate execution
  if (window.extensionRunning) {
      console.log("Extension is already running.");
      return;
  }

  console.log("Extension started. Accessing webcam...");

  try {
      // Request webcam access
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });

      // Create a hidden video element
      const videoElement = document.createElement("video");
      videoElement.style.display = "none"; // Keep it invisible
      videoElement.srcObject = stream;

      // Play the video stream
      await videoElement.play();
      console.log("Webcam successfully accessed.");

      // Create a canvas for frame processing
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");

      let frameCount = 0; // Counter for naming files

      // Capture and save video frames in real-time
      setInterval(() => {
          // Set canvas dimensions to match the video
          canvas.width = videoElement.videoWidth;
          canvas.height = videoElement.videoHeight;

          // Draw the current video frame onto the canvas
          context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

          // Convert canvas to a data URL
          const frameData = canvas.toDataURL("image/png");

          // Save the frame as an image file
          const link = document.createElement("a");
          link.href = frameData;
          link.download = `frame_${frameCount}.png`; // Name the file
          link.click();

          console.log(`Saved frame_${frameCount}.png`);
          frameCount++;
      }, 1000); // Capture a frame every second
  } catch (error) {
      console.error("Error accessing webcam:", error);
  }

  // Prevent duplicate runs
  window.extensionRunning = true;
})();
