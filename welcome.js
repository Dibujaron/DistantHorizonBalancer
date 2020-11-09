function checkReload() {
    const Http = new XMLHttpRequest()
    const url = 'http://distant-horizon.io/build_time'
    Http.open("GET", url);
    Http.send();
    Http.onreadystatechange = (e) => {
        console.log(Http.responseText)
    }
}