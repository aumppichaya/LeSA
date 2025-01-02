// Start the extension
document.getElementById("startLogger").addEventListener("click", () => {
   /* chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        files: ["content.js"], // Inject content.js
      });
    });*/
    console.log("Extension started");
  });
  
  // Stop the extension
  document.getElementById("stopLogger").addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        func: () => {
          // Remove any intervals or clean up
          if (window.extensionInterval) {
            clearInterval(window.extensionInterval);
            delete window.extensionInterval;
            console.log("Extension stopped");
          }
        },
      });
    });
  });
  