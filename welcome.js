class TextScramble {
  constructor(el) {
    this.el = el
    this.chars = "!<>-_\\/[]{}—=+*^?#________"
    this.update = this.update.bind(this)
  }
  setText(newText) {
    const oldText = this.el.innerText
    const length = Math.max(oldText.length, newText.length)
    const promise = new Promise((resolve) => this.resolve = resolve)
    this.queue = []
    for (let i = 0; i < length; i++) {
      const from = oldText[i] || ""
      const to = newText[i] || ""
      const start = Math.floor(Math.random() * 40)
      const end = start + Math.floor(Math.random() * 40)
      this.queue.push({ from, to, start, end })
    }
    cancelAnimationFrame(this.frameRequest)
    this.frame = 0
    this.update()
    return promise
  }
  update() {
    let output = ""
    let complete = 0
    for (let i = 0, n = this.queue.length; i < n; i++) {
      let { from, to, start, end, char } = this.queue[i]
      if (this.frame >= end) {
        complete++
        output += to
      } else if (this.frame >= start) {
        if (!char || Math.random() < 0.28) {
          char = this.randomChar()
          this.queue[i].char = char
        }
        output += `<span class="dud">${char}</span>`
      } else {
        output += from
      }
    }
    this.el.innerHTML = output
    if (complete === this.queue.length) {
      this.resolve()
    } else {
      this.frameRequest = requestAnimationFrame(this.update)
      this.frame++
    }
  }
  randomChar() {
    return this.chars[Math.floor(Math.random() * this.chars.length)]
  }
}

Array.prototype.random = function () {
  return this[Math.floor((Math.random()*this.length))];
}

const splashes = [
    [
        "Neo.",
        "Sooner or later",
        "you're going to realize",
        "that there's a difference",
        "between knowing the path",
        "and walking it."
    ],[
        "Recommended by nine out of ten dentists!"
    ],[
        "Gluten Free!"
    ],[
        "Internally consistent!"
    ],[
        "Now with extra pixels!"
    ],[
        "Futuristic!"
    ],[
        "Open-source!"
    ],[
        "Rather, teach them to long for the endless immensity of the sea..."
    ],[
        "Stallman - approved!"
    ],[
        "Now with 50% fewer beavers!"
    ],[
        "Powered by WebAssembly!"
    ],[
        "Powered by Kotlin!"
    ],[
        "Built with Godot!"
    ],[
        "Somewhat realistic!"
    ],[
        "Unethical capitalism!"
    ],[
        "Spaceships!"
    ],[
        "Artificial Intelligence!",
        "Blockchain!",
        "The Cloud (tm)!"
    ],[
        "Inspired by Firefly!"
    ],[
        "Inspired by The Expanse!"
    ],[
        "Inspired by StarQuest!"
    ],[
        "Inspired by FTL!"
    ],[
        "Inspired by KSP!"
    ],[
        "Inspired by 'Pirates!'"
    ],[
        "Free to play!"
    ],[
        "Not P2W!"
    ],[
        "No woman can step in the same river twice.",
        "For it is not the same river,",
        "and she is not the same woman."
    ],[
        "No man can step in the same river twice.",
        "For it is not the same river,",
        "and he is not the same man."
    ],[
        "Someday we will build a thinking machine...",
        "a truly intelligent machine!",
        "A machine that can see...",
        "a machine that can speak...",
        "A machine that will be proud of us."
    ],[
        "RESULTS ARE NOT GUARANTEED",
        "BUT IF YOU ARE NOT PERFECTLY SATISFIED",
        "YOUR WASTED TIME WILL BE REFUNDED"
    ],[
        "Han shot first!"
    ],[
        "Contains no aliens*!"
    ],[
        "Trade!"
    ],[
        "Racing! (coming soon)"
    ],[
        "Passengers! (coming soon)"
    ],[
        "One must always choose the lesser of two weevils!"
    ],[
        "Uh... everything's under control!... situation.. normal!",
        "We, ah, had a slight, ah, weapons.. malfunction....",
        "But, everything's perfectly all right now!",
        "We're fine... we're all fine here, now.. Thank you!.. How are you?"
    ],[
        "S: Are you Alliance?",
        "J: Am I 'a lion'?",
        "S: What?",
        "J: I don't think of myself as a lion. You might as well, though...",
        "J: I have a mighty roar!",
        "S: I said 'Alliance'.",
        "J: Oh, I thought..."
    ],[
        "Objects in space!"
    ],[
        "When will Trantor be destroyed?"
    ],[
        "Don't panic!"
    ],[
        "Space is big. Really big!",
        "You won't believe how vastly, hugely big it is!",
        "I mean, you may think it's a long way to the supermarket...",
    ],[
        "The Amulet of Samarkand!",
        "It was Simon Lovelace's. Now it is yours..",
        "Soon it will be Simon Lovelace's again."
    ],[
        "Insanity is contagious."
    ],[
        "Evil...",
        "Sometimes, it was something that stood up and announced itself clearly.",
        "Like when he was born a Muslim, and the Christians were evil...",
        "or when he was born Christian, and the Muslims were evil.",
        "He thanked God, in those lives, for making it so obvious."
    ],[
        "Never doubt that a small group of dedicated individuals can change the world.",
        "It is the only thing that ever has."
    ],[
        "Contains nuts!"
    ]
]

function random(min, max){
    return min + Math.random() * (max - min)
} 
window.onload = function() {
    const el = document.getElementById("splashtext")
    let newangle = random(-5,5)
    console.log(newangle)
    el.style.transform = "rotate(" + newangle + "deg)"
    const fx = new TextScramble(el)
    let splash = splashes.random()
    //let splash = splashes[splashes.length - 1]
    let counter = 0
    let isFirst = true
    const next = () => {
        if ( isFirst ){
            setTimeout(next, random(9200, 9200+3200));
            isFirst = false;
        } else if( counter < splash.length ){
            let dur = 3200;
            if(counter < splash.length - 1){
                dur = 2400;
            }
            fx.setText(splash[counter]).then(() => {
                setTimeout(next, dur);
            });
            counter++;
        } else {
            fx.setText("").then(() => {
                setTimeout(next, random(9200,9200+3200));
                newangle = random(-5,5)
                console.log(newangle)
                el.style.transform = "rotate(" + newangle + "deg)"
            });
            splash = splashes.random()
            counter=0;
        }
    }
    next()
}