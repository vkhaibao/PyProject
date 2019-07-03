document.addEventListener('LocalEvent', function(evt) {
chrome.runtime.sendMessage({type: "launch", message: evt.detail}, function(response) {

});
}, false);