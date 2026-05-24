function add_version_to_popup(popup_main_div){
  let version = chrome.runtime.getManifest().version;
  let version_div = document.createElement("div");
  version_div.style.textAlign = "right";
  version_div.style.fontSize = "10px";
  version_div.style.position = "absolute";
  version_div.style.bottom = "10px";
  version_div.style.right = "10px";
  version_div.innerHTML = "v" + version;
  popup_main_div.appendChild(version_div);

}

function set_no_user_display(){    
    let main_div = document.getElementById("main-info-popup");
    main_div.innerHTML = "";

    let div = document.createElement("div");
    div.innerHTML = "Seja bem vindo ao <b>GBP Check Local SEO and Optimization";
    div.style.textAlign = "center";
    div.style.fontSize = "15px";
    div.style.padding = "45px 0px 30px 0px";

    let support_div = document.createElement("div");
    support_div.style.textAlign = "center";
    support_div.style.fontSize = "15px";
    support_div.style.padding = "15px 0px 30px 0px";
    support_div.innerHTML = "Para ajuda, acesse a página:<br><b>gbpcheck.com/suporte</b>";

    main_div.appendChild(div);
    main_div.appendChild(support_div);
    add_version_to_popup(main_div);
}



function set_user_display(user){
  let main_div = document.getElementById("main-info-popup");
  main_div.innerHTML = "";


  let div = document.createElement("div");
  div.innerHTML = "Você está logado no <b>GBP Check Local SEO and Optimization</b>";
  div.style.textAlign = "center";
  div.style.fontSize = "15px";
  div.style.padding = "45px 0px 30px 0px";

  let user_main_info = document.createElement("div");
  user_main_info.style.display = "flex";
  user_main_info.style.justifyContent = "center";
  user_main_info.style.alignItems = "center";
  user_main_info.style.padding = "15px 0px 30px 0px";

  let user_img = document.createElement("img");
  user_img.src = user.picture;
  user_img.style.width = "55px";
  user_img.style.height = "55px";
  user_img.style.borderRadius = "50%";
  user_img.style.margin = "0px 10px 0px 0px";


  let user_info = document.createElement("div");
  user_info.style.display = "flex";
  user_info.style.flexDirection = "column";
  

  let user_name = document.createElement("div");
  user_name.innerText = user.username;
  user_name.style.fontSize = "15px";

  let user_mail = document.createElement("div");
  user_mail.innerText = user.email;
  user_mail.style.fontSize = "15px";

  user_info.appendChild(user_name);
  user_info.appendChild(user_mail);

  user_main_info.appendChild(user_img);
  user_main_info.appendChild(user_info);

  let support_div = document.createElement("div");
  support_div.style.textAlign = "center";
  support_div.style.fontSize = "15px";
  support_div.style.padding = "15px 0px 30px 0px";
  support_div.innerHTML = "Para ajuda, acesse a página:<br><b>gbpcheck.com/suporte</b>";

  main_div.appendChild(div);
  main_div.appendChild(user_main_info);
  main_div.appendChild(support_div);
  add_version_to_popup(main_div);
}



function logout_user(){

  chrome.storage.local.set({"user":{}}, function(result) {

    chrome.tabs.query({currentWindow: true, active: true}, function (tabs){
      var activeTab = tabs[0];
      chrome.tabs.sendMessage(activeTab.id, {"message": "logged_in"});
  });

  })


  document.getElementById("logout-btn").innerText = "Login";
  document.getElementById('logout-btn').addEventListener('click', function() {
    login_user();
  });

  set_no_user_display();

}

function login_user(){
  
  chrome.tabs.query({currentWindow: true, active: true}, function (tabs){
    var activeTab = tabs[0];
    chrome.tabs.sendMessage(activeTab.id, {"message": "auth_user"});
  });
}




chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
  chrome.tabs.sendMessage(tabs[0].id, {"message": "get_url"}, function(response) {
    let IS_GOOGLE = response.url.includes("google.com");
    const IS_MAPS = response.pathname.includes("/maps") && IS_GOOGLE;
    const IS_SEARCH = response.pathname.includes("/search") && IS_GOOGLE;
    const CAN_LOGIN = IS_MAPS || IS_SEARCH;

    if (CAN_LOGIN){
      document.getElementById("login-holder").style.display = "block";
      document.getElementById("no-login-text").style.display = "none";
    }else{
      document.getElementById("login-holder").style.display = "none";
      document.getElementById("no-login-text").style.display = "block";
    }

    
  });
});

function send_page_to_debug(){
  document.getElementById("debug-loader").style.display = "flex";
document.getElementById("debug-btn").style.display = "none";

  chrome.tabs.query({active: true, currentWindow: true}, function (tabs) {
    var activeTab = tabs[0];
    chrome.tabs.sendMessage(activeTab.id, {"message": "debug"}, function(response) {
        document.getElementById("debug-loader").style.display = "none";
        //document.getElementById("debug-btn").style.display = "inline";

        if (response && response.status) {
            document.getElementById('debug-status').style.opacity = "1";
            document.getElementById('debug-status').innerText = response.status;
            document.getElementById('debug-status').style.color = response.status.includes("sucesso") ? "#00aa66" : "#ff0000";

            setTimeout(function(){
                document.getElementById('debug-status').style.opacity = "0";
            }, 3000);
        }
    });
});




}



window.addEventListener('load', (event) => {
  


  chrome.storage.local.get(["user"], function(result) {
    let has_user = false;
    if (result.user){
      if (JSON.stringify(result.user) != JSON.stringify({})){
        has_user = true;
        console.log(result);
        set_user_display(result.user);
      }
    }
    
    
    if (!has_user) {
      document.getElementById("no-login-text").innerText = "Para iniciar, pesquise por um negócio no Google e depois clique em fazer login.";
      document.getElementById("logout-btn").innerText = "Login";
      document.getElementById('logout-btn').addEventListener('click', function() {
        login_user();
      });

      set_no_user_display();

      document.getElementById('debug-btn').style.display = "none";
      document.getElementById('debug-status').style.display = "none";

      

    }else{
      document.getElementById("no-login-text").innerText = "Para utilizar, busque por um negócio no Google Pesquisa e depois clique em Pré Análise.";
      document.getElementById("logout-btn").innerText = "Logout";
      document.getElementById('logout-btn').addEventListener('click', function() {
        logout_user();
      });
      

      document.getElementById('debug-btn').addEventListener('click', function() {
        send_page_to_debug();
      });

    }

  })

});



