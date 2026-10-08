let token=localStorage.getItem('aisys_token');
let currentUser=null;
let currentRole=null;
let refreshTimer=null;
const $=id=>document.getElementById(id);
const jsonHeaders={'Content-Type':'application/json'};

async function api(path,opt={}){
  try{
    opt.headers={...(opt.headers||{}),...(token?{Authorization:`Bearer ${token}`}:{})};
    const r=await fetch(path,opt);
    let d={};try{d=await r.json()}catch{}
    if(r.status===401){token=null;localStorage.removeItem('aisys_token');showAuthView();throw Error('Your session has expired. Please sign in again.')}
    if(!r.ok)throw Error(d.detail||d.message||`Request failed (${r.status})`);
    return d;
  }catch(e){
    if(e instanceof TypeError)throw Error('The server could not be reached. Please make sure AISYS is running.');
    throw e;
  }
}
function toast(msg,type=''){const t=$('toast');if(!t)return;t.textContent=msg;t.className=`toast ${type||''}`.trim();t.hidden=false;clearTimeout(window.__aisysToastTimer);window.__aisysToastTimer=setTimeout(()=>t.hidden=true,3200)}
function friendlyError(e,context='Operation'){console.error(context,e);const msg=String(e?.message||e||'').trim();if(/join is not a function|cannot read properties|undefined|is not a function|syntaxerror/i.test(msg))return `${context} could not be completed. Please refresh the current screen and try again.`;return msg||`${context} could not be completed.`}
function showAuthView(){$('authView').hidden=false;$('authView').style.display='flex';$('appShell').hidden=true;$('appShell').style.display='none';$('u')?.focus()}
function setBusy(button,busy,label){if(!button)return;if(busy){button.dataset.originalText=button.textContent;button.disabled=true;button.setAttribute('aria-busy','true');button.textContent=label||'Working…'}else{button.disabled=false;button.removeAttribute('aria-busy');if(button.dataset.originalText)button.textContent=button.dataset.originalText}}
async function login(button){const submit=button||document.querySelector('#loginForm button[type="submit"]');const username=$('u')?.value.trim();const password=$('p')?.value||'';if(!username||!password){if($('loginStatus')){$('loginStatus').className='login-status error';$('loginStatus').textContent='Enter your username and password.'}toast('Enter your username and password.','error');return false}
  if($('loginStatus')){$('loginStatus').className='login-status';$('loginStatus').textContent='Signing in…'}setBusy(submit,true,'Signing in…');try{const fd=new URLSearchParams();fd.set('username',username);fd.set('password',password);const d=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:fd});let j={};try{j=await d.json()}catch{}if(!d.ok)throw Error(j.detail||'Invalid username or password.');token=j.access_token;localStorage.setItem('aisys_token',token);if($('loginStatus')){$('loginStatus').className='login-status good';$('loginStatus').textContent='Signed in successfully.'}await showApp();return true}catch(e){if($('loginStatus')){$('loginStatus').className='login-status error';$('loginStatus').textContent=friendlyError(e,'Sign in')}toast(friendlyError(e,'Sign in'),'error');return false}finally{setBusy(submit,false)}}
function logout(){if(refreshTimer)clearInterval(refreshTimer);token=null;currentUser=null;currentRole=null;localStorage.removeItem('aisys_token');showAuthView();$('u').value='';$('p').value='';toast('You have been signed out.')}
const ROLE_SECTIONS={admin:['dashboard','catalog','circulation','members','acquisitions','tagging','inventory','security','migration','reports','admin','opac'],librarian:['dashboard','catalog','circulation','members','acquisitions','tagging','inventory','security','reports','opac'],operator:['dashboard','catalog','circulation','inventory','security','opac']};
function applyRoleExperience(){
 const labels={admin:{title:'Administration overview',kicker:'SYSTEM OVERSIGHT',description:'Monitor collection, staff access, migrations, security and system health.'},librarian:{title:'Librarian workspace',kicker:'LIBRARY SERVICES',description:'Manage catalogue records, patrons, circulation, RFID tagging and stock verification.'},operator:{title:'Operations workspace',kicker:'FRONT-DESK OPERATIONS',description:'Process permitted loans and returns, run inventory scans and review security events.'}};
 const copy=labels[currentRole]||labels.operator;
 if($('dashboardHeading'))$('dashboardHeading').textContent=copy.title;
 if($('dashboardKicker'))$('dashboardKicker').textContent=copy.kicker;
 if($('dashboardDescription'))$('dashboardDescription').textContent=copy.description;
 document.querySelectorAll('[data-roles]').forEach(el=>{const allowed=(el.dataset.roles||'').split(',').map(x=>x.trim());el.hidden=!allowed.includes(currentRole)});
 document.querySelectorAll('.nav[data-section]').forEach(el=>{const allowed=(el.dataset.roles||'admin,librarian,operator').split(',').map(x=>x.trim());el.hidden=!allowed.includes(currentRole)});
 const subtitle=document.querySelector('.library-name small');
 if(subtitle)subtitle.textContent=({admin:'Administration Console',librarian:'Librarian Workspace',operator:'Circulation & Inventory'})[currentRole]||'Library Workspace';
}
async function showApp(){
 try{
  const m=await api('/api/me');currentUser=m.username;currentRole=m.role;
  $('authView').hidden=true;$('authView').style.display='none';$('appShell').hidden=false;$('appShell').style.display='flex';
  $('me').textContent=m.username;$('rolePill').textContent=m.role.toUpperCase();applyRoleExperience();
  await refreshAll();showSection('dashboard');startClock();
 }catch(e){console.error('Authentication/session check failed:',e);token=null;localStorage.removeItem('aisys_token');showAuthView();toast(friendlyError(e,'Session check'),'error')}
}
function showSection(id){
 const allowed=ROLE_SECTIONS[currentRole]||ROLE_SECTIONS.operator;
 if(!allowed.includes(id)){toast('This workspace is not available for your role.','error');return}
 document.querySelectorAll('.section').forEach(x=>x.classList.remove('active'));
 document.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));
 const section=$(id);if(!section)return;section.classList.add('active');
 document.querySelector('.nav[data-section="'+id+'"]')?.classList.add('active');
 $('pageTitle').textContent=document.querySelector('.nav[data-section="'+id+'"] span')?.textContent||id;
 const loaders={dashboard:loadDashboard,catalog:loadCatalog,circulation:loadCirculation,members:loadMembers,acquisitions:loadAcquisitions,tagging:loadTags,inventory:loadInventory,security:loadSecurity,migration:loadMigrations,reports:loadReports,admin:loadAdmin,opac:loadOpac};
 const loader=loaders[id];if(loader)loader().then(markRefreshed).catch(e=>toast(friendlyError(e,id+' refresh'),'error'));
}
document.addEventListener('click',e=>{const n=e.target.closest('.nav');if(n){e.preventDefault();showSection(n.dataset.section)}});
function openModal(id){$(id).hidden=false;$(id).querySelector('input,select,textarea')?.focus()}
function closeModal(id){$(id).hidden=true}
function startClock(){if(refreshTimer)clearInterval(refreshTimer);const tick=()=>{$('clock').textContent=new Date().toLocaleString([], {dateStyle:'medium',timeStyle:'short'})};tick();refreshTimer=setInterval(()=>{tick();if(token){loadDashboard().then(markRefreshed).catch(()=>{});if($('security')?.classList.contains('active'))loadSecurity().then(markRefreshed).catch(()=>{})}},5000)}
function markRefreshed(){const el=$('lastRefresh');if(el)el.textContent='Last updated '+new Date().toLocaleString([], {dateStyle:'medium',timeStyle:'short'})}
async function refreshAll(){await Promise.allSettled([loadDashboard(),loadCatalog(),loadMembers(),loadTags(),loadSecurity(),loadMigrations()]);markRefreshed()}
async function refreshAfterMutation(...loaders){await Promise.allSettled([loadDashboard(),...loaders.filter(Boolean).map(fn=>Promise.resolve().then(fn))]);markRefreshed()}
function row(title,sub,meta='',status=''){return `<div class="row-item"><div><strong>${esc(title)}</strong><small>${esc(sub)}</small></div><div class="meta">${status?`<span class="status ${status==='SUCCESS'||status==='FOUND'||status==='AUTHORIZED'?'ok':status==='MISPLACED'||status==='QUEUED'?'warn':'bad'}">${esc(status)}</span><br>`:''}${esc(meta)}</div></div>`}
function table(headers,rows){const hs=Array.isArray(headers)?headers:[];const rs=Array.isArray(rows)?rows:[];return `<table class="table"><thead><tr>${hs.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rs.length?rs.join(''):`<tr><td colspan="${Math.max(hs.length,1)}">No records found.</td></tr>`}</tbody></table>`}
function list(v){return Array.isArray(v)?v:[]}
function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}function dt(v){return v?new Date(v).toLocaleString([], {dateStyle:'medium',timeStyle:'short'}):'—'}

async function loadDashboard(){const [d,c0,r0,g0,h,n0]=await Promise.all([api('/api/dashboard'),api('/api/reports/circulation'),api('/api/rfid/events'),api('/api/gate/events'),api('/api/health'),api('/api/notifications')]);const c=list(c0),r=list(r0),g=list(g0),n=list(n0);$('metrics').innerHTML=[['Catalogued items',d.books],['Members',d.members],['Available',d.available],['Active loans',d.issued],['RFID tags',d.rfid_tags],['Gate events',d.gate_events],['Notifications',d.notifications],['Audit events',d.audit_events]].map(x=>`<div class="metric"><small>${x[0]}</small><b>${x[1]}</b></div>`).join('');$('dashCirculation').innerHTML=c.slice(0,6).map(x=>row(`Book #${x.book_id}`,`Member #${x.member_id} · ${x.protocol}`,dt(x.checkout_at),x.status)).join('')||row('No transactions','Circulation desk is clear');$('dashRfid').innerHTML=r.slice(0,6).map(x=>row(x.tag_id,`${x.accession_no||'Unknown'} · shelf ${x.shelf||'—'}`,dt(x.created_at),x.event_type)).join('')||row('No RFID activity','No recent reads');$('dashSecurity').innerHTML=g.slice(0,4).map(x=>row(x.accession_no,`Tag ${x.tag_id} · ${x.cctv_image_ref}`,dt(x.created_at),x.authorized?'AUTHORIZED':'UNAUTHORIZED')).join('')||row('No gate exceptions','Notification queue is clear');$('healthBox').innerHTML=`<div class="health-line"><span>Application</span><b class="status ok">${esc(h.status)}</b></div><div class="health-line"><span>Database</span><b class="status ok">${esc(h.database)}</b></div><div class="health-line"><span>Version</span><b>${esc(h.version)}</b></div><div class="health-line"><span>Mode</span><b>${esc(h.environment)}</b></div>`}
async function loadCatalog(button=null){
  setBusy(button,true,'Searching…');
  const headers=['Accession','Title','Author','Category','ISBN','Availability','RFID'];
  try{
    const q=($('bookSearch')?.value||'').trim();
    const results=await Promise.all([api('/api/books?q='+encodeURIComponent(q)),api('/api/rfid/tags')]);
    const books=Array.isArray(results[0])?results[0]:[];
    const tags=Array.isArray(results[1])?results[1]:[];
    const tagsByAccession=new Map(tags.filter(t=>t.active).map(t=>[t.accession_no,t.tag_id]));
    $('bookCount').textContent=String(books.length);
    if(!books.length){
      $('catalogTable').innerHTML='<div class="empty-detail"><b>No matching catalogue records</b><p>Try a title, author, accession number, ISBN or category. Clear the search to view all records.</p></div>';
      markRefreshed();
      return;
    }
    $('catalogTable').innerHTML=table(headers,books.map(b=>{
      const tag=tagsByAccession.get(b.accession_no);
      return '<tr>'+
        '<td><button type="button" class="link" onclick="showBook(\''+esc(b.accession_no)+'\')">'+esc(b.accession_no)+'</button></td>'+
        '<td><b>'+esc(b.title)+'</b>'+(b.reference_only?' <span class="status warn">REFERENCE</span>':'')+'</td>'+
        '<td>'+esc(b.author||'—')+'</td>'+
        '<td>'+esc(b.category||'General')+'</td>'+
        '<td>'+esc(b.isbn||'—')+'</td>'+
        '<td><span class="status '+(b.available?'ok':'bad')+'">'+(b.available?'AVAILABLE':'ISSUED')+'</span></td>'+
        '<td>'+(tag?esc(tag):'<span class="status warn">NOT TAGGED</span>')+'</td>'+
      '</tr>';
    }).join(''));
    markRefreshed();
  }catch(e){
    console.error('Catalogue search failed:',e);
    $('bookCount').textContent='—';
    $('catalogTable').innerHTML='<div class="empty-detail"><b>Catalogue could not be loaded</b><p>Check the server connection and try again. The error is shown in the notification.</p></div>';
    toast(friendlyError(e,'Catalogue search'),'error');
  }finally{
    setBusy(button,false);
  }
}
function resetCatalogSearch(){const input=$('bookSearch');if(input)input.value='';loadCatalog()}
async function showBook(acc){
  try{
    const d=await api('/api/books/'+encodeURIComponent(acc));
    const b=d.book;
    $('bookDetail').innerHTML='<div class="kicker">BIBLIOGRAPHIC ITEM RECORD</div><h3>'+esc(b.title)+'</h3>'+
      '<div class="health-box">'+
      '<div class="health-line"><span>Accession number</span><b>'+esc(b.accession_no)+'</b></div>'+
      '<div class="health-line"><span>ISBN / test identifier</span><b>'+esc(b.isbn||'—')+'</b></div>'+
      '<div class="health-line"><span>Author</span><b>'+esc(b.author||'—')+'</b></div>'+
      '<div class="health-line"><span>Category</span><b>'+esc(b.category||'General')+'</b></div>'+
      '<div class="health-line"><span>Availability</span><b class="status '+(b.available?'ok':'bad')+'">'+(b.available?'AVAILABLE':'ISSUED')+'</b></div>'+
      '<div class="health-line"><span>Collection type</span><b>'+(b.reference_only?'REFERENCE ONLY':'CIRCULATING')+'</b></div></div>'+
      '<h4>RFID relationship</h4><p>'+(d.rfid?esc(d.rfid.tag_id)+' · last seen '+dt(d.rfid.last_seen_at):'No active RFID tag is associated with this item.')+'</p>'+
      '<h4>Active loan</h4><p>'+(d.active_loan?'Member #'+d.active_loan.member_id+' · due '+dt(d.active_loan.due_at)+' · '+esc(d.active_loan.protocol):'No active loan')+'</p>'+
      '<button class="btn outline" onclick="loadBookHistory(\''+esc(acc)+'\')">View circulation history</button> <button class="btn outline" onclick="printItemLabel(\''+esc(acc)+'\')">Print item label</button><div id="bookHistory"></div>';
  }catch(e){toast(friendlyError(e,'Open catalogue record'),'error')}
}
function printItemLabel(acc){api('/api/books/'+encodeURIComponent(acc)).then(d=>{const w=window.open('','_blank','width=520,height=420');w.document.write(`<html><head><title>Item Label</title><style>body{font-family:Arial;padding:35px}.label{border:1px solid #222;padding:25px;width:380px}.code{font:32px monospace;letter-spacing:3px;margin:20px 0}</style></head><body><div class="label"><b>AISYS CENTRAL LIBRARY</b><h2>${esc(d.book.title)}</h2><p>${esc(d.book.author)}</p><div class="code">*${esc(d.book.accession_no)}*</div><p>Accession: ${esc(d.book.accession_no)}</p></div><script>window.print()<\/script></body></html>`);w.document.close()})}
async function loadBookHistory(acc){const h=list(await api('/api/books/'+encodeURIComponent(acc)+'/history'));$('bookHistory').innerHTML='<hr>'+h.map(x=>row(x.status,`Member #${x.member_id} · ${x.protocol}`,dt(x.checkout_at))).join('')}
async function createBook(button){setBusy(button,true,'Creating…');try{await api('/api/books',{method:'POST',headers:jsonHeaders,body:JSON.stringify({accession_no:$('bookAccession').value.trim(),title:$('bookTitle').value.trim(),author:$('bookAuthor').value.trim(),category:$('bookCategory').value.trim(),isbn:$('bookIsbn').value.trim(),reference_only:$('bookReference').checked})});closeModal('bookModal');['bookAccession','bookTitle','bookAuthor','bookIsbn'].forEach(id=>$(id).value='');$('bookCategory').value='General';$('bookReference').checked=false;toast('Catalogue record created');await refreshAfterMutation(loadCatalog)}catch(e){toast(friendlyError(e,'Create catalogue record'),'error')}finally{setBusy(button,false)}}
let members=[];async function loadMembers(){members=list(await api('/api/members'));renderMembers();markRefreshed()}function renderMembers(){const q=($('memberSearch')?.value||'').toLowerCase();const rows=members.filter(m=>(m.member_no+' '+m.name).toLowerCase().includes(q));$('membersTable').innerHTML=table(['Member','Name','Status','Fine','Action'],rows.map(m=>`<tr><td><b>${esc(m.member_no)}</b></td><td>${esc(m.name)}<br><small>${esc(m.email)}</small></td><td><span class="status ${m.blocked?'bad':'ok'}">${m.blocked?'BLOCKED':'ACTIVE'}</span></td><td>₹${Number(m.fine_amount).toFixed(2)}</td><td><button class="link" onclick="toggleBlock('${esc(m.member_no)}',${!m.blocked})">${m.blocked?'Unblock':'Block'}</button> <button class="link" onclick="setFine('${esc(m.member_no)}',${m.fine_amount})">Fine</button></td></tr>`).join(''))}
async function createMember(button){setBusy(button,true,'Creating…');try{await api('/api/members',{method:'POST',headers:jsonHeaders,body:JSON.stringify({member_no:$('memberNo').value.trim(),name:$('memberName').value.trim(),email:$('memberEmail').value.trim()})});closeModal('memberModal');['memberNo','memberName','memberEmail'].forEach(id=>$(id).value='');toast('Member created');await refreshAfterMutation(loadMembers)}catch(e){toast(friendlyError(e,'Create member'),'error')}finally{setBusy(button,false)}}
async function toggleBlock(no,b){try{await api(`/api/members/${encodeURIComponent(no)}/block?blocked=${b}`,{method:'POST'});toast(b?'Member blocked':'Member unblocked');await refreshAfterMutation(loadMembers)}catch(e){toast(friendlyError(e,'Update member status'),'error')}}
async function setFine(no,current){const v=prompt('Fine amount (₹):',current);if(v===null)return;const amount=Number(v);if(!Number.isFinite(amount)||amount<0){toast('Enter a valid non-negative fine amount.','error');return}try{await api(`/api/members/${encodeURIComponent(no)}/fine?amount=${encodeURIComponent(amount)}`,{method:'POST'});toast('Fine updated');await refreshAfterMutation(loadMembers)}catch(e){toast(friendlyError(e,'Update fine'),'error')}}
async function checkoutItem(button){setBusy(button,true,'Issuing…');try{const d=await api('/api/circulation/checkout',{method:'POST',headers:jsonHeaders,body:JSON.stringify({member_no:$('coMember').value.trim(),accession_no:$('coBook').value.trim(),protocol:$('coProtocol').value,days:+$('coDays').value})});toast('Checkout completed · due '+dt(d.due_at));await refreshAfterMutation(loadCirculation)}catch(e){toast(friendlyError(e,'Checkout'),'error')}finally{setBusy(button,false)}}
async function renewItem(button){setBusy(button,true,'Renewing…');try{const d=await api('/api/circulation/renew',{method:'POST',headers:jsonHeaders,body:JSON.stringify({accession_no:$('rnBook').value.trim(),protocol:$('rnProtocol').value,days:+$('rnDays').value})});toast('Loan renewed · due '+dt(d.due_at));await refreshAfterMutation(loadCirculation)}catch(e){toast(friendlyError(e,'Renew loan'),'error')}finally{setBusy(button,false)}}
async function checkinItem(button){setBusy(button,true,'Returning…');try{await api('/api/circulation/checkin',{method:'POST',headers:jsonHeaders,body:JSON.stringify({accession_no:$('ciBook').value.trim(),protocol:$('ciProtocol').value,days:14})});toast('Item checked in');await refreshAfterMutation(loadCirculation)}catch(e){toast(friendlyError(e,'Check in'),'error')}finally{setBusy(button,false)}}
async function loadCirculation(){const c=list(await api('/api/circulation/history'));$('circulationTable').innerHTML=table(['ID','Book','Member','Status','Channel','Checkout','Due','Returned'],c.map(x=>`<tr><td>${x.id}</td><td>${x.book_id}</td><td>${x.member_id}</td><td><span class="status ${x.status==='RETURNED'?'ok':'warn'}">${x.status}</span></td><td>${esc(x.protocol)}</td><td>${dt(x.checkout_at)}</td><td>${dt(x.due_at)}</td><td>${dt(x.returned_at)}</td></tr>`).join(''))}
async function loadAcquisitions(){const [a0,s0]=await Promise.all([api('/api/acquisitions'),api('/api/serials')]);const a=list(a0),s=list(s0);$('acqTable').innerHTML=table(['Reference','Vendor','Status','Ordered'],a.map(x=>`<tr><td>${esc(x.accession_no)}</td><td>${esc(x.vendor)}</td><td>${esc(x.status)}</td><td>${dt(x.ordered_at)}</td></tr>`).join(''));$('serialTable').innerHTML=table(['Title','Volume','Issue','Date'],s.map(x=>`<tr><td>${esc(x.title)}</td><td>${esc(x.volume)}</td><td>${esc(x.issue_no)}</td><td>${esc(x.issue_date)}</td></tr>`).join(''))}
async function createAcquisition(button){setBusy(button,true,'Saving…');try{await api('/api/acquisitions',{method:'POST',headers:jsonHeaders,body:JSON.stringify({accession_no:$('acqAcc').value.trim(),vendor:$('acqVendor').value.trim(),status:$('acqStatus').value})});$('acqAcc').value='';$('acqVendor').value='';toast('Acquisition saved');await refreshAfterMutation(loadAcquisitions)}catch(e){toast(friendlyError(e,'Save acquisition'),'error')}finally{setBusy(button,false)}}
async function createSerial(button){setBusy(button,true,'Adding…');try{await api('/api/serials',{method:'POST',headers:jsonHeaders,body:JSON.stringify({title:$('serTitle').value.trim(),volume:$('serVol').value.trim(),issue_no:$('serIssue').value.trim(),issue_date:$('serDate').value.trim()})});['serTitle','serVol','serIssue','serDate'].forEach(id=>$(id).value='');toast('Serial issue added');await refreshAfterMutation(loadAcquisitions)}catch(e){toast(friendlyError(e,'Add serial issue'),'error')}finally{setBusy(button,false)}}
async function validateBookForTag(){try{const d=await api('/api/books/'+encodeURIComponent($('tagAcc').value));$('tagValidation').className='notice good';$('tagValidation').textContent=`Valid: ${d.book.title} · ${d.book.available?'available':'issued'} · ${d.rfid?'existing tag '+d.rfid.tag_id:'no active tag'}`}catch(e){$('tagValidation').className='notice bad';$('tagValidation').textContent=e.message}}
async function associateTag(button){
  setBusy(button,true,'Encoding…');
  try{
    const accession=$('tagAcc').value.trim();
    const tagId=$('tagUid').value.trim();
    if(!accession||!tagId)throw Error('Enter both an accession number and RFID tag UID.');
    const created=await api('/api/rfid/associate',{method:'POST',headers:jsonHeaders,body:JSON.stringify({accession_no:accession,tag_id:tagId})});
    $('tagUid').value='';
    $('tagValidation').className='notice good';
    $('tagValidation').textContent='Tag associated successfully: '+(created.tag_id||tagId)+' → '+(created.accession_no||accession);
    await loadTags({expectedTagId:created.tag_id||tagId});
    await loadCatalog();
    markRefreshed();
    toast('RFID tag encoded and associated');
  }catch(e){toast(friendlyError(e,'RFID association'),'error')}
  finally{setBusy(button,false)}
}
async function loadTags(options={}){
  const headers=['Tag UID','Accession','Active','Last seen'];
  try{
    const t=list(await api('/api/rfid/tags'));
    $('tagsTable').innerHTML=table(headers,t.map(x=>'<tr><td><b>'+esc(x.tag_id)+'</b></td><td>'+esc(x.accession_no||'—')+'</td><td><span class="status '+(x.active?'ok':'bad')+'">'+(x.active?'ACTIVE':'RETIRED')+'</span></td><td>'+dt(x.last_seen_at)+'</td></tr>').join(''));
    if(options.expectedTagId&&!t.some(x=>x.tag_id===options.expectedTagId)){
      toast('Tag was saved, but the refreshed tag list did not return it. Check the active database and deployment.','error');
    }
    return t;
  }catch(e){
    $('tagsTable').innerHTML='<div class="empty-detail"><b>Tagged items could not be loaded</b><p>'+esc(e.message||'Request failed')+'</p><button type="button" class="btn outline" onclick="loadTags()">Try again</button></div>';
    toast(friendlyError(e,'RFID tag list'),'error');
    throw e;
  }
}
async function inventoryScan(button){setBusy(button,true,'Scanning…');try{const expected=$('invExpected').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);const observed=$('invTags').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);if(!expected.length&&!observed.length)throw Error('Enter expected or observed tag UIDs');const d=await api('/api/rfid/inventory/session',{method:'POST',headers:jsonHeaders,body:JSON.stringify({shelf:$('invShelf').value.trim(),expected_tag_ids:expected,observed_tag_ids:observed})});$('inventorySummary').textContent=`Expected ${d.expected} · Found ${d.found} · Missing ${d.missing} · Unknown ${d.unknown}`;$('inventoryTable').innerHTML=table(['Tag','Accession','Shelf','Classification','Confirmation'],(d.items||[]).map(x=>`<tr><td>${esc(x.tag_id)}</td><td>${esc(x.accession_no)}</td><td>${esc(x.shelf)}</td><td><span class="status ${x.status==='FOUND'?'ok':x.status==='MISPLACED'?'warn':'bad'}">${esc(x.status)}</span></td><td>${esc(x.confirmation)}</td></tr>`));toast('Shelf verification completed');await refreshAfterMutation(loadInventory)}catch(e){toast(friendlyError(e,'Shelf verification'),'error')}finally{setBusy(button,false)}}async function loadInventory(){await loadTags()}
async function triggerGate(button){setBusy(button,true,'Evaluating…');try{const d=await api('/api/gate/event',{method:'POST',headers:jsonHeaders,body:JSON.stringify({tag_id:$('gateUid').value.trim(),security_bit:$('gateBit').checked,cctv_ref:$('gateCctv').value.trim(),lms_online:!$('gateOffline').checked,footfall_count:1})});toast(d.authorized?'Authorized passage recorded':'Unauthorized event queued',d.authorized?'':'error');await refreshAfterMutation(loadSecurity)}catch(e){toast(friendlyError(e,'Security gate'),'error')}finally{setBusy(button,false)}}async function loadSecurity(){const [g0,n0]=await Promise.all([api('/api/gate/events'),api('/api/notifications')]);const g=list(g0),n=list(n0);$('gateTable').innerHTML=table(['Time','Tag','Accession','Decision','CCTV','Notification'],g.map(x=>`<tr><td>${dt(x.created_at)}</td><td>${esc(x.tag_id)}</td><td>${esc(x.accession_no)}</td><td><span class="status ${x.authorized?'ok':'bad'}">${x.authorized?'AUTHORIZED':'ALARM'}</span></td><td>${esc(x.cctv_image_ref)}</td><td>${esc(x.notification_status)}</td></tr>`).join(''));$('notificationTable').innerHTML=table(['Channel','Recipient','Status','Message'],n.map(x=>`<tr><td>${esc(x.channel)}</td><td>${esc(x.recipient)}</td><td>${esc(x.status)}</td><td>${esc(x.message)}</td></tr>`).join(''))}
async function smartCardCheck(button){setBusy(button,true,'Validating…');try{const d=await api('/api/smart-card/login',{method:'POST',headers:jsonHeaders,body:JSON.stringify({card_id:$('cardUid').value.trim(),username:$('cardUser').value.trim()})});$('cardResult').className=d.authenticated?'notice good':'notice bad';$('cardResult').textContent=d.authenticated?`Card accepted · ${d.username} · method ${d.method||'smartcard'}`:'Card rejected';toast(d.authenticated?'Smart card accepted':'Smart card rejected',d.authenticated?'':'error');await refreshAfterMutation()}catch(e){toast(friendlyError(e,'Smart-card validation'),'error')}finally{setBusy(button,false)}}
async function migration(mode,button){setBusy(button,true,mode==='dry-run'?'Validating…':'Importing…');try{const f=$('migrationFile').files[0];if(!f)throw Error('Choose CSV/XLSX first');const fd=new FormData();fd.append('file',f);const d=await api('/api/migration/'+mode,{method:'POST',body:fd});$('migrationResult').className=`notice ${d.status==='COMPLETED'?'good':d.status==='REJECTED'?'bad':''}`;$('migrationResult').innerHTML=`<b>${esc(d.status)}</b><br>Source ${esc(d.source_name)} · ${d.source_rows} rows · valid ${d.valid_rows} · invalid ${d.invalid_rows} · duplicates ${d.duplicate_rows} · migrated ${d.migrated_rows}`;toast(mode==='dry-run'?'Validation complete':'Migration complete');await refreshAfterMutation(loadMigrations)}catch(e){toast(friendlyError(e,'Migration'),'error')}finally{setBusy(button,false)}}async function rollbackMigration(id){if(!confirm('Rollback this completed migration batch?'))return;try{await api('/api/migration/runs/'+id+'/rollback',{method:'POST'});toast('Migration batch rolled back');await refreshAfterMutation(loadMigrations)}catch(e){toast(friendlyError(e,'Migration rollback'),'error')}}
async function loadMigrations(){const m=list(await api('/api/migration/runs'));$('migrationTable').innerHTML=table(['Run','Source','Status','Source','Valid','Invalid','Duplicates','Migrated','Action'],m.map(x=>`<tr><td>${x.id}</td><td>${esc(x.source_name)}</td><td><span class="status ${x.status==='COMPLETED'?'ok':x.status==='ROLLED_BACK'?'warn':'bad'}">${esc(x.status)}</span></td><td>${x.source_rows}</td><td>${x.valid_rows}</td><td>${x.invalid_rows}</td><td>${x.duplicate_rows}</td><td>${x.migrated_rows}</td><td>${x.status==='COMPLETED'?`<button class="link" onclick="rollbackMigration(${x.id})">Rollback</button>`:'—'}</td></tr>`).join(''))}
async function loadReports(){const [d,c0,a0,summary]=await Promise.all([api('/api/dashboard'),api('/api/reports/circulation'),api('/api/audit'),api('/api/reports/summary')]);const c=list(c0),a=list(a0);$('reportMetrics').innerHTML=[['Items',d.books],['Members',d.members],['Available',d.available],['Issued',d.issued],['RFID',d.rfid_tags],['Gate',d.gate_events],['Notifications',d.notifications],['Audit',d.audit_events],['Unpaid fines','₹'+Number(summary.unpaid_fines).toFixed(2)],['Missing',summary.missing_inventory]].map(x=>`<div class="metric"><small>${x[0]}</small><b>${x[1]}</b></div>`).join('');$('reportCirculation').innerHTML=c.map(x=>row('Book #'+x.book_id,'Member #'+x.member_id+' · '+x.protocol,dt(x.checkout_at),x.status)).join('')||row('No transactions','');$('reportAudit').innerHTML=a.slice(0,40).map(x=>row(x.action,x.actor+' · '+x.entity,dt(x.created_at),x.outcome)).join('')||row('No audit entries','')}
async function loadAdmin(){try{const [u0,c]=await Promise.all([api('/api/admin/users'),api('/api/admin/config')]);const u=list(u0);$('usersTable').innerHTML=table(['Username','Role','Active','Created'],u.map(x=>`<tr><td><b>${esc(x.username)}</b></td><td>${esc(x.role)}</td><td>${x.active?'Yes':'No'}</td><td>${dt(x.created_at)}</td></tr>`).join(''));$('fineLimit').value=c.fine_limit||100;$('loanDays').value=c.loan_days||14;$('configResult').textContent='Configuration loaded.'}catch(e){toast(e.message,'error')}}async function createUser(button){setBusy(button,true,'Creating…');try{await api('/api/admin/users',{method:'POST',headers:jsonHeaders,body:JSON.stringify({username:$('newUser').value.trim(),password:$('newPass').value,role:$('newRole').value})});toast('Staff account created');$('newUser').value='';$('newPass').value='';await refreshAfterMutation(loadAdmin)}catch(e){toast(friendlyError(e,'Create staff account'),'error')}finally{setBusy(button,false)}}
async function saveConfig(button){setBusy(button,true,'Saving…');try{await api('/api/admin/config',{method:'POST',headers:jsonHeaders,body:JSON.stringify({key:'fine_limit',value:$('fineLimit').value})});await api('/api/admin/config',{method:'POST',headers:jsonHeaders,body:JSON.stringify({key:'loan_days',value:$('loanDays').value})});$('configResult').className='notice good';$('configResult').textContent='Parameters saved and audited.';toast('Library parameters updated');await refreshAfterMutation(loadAdmin)}catch(e){toast(friendlyError(e,'Save parameters'),'error')}finally{setBusy(button,false)}}
async function loadOpac(){const q=encodeURIComponent($('opacSearch')?.value||'');const r=list(await api('/api/opac?q='+q));$('opacTable').innerHTML=table(['Title','Author','Category','Availability','Accession'],r.map(x=>`<tr><td><b>${esc(x.title)}</b></td><td>${esc(x.author)}</td><td>${esc(x.category)}</td><td><span class="status ${x.available?'ok':'bad'}">${x.available?'Available':'Issued'}</span></td><td>${esc(x.accession_no)}</td></tr>`).join(''))}
async function runDemo(button){setBusy(button,true,'Running demo…');try{await createBookSafe({accession_no:'DEMO-ILMS-001',title:'RFID Library Systems',author:'AISYS Demo',category:'Technology'});await createMemberSafe({member_no:'DEMO-M-001',name:'Demo Patron',email:'demo@example.local'});await associateSafe({accession_no:'DEMO-ILMS-001',tag_id:'RFID-DEMO-ILMS-001'});await api('/api/rfid/read',{method:'POST',headers:jsonHeaders,body:JSON.stringify({tag_id:'RFID-DEMO-ILMS-001',shelf:'A-01',expected_shelf:'A-01'})});toast('Acceptance demo completed');await refreshAll()}catch(e){toast(friendlyError(e,'Acceptance demo'),'error')}finally{setBusy(button,false)}}async function createBookSafe(b){try{return await api('/api/books',{method:'POST',headers:jsonHeaders,body:JSON.stringify(b)})}catch(e){if(e.message.includes('already exists'))return null;throw e}}async function createMemberSafe(b){try{return await api('/api/members',{method:'POST',headers:jsonHeaders,body:JSON.stringify(b)})}catch(e){if(e.message.includes('already exists'))return null;throw e}}async function associateSafe(b){try{return await api('/api/rfid/associate',{method:'POST',headers:jsonHeaders,body:JSON.stringify(b)})}catch(e){if(e.message.includes('already exists'))return null;throw e}}
window.addEventListener('error',e=>{if(e?.message)toast(friendlyError(e.error||e,'Interface error'),'error')});window.addEventListener('unhandledrejection',e=>{e.preventDefault();toast(friendlyError(e.reason,'Interface operation'),'error')});if(token)showApp();
