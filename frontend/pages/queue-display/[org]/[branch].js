import React from 'react';
import { tIn } from '../../../lib/i18n';

/* DQDS — Digital Queue Display System: public, read-only waiting-room board.
   No authentication, no patient identity, one poll of
   /api/v1/queue/display/{org}/{branch}[?display=<code>] every 10 s (the
   response is served "public, max-age=10").

   MP-38 … MP-45 live here:

   * **Language precedence (MD-12 / AC-08).** `?lang=` wins; below it the
     *configured* display language returned by the API; only an unconfigured
     branch board falls back to the device's stored preference.  Nothing on a
     configured display reads or writes storage, so clearing a browser leaves the
     language exactly as the facility configured it.
   * **Validator handling (MP-43 / MD-15).** The board keeps the weak `ETag` and
     sends `If-None-Match`; a `304` leaves React state untouched, so an idle
     screen never re-renders on a poll.
   * **Presentation.** TV-scale typography (`clamp()` in `styles/global.css`), the
     configured display name in the header, the room label, the estimated wait
     with its mandatory marker, and the facility-controlled footer.
   * **Absent means absent (MD-17).** A field the facility switched off is not in
     the payload; the page renders nothing for it.  It never hides a value the
     server sent — that would make this page the safety boundary.

   Client-only values (route, language) are resolved after mount so the
   server-rendered markup matches the first client render — no hydration drift. */

const REFRESH_MS = 10000;           /* matches the cache window (max-age=10) */
const LOCALE_KEY = 'dqds_locale';   /* device preference: unconfigured boards only */
const LANGS = ['bn', 'en'];
const DASH = '\u2014';              /* em dash: no room assigned, no token */

/* Route, query string and storage are client-only — call from effects only. */
function parseRoute(){
  const m = window.location.pathname.match(/\/queue-display\/([^/]+)\/([^/]+)(?:\/.*)?$/);
  if(m&&m[1]&&m[2]) return {org:decodeURIComponent(m[1]),branch:decodeURIComponent(m[2])};
  return null;
}

/* `?display=<code>` selects one configured board for this branch (MP-36). */
function displayQuery(){
  const m = window.location.search.match(/[?&]display=([^&]*)/);
  return m&&m[1] ? decodeURIComponent(m[1]).trim().toLowerCase() : '';
}

function langQuery(){
  const m = window.location.search.match(/[?&]lang=(bn|en)(?:&|$)/);
  return m ? m[1] : '';
}

/* Device preference: the board's own choice, then a staff preview's locale, then
   the AMSDP default (bn).  Consulted only when no display is configured. */
function deviceLang(){
  try{
    const stored = window.localStorage.getItem(LOCALE_KEY);
    if(LANGS.indexOf(stored)>=0) return stored;
    const sess = window.sessionStorage.getItem('locale');
    if(LANGS.indexOf(sess)>=0) return sess;
  }catch(err){/* storage unavailable (private mode) — use the default */}
  return 'bn';
}

function boardUrl(route, code){
  const base = '/api/v1/queue/display/'+encodeURIComponent(route.org)+'/'+encodeURIComponent(route.branch);
  return code ? base+'?display='+encodeURIComponent(code) : base;
}

function fmtTime(iso,lang){
  if(!iso) return DASH;
  try{
    return new Intl.DateTimeFormat(lang==='bn'?'bn-BD':'en-GB',
      {hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date(iso));
  }catch(err){ return DASH; }
}


export default function QueueDisplay(){
  const [route,setRoute]=React.useState(undefined);  /* undefined=resolving, null=bad URL */
  const [code,setCode]=React.useState('');           /* ?display= from the URL */
  const [lang,setLang]=React.useState('bn');
  const [langLocked,setLangLocked]=React.useState(false); /* ?lang= or an operator toggle */
  const [configuredLang,setConfiguredLang]=React.useState('');
  const [d,setD]=React.useState(null);
  const [phase,setPhase]=React.useState('loading');  /* loading|ready|notfound|error */
  const [stale,setStale]=React.useState(false);
  const [lastUpd,setLastUpd]=React.useState(null);
  const [nonce,setNonce]=React.useState(0);          /* bumped by Retry */

  React.useEffect(()=>{
    const override=langQuery();
    if(override){ setLang(override); setLangLocked(true); }
    else setLang(deviceLang());
    setCode(displayQuery());
    setRoute(parseRoute());
  },[]);

  /* The configured language is applied once, and only while nothing has been
     locked on top of it — a `?lang=` override or an operator's own choice. */
  React.useEffect(()=>{
    const wanted=(d&&d.display&&d.display.language)||'';
    if(!wanted||langLocked||wanted===configuredLang) return;
    setConfiguredLang(wanted);
    setLang(wanted);
  },[d,langLocked,configuredLang]);

  React.useEffect(()=>{
    if(!route) return undefined;
    let cancelled=false;
    let inFlight=false;
    let etag='';                       /* weak validator from the last 200 (MP-43) */
    const url=boardUrl(route,code);

    function load(){
      if(inFlight) return;
      inFlight=true;
      const headers={Accept:'application/json'};
      /* Revalidate instead of re-downloading: an unchanged board answers 304. */
      if(etag) headers['If-None-Match']=etag;
      fetch(url,{headers})
        .then(r=>{
          if(r.status===304) return {unchanged:true};   /* no state change, no re-render */
          if(r.status===404){           /* unknown branch or unknown/disabled display */
            if(!cancelled){setPhase('notfound');setD(null);setStale(false);setLastUpd(null);}
            return {unchanged:true};
          }
          if(!r.ok) throw new Error('http '+r.status);
          etag=r.headers.get('ETag')||etag;
          return r.json().then(j=>({payload:j}));
        })
        .then(res=>{
          if(cancelled||!res||res.unchanged) return;
          setD(res.payload); setPhase('ready'); setStale(false);
          setLastUpd(res.payload.updated_at||new Date().toISOString());
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
  },[route,code,nonce]);

  const tr=(k)=>tIn(lang,k);
  function retry(){setPhase('loading');setStale(false);setNonce(n=>n+1);}

  /* A local toggle is an explicit override: on a configured board it is written
     into the URL (so it survives a restart without any storage) and on an
     unconfigured board it is remembered on the device. */
  function toggleLang(){
    const next=lang==='bn'?'en':'bn';
    setLang(next);
    const configured=!!(d&&d.display&&d.display.language);
    if(configured||langLocked){
      setLangLocked(true);
      try{
        const q=window.location.search.replace(/[?&]lang=(bn|en)/,'');
        const search=(q?q+'&':'?')+'lang='+next;
        window.history.replaceState(null,'',window.location.pathname+search);
      }catch(err){/* history unavailable — the choice still holds for this session */}
      return;
    }
    try{window.localStorage.setItem(LOCALE_KEY,next);}catch(err){/* ignore */}
  }

  const display=d&&d.display;
  const orgLabel=(d&&d.organization&&d.organization.name)||(route&&route.org)||'';
  const branchLabel=(d&&d.branch&&d.branch.name)||(route&&route.branch)||'';
  const branchCode=(d&&d.branch&&d.branch.code)||(route&&route.branch)||'';
  const missing=route===null||phase==='notfound';

  /* One body per state; the shell (org/branch context + footer) stays mounted
     throughout so the board always says which branch it belongs to. */
  let body;
  if(route===undefined){
    body=(<p className="dqds-loading" role="status">{tr('dqdsLoading')}</p>);
  }else if(missing){
    body=(<div className="dqds-error"><h2>{tr('dqdsNotFound')}</h2><p>{tr('dqdsNotFoundHint')}</p></div>);
  }else if(phase==='error'&&!d){
    body=(
      <div className="dqds-error">
        <h2>{tr('dqdsError')}</h2>
        <button type="button" className="dqds-retry" onClick={retry}>{tr('dqdsRetry')}</button>
      </div>
    );
  }else if(!d){
    body=(<p className="dqds-loading" role="status">{tr('dqdsLoading')}</p>);
  }else if(!d.doctors||d.doctors.length===0){
    body=(<div className="dqds-empty" role="status"><h2>{tr('dqdsEmpty')}</h2></div>);
  }else{
    body=(
      <div className="dqds-doctors" aria-live="polite">
        {d.doctors.map((doc,i)=>(
          <div key={(doc.doctor_name||'doctor')+'-'+i} className="dqds-doc-row"
            data-testid="dqds-doctor-row">
            <div className="dqds-doc-head">
              <div className="dqds-doc-name">{doc.doctor_name||DASH}</div>
              {/* The room is a facility label.  A doctor with no chamber has no
                  room_name key at all, and a facility may switch the field off
                  (MP-45) — either way nothing is invented and nothing is hidden. */}
              {doc.room_name!==undefined
                ? <div className="dqds-room" data-testid="dqds-room">{doc.room_name||DASH}</div>
                : null}
            </div>
            <div className="dqds-doc-info">
              <span className="dqds-serving">
                <span className="dqds-label">{tr('dqdsNowServing')}</span>
                <span className="dqds-token" data-testid="dqds-token">{doc.currently_serving||DASH}</span>
              </span>
              {doc.patients_waiting!==undefined
                ? (
                  <span className="dqds-waiting" data-testid="dqds-waiting-count">
                    <span className="dqds-wait-count">{doc.patients_waiting||'0'}</span>
                    <span className="dqds-label">{tr('dqdsWaitingCount')}</span>
                  </span>
                )
                : null}
              {/* MD-13 / R-13: the marker sits next to the number, in the board's
                  own language, and the wording never promises a time. */}
              {doc.estimated_wait_minutes!==undefined
                ? (
                  <span className="dqds-waiting dqds-estimate" data-testid="dqds-estimate">
                    <span className="dqds-est-badge" aria-hidden="true">&#8776;</span>
                    <span className="dqds-est-value">{doc.estimated_wait_minutes}</span>
                    <span className="dqds-label">
                      {tr('dqdsEstWait')} ({tr('dqdsMinutes')})
                    </span>
                  </span>
                )
                : null}
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
            {/* A configured display names itself; the branch board keeps the
                organisation as its heading. */}
            <h1 className="dqds-org" data-testid="dqds-title">
              {(display&&display.name)||orgLabel||'AMSDP'}
            </h1>
            <p className="dqds-branch">{tr('branch')}: {branchLabel||DASH}</p>
            {display&&display.scope_type&&display.scope_type!=='branch'
              ? <p className="dqds-scope" data-testid="dqds-scope">{tr('dispScope')}: {scopeLabel(display,tr)}</p>
              : null}
          </div>
          <div className="dqds-header-right">
            <div className="dqds-title">{tr('dqdsTitle')}</div>
            <button type="button" className="dqds-lang" onClick={toggleLang}
              aria-label={tr('dqdsLangSwitchLabel')}>
              {tr('dqdsLangSwitch')}
            </button>
          </div>
        </div>

        {stale&&d?<div className="dqds-stale" role="status">{tr('dqdsStale')}</div>:null}

        {body}

        <div className="dqds-footer">
          <span className="dqds-upd">{tr('dqdsUpdated')}: {fmtTime(lastUpd,lang)}</span>
          {/* Facility-controlled public information (MD-17): rendered only when
              the facility set it, in the display's own language. */}
          {display&&display.footer_text
            ? <span className="dqds-footer-text" data-testid="dqds-footer-text">{display.footer_text}</span>
            : null}
          <span className="dqds-org-code">AMSDP &middot; {branchCode}</span>
        </div>
      </div>
    </div>
  );
}

/* The scope is facility configuration, so it is labelled in the board language.
   The translator is passed in: this helper lives at module scope and has no
   access to the component's `tr`, and an earlier version referenced it anyway —
   which threw a ReferenceError the moment a non-branch display rendered. */
function scopeLabel(display,tr){
  if(display.scope_type==='doctors') return tr('dispScopeDoctors');
  if(display.scope_type==='department') return tr('dispScopeDepartment');
  if(display.scope_type==='room') return tr('dispScopeRoom');
  return tr('dispScopeBranch');
}
