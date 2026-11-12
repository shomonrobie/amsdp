import React from 'react';

/* DQDS — Digital Queue Display System: public, read-only waiting-room board.
   No authentication, no patient identity, 10 s poll of
   /api/v1/queue/display/{org}/{branch} (served with "public, max-age=10").
   Client-only values (route, language) are resolved after mount so the
   server-rendered markup matches the first client render — no hydration drift. */

const L = {
  bn: {
    tl:'লাইভ কিউ ডিসপ্লে', lq:'লোড হচ্ছে...', er:'তথ্য লোড করা যায়নি', ee:'আবার চেষ্টা করুন',
    og:'সংগঠন', br:'শাখা', dr:'ডাক্তার', now:'বর্তমানে সেবা', wt:'অপেক্ষারত',
    noq:'এই শাখায় এখন অপেক্ষারত কোনো রোগী নেই', none:'—', up:'সর্বশেষ হালনাগাদ',
    nf:'শাখাটি পাওয়া যায়নি',
    nf2:'সংগঠন বা শাখার ঠিকানাটি সঠিক নয়। অনুগ্রহ করে URL যাচাই করুন।',
    nt:'অপেক্ষারত রোগী', sv:'বর্তমানে সেবা',
    off:'সংযোগ বিচ্ছিন্ন — সর্বশেষ প্রাপ্ত তথ্য দেখানো হচ্ছে',
  },
  en: {
    tl:'Live Queue Display', lq:'Loading...', er:'Could not load the queue', ee:'Try again',
    og:'Organization', br:'Branch', dr:'Doctor', now:'Now serving', wt:'Waiting',
    noq:'No patients are waiting at this branch right now', none:'—',
    up:'Last updated', nf:'Branch not found',
    nf2:'This organization/branch address is not valid. Please check the URL.',
    nt:'patients waiting', sv:'Now serving',
    off:'Connection lost — showing the last known queue',
  },
};

const LOCALE_KEY = 'dqds_locale';   /* display-local: survives TV restarts */
const LANGS = ['bn', 'en'];
const REFRESH_MS = 10000;           /* matches the cache window (max-age=10) */

/* Route, query string and storage are client-only — call from effects only. */
function parseRoute(){
  const m = window.location.pathname.match(/\/queue-display\/([^/]+)\/([^/]+)(?:\/.*)?$/);
  if(m&&m[1]&&m[2]) return {org:decodeURIComponent(m[1]),branch:decodeURIComponent(m[2])};
  return null;
}

/* Display language: ?lang= override, then the board's own stored choice, then
   a staff preview's locale, then the AMSDP default (bn). */
function initialLang(){
  const q = window.location.search.match(/[?&]lang=(bn|en)(?:&|$)/);
  if(q) return q[1];
  try{
    const stored = window.localStorage.getItem(LOCALE_KEY);
    if(LANGS.indexOf(stored)>=0) return stored;
    const sess = window.sessionStorage.getItem('locale');
    if(LANGS.indexOf(sess)>=0) return sess;
  }catch(err){/* storage unavailable (private mode) — use the default */}
  return 'bn';
}

function fmtTime(iso,lang){
  if(!iso) return '—';
  try{
    return new Intl.DateTimeFormat(lang==='bn'?'bn-BD':'en-GB',
      {hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date(iso));
  }catch(err){ return '—'; }
}


export default function QueueDisplay(){
  const [route,setRoute]=React.useState(undefined);  /* undefined=resolving, null=bad URL */
  const [lang,setLang]=React.useState('bn');
  const [d,setD]=React.useState(null);
  const [phase,setPhase]=React.useState('loading');  /* loading|ready|notfound|error */
  const [stale,setStale]=React.useState(false);
  const [lastUpd,setLastUpd]=React.useState(null);
  const [nonce,setNonce]=React.useState(0);          /* bumped by Retry */

  React.useEffect(()=>{
    setLang(initialLang());
    setRoute(parseRoute());
  },[]);

  React.useEffect(()=>{
    if(!route) return undefined;
    let cancelled=false;
    let inFlight=false;
    const url='/api/v1/queue/display/'+encodeURIComponent(route.org)+'/'+encodeURIComponent(route.branch);

    function load(){
      if(inFlight) return;
      inFlight=true;
      fetch(url,{headers:{Accept:'application/json'}})
        .then(r=>{
          if(r.status===404){           /* unavailable org/branch — non-disclosing */
            if(!cancelled){setPhase('notfound');setD(null);setStale(false);setLastUpd(null);}
            return null;
          }
          if(!r.ok) throw new Error('http '+r.status);
          return r.json();
        })
        .then(j=>{
          if(cancelled||!j) return;
          setD(j); setPhase('ready'); setStale(false);
          setLastUpd(j.updated_at||new Date().toISOString());
        })
        .catch(()=>{
          if(cancelled) return;
          /* Temporary failure: keep the last known board on screen and flag it.
             The next successful poll clears the flag by itself (recovery). */
          setStale(true);
          setPhase(p=>p==='ready'?'ready':'error');
        })
        .then(()=>{inFlight=false;});
    }

    load();
    const iv=setInterval(load,REFRESH_MS);
    return ()=>{cancelled=true;clearInterval(iv);};
  },[route,nonce]);

  function T(k){return (L[lang]||L.bn)[k]||k;}
  function retry(){setPhase('loading');setStale(false);setNonce(n=>n+1);}
  function toggleLang(){
    const next=lang==='bn'?'en':'bn';
    setLang(next);
    try{window.localStorage.setItem(LOCALE_KEY,next);}catch(err){/* ignore */}
  }


  const orgLabel=(d&&d.organization&&d.organization.name)||(route&&route.org)||'';
  const branchLabel=(d&&d.branch&&d.branch.name)||(route&&route.branch)||'';
  const branchCode=(d&&d.branch&&d.branch.code)||(route&&route.branch)||'';
  const missing=route===null||phase==='notfound';

  /* One body per state; the shell (org/branch context + footer) stays mounted
     throughout so the board always says which branch it belongs to. */
  let body;
  if(route===undefined){
    body=(<p className="dqds-loading" role="status">{T('lq')}</p>);
  }else if(missing){
    body=(<div className="dqds-error"><h2>{T('nf')}</h2><p>{T('nf2')}</p></div>);
  }else if(phase==='error'&&!d){
    body=(
      <div className="dqds-error">
        <h2>{T('er')}</h2>
        <button type="button" className="dqds-retry" onClick={retry}>{T('ee')}</button>
      </div>
    );
  }else if(!d){
    body=(<p className="dqds-loading" role="status">{T('lq')}</p>);
  }else if(!d.doctors||d.doctors.length===0){
    body=(<div className="dqds-empty" role="status"><h2>{T('noq')}</h2></div>);
  }else{
    body=(
      <div className="dqds-doctors" aria-live="polite">
        {d.doctors.map((doc,i)=>(
          <div key={(doc.doctor_name||'doctor')+'-'+i} className="dqds-doc-row">
            <div className="dqds-doc-name">{doc.doctor_name||T('none')}</div>
            <div className="dqds-doc-info">
              <span className="dqds-serving">
                <span className="dqds-label">{T('sv')}</span>
                <span className="dqds-token">{doc.currently_serving||T('none')}</span>
              </span>
              <span className="dqds-waiting">
                <span className="dqds-wait-count">{doc.patients_waiting||'0'}</span>
                <span className="dqds-label">{T('nt')}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="dqds-root">
      <div className="dqds-card">
        <div className="dqds-header">
          <div>
            <h1 className="dqds-org">{orgLabel||'AMSDP'}</h1>
            <p className="dqds-branch">{T('br')}: {branchLabel||T('none')}</p>
          </div>
          <div className="dqds-header-right">
            <div className="dqds-title">{T('tl')}</div>
            <button type="button" className="dqds-lang" onClick={toggleLang}
              aria-label={lang==='bn'?'Switch to English':'বাংলায় দেখুন'}>
              {lang==='bn'?'English':'বাংলা'}
            </button>
          </div>
        </div>

        {stale&&d?<div className="dqds-stale" role="status">{T('off')}</div>:null}

        {body}

        <div className="dqds-footer">
          <span className="dqds-upd">{T('up')}: {fmtTime(lastUpd,lang)}</span>
          <span className="dqds-org-code">AMSDP · {branchCode}</span>
        </div>
      </div>
    </div>
  );
}
