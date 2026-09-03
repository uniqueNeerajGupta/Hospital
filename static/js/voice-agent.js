/**
 * PR Harvest — AI-Powered Persistent Voice Agent
 *
 * Unlike a rigid keyword-matcher, this sends what the user says to the
 * same AI agent backend (/api/agent) that powers hospital booking —
 * so it can:
 *   - Understand vague/misremembered requests, not just exact keywords.
 *   - Actually complete actions (like booking a bed), not just navigate.
 *   - Explain the page it's sending you to, in your own language.
 *   - List what it can do if asked.
 *
 * Stays ON across page navigation (via localStorage) until the user
 * explicitly turns it off — toggle with a status light, not a one-shot tap.
 *
 * Include on every page with: <script src="/static/js/voice-agent.js"></script>
 */

(function(){

  const AGENT_STATE_KEY = 'prHarvestAgentOn';
  const HISTORY_KEY = 'prHarvestAgentHistory';

  function detectSpokenLang(){
    const saved = localStorage.getItem('preferredLang');
    if(saved === 'hi' || saved === 'mr') return saved;
    return 'en';
  }

  function isAgentOn(){
    return localStorage.getItem(AGENT_STATE_KEY) === 'true';
  }
  function setAgentOn(val){
    localStorage.setItem(AGENT_STATE_KEY, val ? 'true' : 'false');
  }

  function getProfile(){
    try{
      const raw = localStorage.getItem('prHarvestPatientProfile');
      return raw ? JSON.parse(raw) : null;
    }catch(e){ return null; }
  }

  function getHistory(){
    try{
      const raw = sessionStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    }catch(e){ return []; }
  }
  function pushHistory(userText, replyText){
    const h = getHistory();
    h.push({role:'user', content:userText});
    h.push({role:'assistant', content:replyText});
    sessionStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(-16)));
  }

  let userLat = null, userLng = null;
  if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(
      pos => { userLat = pos.coords.latitude; userLng = pos.coords.longitude; },
      () => {},
      {timeout: 6000}
    );
  }

  function injectStyles(){
    const style = document.createElement('style');
    style.textContent = `
      .va-toggle-wrap{position:fixed;right:25px;bottom:200px;z-index:99997;display:flex;align-items:center;gap:8px;}
      .va-fab{
        width:58px;height:58px;border-radius:50%;background:#eef4f6;color:#5c7580;
        display:flex;align-items:center;justify-content:center;cursor:pointer;
        border:3px solid #dbe6ea;box-shadow:0 6px 20px rgba(8,34,46,0.2);
        font-size:22px;font-family:'Inter',sans-serif;transition:all .2s;position:relative;
      }
      .va-fab.on{background:#08222e;border-color:#4ac9e2;color:#4ac9e2;}
      .va-fab.listening{animation:vaListenPulse 1s infinite;}
      .va-fab.thinking{animation:vaThinkPulse .6s infinite;}
      @keyframes vaListenPulse{
        0%,100%{box-shadow:0 6px 20px rgba(74,201,226,0.3),0 0 0 0 rgba(74,201,226,0.5);}
        50%{box-shadow:0 6px 20px rgba(74,201,226,0.3),0 0 0 14px rgba(74,201,226,0);}
      }
      @keyframes vaThinkPulse{0%,100%{transform:scale(1);}50%{transform:scale(1.1);}}
      .va-status-light{position:absolute;top:-2px;right:-2px;width:16px;height:16px;border-radius:50%;background:#8fa3ab;border:2.5px solid #fff;}
      .va-status-light.on{background:#3ce27a;animation:vaLightBlink 1.5s infinite;}
      @keyframes vaLightBlink{0%,100%{opacity:1;}50%{opacity:.4;}}
      .va-bubble{background:#fff;border-radius:12px;padding:8px 14px;box-shadow:0 4px 14px rgba(8,34,46,0.15);font-family:'Inter',sans-serif;font-size:11.5px;font-weight:700;color:#0e2430;display:none;white-space:nowrap;}
      .va-bubble.show{display:block;}
      .va-transcript-toast{
        position:fixed;left:50%;bottom:110px;transform:translateX(-50%);z-index:99998;
        background:#08222e;color:#fff;padding:12px 20px;border-radius:20px;font-family:'Inter',sans-serif;
        font-size:12.5px;font-weight:600;max-width:85%;text-align:center;display:none;
        box-shadow:0 6px 20px rgba(0,0,0,0.3);line-height:1.5;
      }
      .va-transcript-toast.show{display:block;}
      .va-transcript-toast .va-label{display:block;font-size:9.5px;color:#4ac9e2;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px;font-weight:800;}
    `;
    document.head.appendChild(style);
  }

  let recognition = null;
  let shouldBeListening = false;
  let processing = false; // true while waiting for backend response — pause recognition restart
  let fabEl, lightEl, bubbleEl, toastEl;

  function initRecognition(){
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(!SpeechRecognition) return null;
    const lang = detectSpokenLang();
    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = lang === 'hi' ? 'hi-IN' : (lang === 'mr' ? 'mr-IN' : 'en-IN');
    return rec;
  }

  function speak(text, onEnd){
    if(!window.speechSynthesis){ if(onEnd) onEnd(); return; }
    const lang = detectSpokenLang();
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang === 'hi' ? 'hi-IN' : (lang === 'mr' ? 'mr-IN' : 'en-IN');
    u.rate = 0.95;
    if(onEnd) u.onend = onEnd;
    window.speechSynthesis.speak(u);
  }

  function showToast(label, text){
    toastEl.innerHTML = `<span class="va-label">${label}</span>${text}`;
    toastEl.classList.add('show');
  }
  function hideToast(){
    toastEl.classList.remove('show');
  }

  const LOCAL_OFF_PHRASES = ['turn off','stop listening','band karo','बंद करो','थांबा','बंद कर'];

  async function handleFinalTranscript(text){
    const lower = text.toLowerCase();
    if(LOCAL_OFF_PHRASES.some(p => lower.includes(p))){
      const lang = detectSpokenLang();
      speak(({en:"Turning off.",hi:"बंद कर रहा हूं।",mr:"बंद करत आहे."})[lang]);
      turnOff();
      return;
    }

    processing = true;
    fabEl.classList.remove('listening');
    fabEl.classList.add('thinking');
    showToast('You said', text);

    try{
      const res = await fetch('/api/agent', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          message: text,
          history: getHistory(),
          profile: getProfile(),
          lat: userLat,
          lng: userLng,
        })
      });
      const data = await res.json();
      fabEl.classList.remove('thinking');

      if(data.error){
        speak(data.error);
        hideToast();
        processing = false;
        return;
      }

      showToast('Agent', data.reply);
      pushHistory(text, data.reply);

      speak(data.reply, () => {
        hideToast();
        processing = false;
        if(data.route){
          setAgentOn(true); // persist across navigation
          window.location.href = data.route;
        } else if(shouldBeListening){
          // stay listening for the next command
        }
      });
    }catch(e){
      fabEl.classList.remove('thinking');
      hideToast();
      processing = false;
    }
  }

  function startRecognitionLoop(){
    if(!recognition) recognition = initRecognition();
    if(!recognition){
      alert('Voice commands need Chrome or Edge browser.');
      turnOff();
      return;
    }

    let finalBuffer = '';
    let silenceTimer = null;

    recognition.onresult = (event) => {
      let interim = '';
      for(let i = event.resultIndex; i < event.results.length; i++){
        const transcript = event.results[i][0].transcript;
        if(event.results[i].isFinal){
          finalBuffer += transcript + ' ';
        } else {
          interim += transcript;
        }
      }
      if(interim) showToast('Listening', interim);

      // Debounce: wait briefly after the last final chunk in case the user keeps talking,
      // then treat the buffered text as one complete command.
      if(finalBuffer.trim()){
        if(silenceTimer) clearTimeout(silenceTimer);
        silenceTimer = setTimeout(() => {
          const command = finalBuffer.trim();
          finalBuffer = '';
          if(command && !processing){
            handleFinalTranscript(command);
          }
        }, 900);
      }
    };

    recognition.onend = () => {
      if(shouldBeListening && !processing){
        try{ recognition.start(); }catch(e){}
      } else if(!shouldBeListening){
        fabEl.classList.remove('listening');
      }
    };

    recognition.onerror = (e) => {
      if(shouldBeListening && e.error !== 'aborted' && !processing){
        try{ recognition.start(); }catch(err){}
      }
    };

    try{ recognition.start(); }catch(e){}
    fabEl.classList.add('listening');
  }

  function turnOn(speakGreeting){
    shouldBeListening = true;
    setAgentOn(true);
    fabEl.classList.add('on');
    lightEl.classList.add('on');
    bubbleEl.textContent = 'Listening…';
    bubbleEl.classList.add('show');
    setTimeout(() => bubbleEl.classList.remove('show'), 2200);

    if(speakGreeting){
      const lang = detectSpokenLang();
      const msg = ({
        en: "Voice agent on. Ask me anything — like 'I need a hospital bed' or 'what can you do'.",
        hi: "वॉइस एजेंट चालू है। कुछ भी पूछें — जैसे 'मुझे अस्पताल में बेड चाहिए' या 'आप क्या कर सकते हैं'।",
        mr: "व्हॉइस एजंट सुरू आहे. काहीही विचारा — जसे 'मला रुग्णालयात बेड हवा आहे' किंवा 'तुम्ही काय करू शकता'."
      })[lang];
      speak(msg, () => startRecognitionLoop());
    } else {
      startRecognitionLoop();
    }
  }

  function turnOff(){
    shouldBeListening = false;
    processing = false;
    setAgentOn(false);
    fabEl.classList.remove('on','listening','thinking');
    lightEl.classList.remove('on');
    hideToast();
    if(recognition){ try{ recognition.stop(); }catch(e){} }
  }

  function toggle(){
    if(isAgentOn() && shouldBeListening){
      turnOff();
    } else {
      turnOn(true);
    }
  }

  function buildDOM(){
    const wrap = document.createElement('div');
    wrap.className = 'va-toggle-wrap';

    const bubble = document.createElement('div');
    bubble.className = 'va-bubble';

    const fab = document.createElement('div');
    fab.className = 'va-fab';
    fab.innerHTML = '🎙️<div class="va-status-light" id="vaStatusLight"></div>';
    fab.title = 'Tap to turn voice agent on/off';

    wrap.appendChild(bubble);
    wrap.appendChild(fab);
    document.body.appendChild(wrap);

    const toast = document.createElement('div');
    toast.className = 'va-transcript-toast';
    document.body.appendChild(toast);

    fabEl = fab;
    lightEl = document.getElementById('vaStatusLight');
    bubbleEl = bubble;
    toastEl = toast;

    fab.addEventListener('click', toggle);
  }

  function init(){
    injectStyles();
    buildDOM();
    if(isAgentOn()){
      turnOn(false); // resume silently on page navigation, no repeated greeting
    }
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();