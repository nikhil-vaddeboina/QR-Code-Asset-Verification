(() => {
  const resultBox = document.getElementById('scanResult');
  const status = document.getElementById('cameraStatus');
  const start = document.getElementById('startScan');
  const stop = document.getElementById('stopScan');
  let scanner;
  const showError = message => { resultBox.hidden=false; resultBox.innerHTML=`<div class="scan-error"><i class="bi bi-exclamation-circle"></i><div><b>Could not find that asset</b><p>${message}</p></div></div>`; };
  async function lookup(raw) {
    let id = raw.trim();
    try { const parsed = new URL(id); const match=parsed.pathname.match(/\/lookup\/(AST-[\w-]+)/i) || parsed.pathname.match(/\/assets\/(AST-[\w-]+)/i); if(match) id=match[1]; } catch (_) {}
    id = id.toUpperCase().match(/AST-[A-Z0-9-]+/)?.[0] || id.toUpperCase();
    if (!/^AST-[A-Z0-9-]+$/.test(id)) return showError('This QR code is not a recognized AssetFlow label.');
    try {
      const response=await fetch(`/lookup/${encodeURIComponent(id)}`);
      const asset=await response.json();
      if(!response.ok) return showError(asset.error || 'No asset matches this ID.');
      resultBox.hidden=false;
      resultBox.innerHTML=`<div class="scan-found"><div class="scan-found-top"><span class="success-icon small-success"><i class="bi bi-check-lg"></i></span><div><small>ASSET FOUND</small><h3>${escapeHtml(asset.name)}</h3><span class="mono">${escapeHtml(asset.asset_id)} · ${escapeHtml(asset.serial_number)}</span></div><span class="status-pill ${asset.status.toLowerCase().replaceAll(' ','-')}">${escapeHtml(asset.status)}</span></div><div class="scan-meta"><span><small>LOCATION</small><b>${escapeHtml(asset.location)}</b></span><span><small>DEPARTMENT</small><b>${escapeHtml(asset.department)}</b></span><span><small>ASSIGNED TO</small><b>${escapeHtml(asset.assigned_to)}</b></span></div><a class="button primary" href="${asset.url}"><i class="bi bi-check2-circle"></i> Continue to verification</a></div>`;
      resultBox.scrollIntoView({behavior:'smooth',block:'center'});
    } catch (_) { showError('Unable to reach the server. Check your connection and try again.'); }
  }
  function escapeHtml(s){const el=document.createElement('span');el.textContent=s;return el.innerHTML;}
  document.getElementById('manualLookup').addEventListener('submit',e=>{e.preventDefault();lookup(document.getElementById('assetIdInput').value);});
  start.addEventListener('click', async()=>{
    if(!window.Html5Qrcode){status.innerHTML='<i></i> SCANNER UNAVAILABLE';showError('The QR scanning library did not load. Check your internet connection.');return;}
    scanner ||= new Html5Qrcode('reader');
    status.innerHTML='<i></i> REQUESTING CAMERA'; start.disabled=true;
    try { await scanner.start({facingMode:'environment'},{fps:10,qrbox:{width:230,height:230}}, text=>{scanner.stop().catch(()=>{});start.disabled=false;stop.disabled=true;status.innerHTML='<i></i> QR CODE FOUND';lookup(text);},()=>{}); start.disabled=true;stop.disabled=false;status.innerHTML='<i></i> SCANNING'; }
    catch (_) {start.disabled=false;status.innerHTML='<i></i> CAMERA UNAVAILABLE';showError('Allow camera access in your browser, or use the asset ID field below.');}
  });
  stop.addEventListener('click',async()=>{if(scanner?.isScanning){await scanner.stop();stop.disabled=true;start.disabled=false;status.innerHTML='<i></i> CAMERA READY';}});
})();
