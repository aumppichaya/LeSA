chrome.runtime.onInstalled.addListener(() => {
    console.log("WebCam Extension Installed");
  });
  
  // Optional: Log data or handle events in the background
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Received message:", message);
    sendResponse({ status: "success" });
  });
  