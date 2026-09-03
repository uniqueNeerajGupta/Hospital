/**
 * PR Harvest — One-Tap SOS Widget
 *
 * Goal: during a real emergency, the user should have to do almost nothing.
 * - First time ever: user saves one emergency contact number (10 seconds, once).
 * - Every time after that: ONE tap on the floating SOS button auto-fetches
 *   live location and opens WhatsApp with it pre-filled — no forms, no typing.
 * - A 3-second cancel window prevents accidental triggers from a stray tap,
 *   but does NOT require any extra action to actually send.
 *
 * Include on any page with: <script src="/static/js/sos-widget.js"></script>
 */

(function(){
  const SOS_CONTACT_KEY = 'sosEmergencyContact';
  const HOTLINE = '+919987003075';

  function injectStyles(){
    const style = document.createElement('style');
    style.textContent = `
      .sos-fab{
        position:fixed;left:20px;bottom:25px;z-index:99998;
        width:64px;height:64px;border-radius:50%;background:#e23c3c;color:#fff;
        display:flex;align-items:center;justify-content:center;flex-direction:column;
        border:3px solid #fff;box-shadow:0 6px 20px rgba(226,60,60,0.5);cursor:pointer;
        font-family:'Inter',sans-serif;animation:sosPulse 2s infinite;user-select:none;
      }
      .sos-fab-label{font-size:11px;font-weight:900;letter-spacing:.5px;line-height:1;margin-top:1px;}
      @keyframes sosPulse{
        0%,100%{box-shadow:0 6px 20px rgba(226,60,60,0.5),0 0 0 0 rgba(226,60,60,0.5);}
        50%{box-shadow:0 6px 20px rgba(226,60,60,0.5),0 0 0 10px rgba(226,60,60,0);}
      }
      .sos-overlay{
        position:fixed;inset:0;background:rgba(8,20,28,0.7);backdrop-filter:blur(2px);
        z-index:99999;display:none;align-items:center;justify-content:center;padding:20px;
      }
      .sos-overlay.open{display:flex;}
      .sos-modal{
        background:#fff;border-radius:20px;padding:26px 22px;max-width:360px;width:100%;
        text-align:center;font-family:'Inter',sans-serif;
      }
      .sos-modal h3{font-family:'Manrope',sans-serif;font-size:18px;font-weight:800;color:#0e2430;margin-bottom:8px;}
      .sos-modal p{font-size:13px;color:#5c7580;line-height:1.6;margin-bottom:16px;}
      .sos-input{
        width:100%;padding:13px;border:1.5px solid #dbe6ea;border-radius:10px;font-size:14px;
        text-align:center;margin-bottom:12px;outline:none;
      }
      .sos-input:focus{border-color:#4ac9e2;}
      .sos-save-btn{width:100%;background:#08222e;color:#fff;border:none;padding:13px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;}

      .sos-countdown-ring{
        width:110px;height:110px;border-radius:50%;margin:0 auto 16px;position:relative;
        display:flex;align-items:center;justify-content:center;
        background:conic-gradient(#e23c3c var(--pct,0%), #f0dcae 0%);
      }
      .sos-countdown-inner{
        width:92px;height:92px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;
        font-family:'Manrope',sans-serif;font-size:34px;font-weight:800;color:#e23c3c;
      }
      .sos-cancel-btn{width:100%;background:#eef4f6;color:#3d5b66;border:none;padding:13px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;margin-top:6px;}

      .sos-sent-icon{width:64px;height:64px;border-radius:50%;background:#eafaf0;color:#1e8449;display:flex;align-items:center;justify-content:center;font-size:30px;margin:0 auto 14px;}
      .sos-action-row{display:flex;gap:8px;margin-top:14px;}
      .sos-action-btn{flex:1;padding:13px;border-radius:10px;font-size:13.5px;font-weight:800;text-decoration:none;display:block;}
      .sos-action-btn.call{background:#e23c3c;color:#fff;}
      .sos-action-btn.wa{background:#25D366;color:#fff;}
      .sos-edit-link{display:block;margin-top:14px;font-size:11.5px;color:#8fa3ab;font-weight:600;cursor:pointer;}
    `;
    document.head.appendChild(style);
  }

  function getContact(){
    return localStorage.getItem(SOS_CONTACT_KEY) || '';
  }
  function saveContact(num){
    localStorage.setItem(SOS_CONTACT_KEY, num);
  }

  function buildDOM(){
    const fab = document.createElement('div');
    fab.className = 'sos-fab';
    fab.innerHTML = `<div style="font-size:20px;">🆘</div><div class="sos-fab-label">SOS</div>`;

    const overlay = document.createElement('div');
    overlay.className = 'sos-overlay';
    overlay.innerHTML = `<div class="sos-modal" id="sosModalContent"></div>`;

    document.body.appendChild(fab);
    document.body.appendChild(overlay);

    fab.addEventListener('click', onSosTap);
    overlay.addEventListener('click', (e) => { if(e.target === overlay) closeSos(); });

    return {fab, overlay};
  }

  let overlayEl, modalEl;
  let countdownTimer = null;
  let cancelled = false;

  function openOverlay(){ overlayEl.classList.add('open'); }
  function closeSos(){
    overlayEl.classList.remove('open');
    if(countdownTimer) clearInterval(countdownTimer);
  }

  function onSosTap(){
    const contact = getContact();
    if(!contact){
      showSetupPanel();
    } else {
      showCountdownPanel(contact);
    }
    openOverlay();
  }

  function showSetupPanel(){
    modalEl.innerHTML = `
      <h3>🆘 One-Time SOS Setup</h3>
      <p>Save one family member's number now. After this, sending an SOS will only take <b>one tap</b> — no typing, ever again.</p>
      <input type="tel" class="sos-input" id="sosContactInput" placeholder="Family member's number" maxlength="10">
      <button class="sos-save-btn" id="sosSaveBtn">Save & Continue</button>
      <div class="sos-edit-link" id="sosCancelSetup">Cancel</div>
    `;
    document.getElementById('sosSaveBtn').addEventListener('click', () => {
      const val = document.getElementById('sosContactInput').value.trim();
      if(val.length < 10){ alert('Please enter a valid 10-digit number.'); return; }
      saveContact(val);
      showCountdownPanel(val);
    });
    document.getElementById('sosCancelSetup').addEventListener('click', closeSos);
  }

  function showCountdownPanel(contact){
    cancelled = false;
    let secondsLeft = 3;

    modalEl.innerHTML = `
      <h3>Sending SOS in…</h3>
      <p>Tap Cancel if this was accidental.</p>
      <div class="sos-countdown-ring" id="sosRing" style="--pct:0%;">
        <div class="sos-countdown-inner" id="sosCountNum">${secondsLeft}</div>
      </div>
      <button class="sos-cancel-btn" id="sosCancelBtn">Cancel</button>
    `;
    document.getElementById('sosCancelBtn').addEventListener('click', () => {
      cancelled = true;
      closeSos();
    });

    // Start fetching location immediately in the background — don't wait for the countdown
    let locationPromise = new Promise((resolve) => {
      if(!navigator.geolocation){ resolve(null); return; }
      navigator.geolocation.getCurrentPosition(
        pos => resolve(`https://maps.google.com/?q=${pos.coords.latitude},${pos.coords.longitude}`),
        () => resolve(null),
        {timeout: 6000}
      );
    });

    const ring = document.getElementById('sosRing');
    const numEl = document.getElementById('sosCountNum');

    countdownTimer = setInterval(() => {
      secondsLeft--;
      if(numEl) numEl.textContent = secondsLeft > 0 ? secondsLeft : '0';
      if(ring) ring.style.setProperty('--pct', `${((3-secondsLeft)/3)*100}%`);

      if(secondsLeft <= 0){
        clearInterval(countdownTimer);
        if(!cancelled){
          locationPromise.then(mapsLink => sendSos(contact, mapsLink));
        }
      }
    }, 1000);
  }

  function sendSos(contact, mapsLink){
    const locationText = mapsLink ? `📍 My live location: ${mapsLink}` : '📍 Location unavailable — please call me directly.';
    const message = `🆘 SOS — I NEED HELP\n\n${locationText}\n\nSent automatically via PR Harvest.`;
    const encoded = encodeURIComponent(message);
    const waUrl = `https://wa.me/91${contact}?text=${encoded}`;

    // Auto-open WhatsApp right away — this is the core "do it for me" action
    window.open(waUrl, '_blank');

    modalEl.innerHTML = `
      <div class="sos-sent-icon">✓</div>
      <h3>SOS Sent</h3>
      <p>Your location was sent to your emergency contact on WhatsApp. You can also call for immediate help.</p>
      <div class="sos-action-row">
        <a href="tel:${HOTLINE}" class="sos-action-btn call">📞 Call Now</a>
        <a href="${waUrl}" target="_blank" class="sos-action-btn wa">💬 Reopen WhatsApp</a>
      </div>
      <div class="sos-edit-link" id="sosCloseBtn">Close</div>
    `;
    document.getElementById('sosCloseBtn').addEventListener('click', closeSos);
  }

  function init(){
    injectStyles();
    const {overlay} = buildDOM();
    overlayEl = overlay;
    modalEl = document.getElementById('sosModalContent');
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();