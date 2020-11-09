function checkReload() {
    const Http = new XMLHttpRequest()
    const url = 'http://distant-horizon.io/build_time'
    Http.open("GET", url);
    console.log("requesting last build time...");
    Http.send();
    Http.onreadystatechange = (e) => {
        const data = JSON.parse(Http.responseText);
        const server_build_time = data.time;
        const cached_build_time = getCookie("buildTime");
        console.log("server last build time is " + server_build_time, " cached build time is " + cached_build_time); 
        if(!cached_build_time || server_build_time > cached_build_time){
            console.log("cached client is out of date, reloading.");
            setCookie("buildTime", server_build_time);
            location.reload(true);
        } else {
            console.log("cached client is up to date, no reload required.")
        }
    }
}

function setCookie(cname, cvalue, exdays) {
  var d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  var expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}
