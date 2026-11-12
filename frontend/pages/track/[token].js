import React from 'react';

/* PQT — Personal Queue Tracking, account-free appointment visibility. */
const L = {
  bn: {
    pl:'AMSDP - আপনার অ্যাপয়েন্টমেন্ট', ap:'অ্যাপয়েন্টমেন্ট', dt:'তারিখ', st:'সময়',
    doc:'ডাক্তার', br:'শাখা', sts:'অবস্থা', tok:'টোকেন', now:'বর্তমানে',
    ahead:'আপনার আগে', eta:'আনুমানিক অপেক্ষার সময়', min:'মিনিট', close:'বন্ধ',
    loading:'লোড হচ্ছে...', err:'তথ্য লোড করতে ব্যর্থ', prv:'এই পৃষ্ঠা শুধুমাত্র আপনার অ্যাপয়েন্টমেন্ট দেখায়।',
    warn:'অপেক্ষার সময় পরিবর্তন হতে পারে।', stay:'আপনার যদি জরুরি প্রয়োজন হয় বা থাকতে নির্দেশ দেওয়া হয়ে থাকে, দয়া করে অপেক্ষার এলাকায় থাকুন।',
  },
  en:{
    pl:'AMSDP — Your Appointment', ap:'Appointment', dt:'Date', st:'Time',
    doc:'Doctor', br:'Branch', sts:'Status', tok:'Token', now:'Now serving',
    ahead:'Ahead of you', eta:'Estimated wait', min:'min', close:'Close',
    loading:'Loading...', err:'Failed to load info', prv:'This page shows only your appointment.',
    warn:'Waiting times can change.', stay:'If you need urgent attention or have been told to stay, please remain in the waiting area.',
  },
};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}

function getP(){try{const m=window.location.pathname.match(/\/track\/(.+)/);return m?m[1]:''}catch(e){return''}}

export default function Track(){
  const [d,setD]=React.useState(null);const [l,setL]=React.useState(true);const [e,setE]=React.useState('');
  const token=getP();
  React.useEffect(()=>{
    if(!token||token.length<32){setE(T('err'));setL(false);return;}
    fetch('/api/v1/track/'+encodeURIComponent(token)).then(r=>{if(!r.ok){setE(T('err'));setL(false);return;}
      return r.json();}).then(j=>{if(j){setD(j);setL(false);}}).catch(()=>{setE(T('err'));setL(false);});
    const iv=setInterval(()=>{
      fetch('/api/v1/track/'+encodeURIComponent(token)).then(r=>r.ok?r.json():null).then(j=>{if(j)setD(j);}).catch(()=>{});
    },15000);
    return ()=>clearInterval(iv);
  },[token]);

  if(e)return(<div className="pqt-root"><div className="pqt-card"><p style={{color:'#888',textAlign:'center',padding:'2rem'}}>{T('err')}</p></div></div>);
  if(l)return(<div className="pqt-root"><div className="pqt-card"><p style={{textAlign:'center',padding:'2rem'}}>{T('loading')}</p></div></div>);
  if(!d)return null;

  const a=d.appointment||{},q=d.queue||{},doc=d.doctor||{},br=d.branch||{};
  const st_map={BOOKED:'Booked',CONFIRMED:'Confirmed',CHECKED_IN:'Checked-in',IN_QUEUE:'In queue',
    IN_CONSULTATION:'Consultation',COMPLETED:'Completed',CANCELLED:'Cancelled',NO_SHOW:'No-show',AWAITING_CONFIRMATION:'Pending'};

  return(<div className="pqt-root">
    <div className="pqt-card">
      <h2 style={{margin:'0 0 0.5rem'}}>{T('pl')}</h2>
      <p style={{fontSize:'0.75rem',color:'#888',marginBottom:'0.8rem'}}>{T('prv')}</p>

      <div className="pqt-grid">
        <div><strong>{T('doc')}</strong><br/>{doc.name||'-'}</div>
        <div><strong>{T('br')}</strong><br/>{br.name||'-'}</div>
        <div><strong>{T('dt')}</strong><br/>{a.date||'-'}</div>
        <div><strong>{T('st')}</strong><br/>{a.start_time||'-'}</div>
        <div><strong>{T('sts')}</strong><br/>{st_map[a.status]||a.status||'-'}</div>
        <div><strong>{T('tok')}</strong><br/>{q.my_token||a.token_number||'-'}</div>
      </div>

      <hr style={{border:'none',borderTop:'1px solid #ddd',margin:'1rem 0'}}/>

      <div className="pqt-queue">
        <div className="pqt-serving">
          {T('now')}: <strong style={{fontSize:'1.2rem',color:'#1a5c7a'}}>{q.currently_serving||'-'}</strong>
        </div>
        <div className="pqt-stats">
          <div><span className="stat-num">{q.patients_ahead??'-'}</span><br/>{T('ahead')}</div>
          <div><span className="stat-num">{q.estimated_wait_min??'-'}</span><br/>{T('eta')} ({T('min')})</div>
        </div>
      </div>

      <hr style={{border:'none',borderTop:'1px solid #ddd',margin:'1rem 0'}}/>
      <p style={{fontSize:'0.75rem',color:'#c62828'}}>{T('warn')}</p>
      <p style={{fontSize:'0.7rem',color:'#888'}}>{T('stay')}</p>
    </div>
  </div>);
}