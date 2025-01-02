chrome.runtime.onInstalled.addListener(() => {
    chrome.notifications.create({
        type: "basic",
        iconUrl: "icon.png",
        title: "LeSA",
        message: "LeSA is here!. \r\nJoin the vdo conference and enable LeSA from Extension button.",
    });
});


// Listen for the extension icon click event
chrome.action.onClicked.addListener((tab) => {
    // Show a confirmation notification
    chrome.notifications.create("confirmRun", {
        type: "basic",
        iconUrl: "icon.png",
        title: "LeSA",
        message: "Do you want to allow LeSA to monitor the video conference?",
        buttons: [
            { title: "Yes" },
            { title: "No" },
        ],
        requireInteraction: true,
    });
});


// Listen for notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
    if (notificationId === "confirmRun") {
        if (buttonIndex === 0) {
            // User clicked "Yes"
            console.log("User allowed the extension.");

            // Inject content.js into the active tab
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    files: ["content.js"],
                });
            });
        } else if (buttonIndex === 1) {
            // User clicked "No"
            console.log("User denied the extension.");
        }
    }
});