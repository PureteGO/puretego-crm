chrome.runtime.onMessageExternal.addListener(
    function(request, sender, sendResponse) {
        
        if (request.id && request.email) {

            chrome.storage.local.get(function(result) {

                let last_active_tab = result.tab_id;

                chrome.storage.local.set({"user": request}, function() {
                    
                    
                    chrome.tabs.sendMessage(last_active_tab, {
                        "message": "logged_in"
                    });


                    chrome.tabs.update(last_active_tab, {
                        selected: true
                    });

                    chrome.tabs.query({ active: false, currentWindow: true}, function(tabs) {
                        for (let i = 0; i < tabs.length; i++) {
                            if (tabs[i].url == "https://app.gbpcheck.com/extension/auth" || tabs[i].url.includes(".gbpcheck.com/extension/auth")) {
                                chrome.tabs.remove(tabs[i].id);
                            }
                        }
                    });




                });


            });



        }


        return false;



    });



chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        if (request.method == "get_tab") {

            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                sendResponse({
                    "tab_id": tabs[0].id
                });
            });

            return true;


        }
    }
);

let app_root_url = "https://app.gbpcheck.com";
let app_root_local_url = "http://localhost:5000";

chrome.runtime.onInstalled.addListener(function(details){
    if(details.reason == "install" || details.reason == "update"){
        //redirect to url 
        // let extension_version = chrome.runtime.getManifest().version;
        // chrome.tabs.create({ url: app_root_url + "/extension/welcome?version=" + extension_version });

    }
});