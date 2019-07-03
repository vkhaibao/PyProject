var port = null;

chrome.runtime.onMessage.addListener(
	function(request, sender, sendResponse) {
		if (request.type == "launch"){
			connectToNativeHost(request.message);
		}
		return true;
	}
);

function onNativeMessage(msg) {
}

function onDisconnected() {
	port = null;
}

function connectToNativeHost(msg) {
	var nativeHostName = "com.logbase.local.launch";
	port = chrome.runtime.connectNative(nativeHostName);
	port.onMessage.addListener(onNativeMessage);
	port.onDisconnect.addListener(onDisconnected);
	port.postMessage({message: msg});
 }