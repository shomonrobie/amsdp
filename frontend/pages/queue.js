import React from 'react';
const L = {
  bn:{t:'কিউ',d:'ডাক্তার',dt:'তারিখ',p:'অবস্থান',tk:'টোকেন',pt:'রোগী',st:'অবস্থা',na:'কোন কিউ এন্ট্রি পাওয়া যায়নি',ld:'লোড কিউ'},
  en:{t:'Queue',d:'Doctor',dt:'Date',p:'Position',tk:'Token',pt:'Patient',st:'Status',na:'No queue entries found',ld:'Load Queue'},
};
function T(k){const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';return (L[l]||L.bn)[k]||k;}

export default function Queue(){
  const u=typeof window!=='undefined'?JSON.parse(sessionStorage.getItem('amsdp_user')||'{}'):{};
  if(!u||!u.id)return<div style={{padding:'2rem',textAlign:'center'}}><h1>Login Required</h1><p><a href="/">Go to login</a></p></div>;

  async function load(e){
    e.preventDefault();
    const tkn=sessionStorage.getItem('amsdp_token');
    const pr=document.getElementById('qr');
    const did=document.getElementById('qdid')?.value||'';
    const dt=document.getElementById('qdt')?.value||'';
    if(!did||!dt){pr.innerHTML='<p style="color:#d32f2f">Please enter Doctor ID and Date</p>';return;}
    try{
      const r=await fetch('/api/v1/queue?organization_id='+encodeURIComponent(u.organization_id)+'&branch_id='+encodeURIComponent(u.branch_id||'br1')+'&doctor_id='+encodeURIComponent(did)+'&date='+encodeURIComponent(dt),{
        headers:{'Authorization':'Bearer '+tkn}
      });
      if(!r.ok){pr.innerHTML='<p style="color:#d32f2f">Error: '+r.status+'</p>';return;}
      const d=await r.json();
      const entries=d.entries||[];
      if(!entries.length){pr.innerHTML='<p>'+T('na')+'</p>';return;}
      let html='<p><strong>Waiting:</strong> '+d.waiting+' | <strong>Date:</strong> '+d.date+'</p>'+
        '<table style="width:100%;borderCollapse:collapse"><thead><tr style="background:#eef">'+
        '<th style="padding:0.5rem;textAlign:left">'+T('p')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('tk')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('pt')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">Source</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('st')+'</th></tr></thead><tbody>';
      for(let i=0;i<entries.length;i++){
        const e=entries[i];
        html+='<tr style="borderBottom:1px solid #ddd">'+
          '<td style="padding:0.5rem">'+(e.position||'')+'</td>'+
          '<td style="padding:0.5rem">'+(e.token||'')+'</td>'+
          '<td style="padding:0.5rem">'+(e.patient_id||'').substring(0,8)+'</td>'+
          '<td style="padding:0.5rem">'+(e.entry_source||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(e.status||'')+'</td></tr>';
      }
      html+='</tbody></table>';
      pr.innerHTML=html;
    }catch(err){pr.innerHTML='<p style="color:#d32f2f">Connection failed</p>';}
  }

  return(
    <div>
      <h1>{T('t')}</h1>
      <form onSubmit={load} style={{display:'flex',gap:'0.5rem',marginBottom:'1rem',alignItems:'center'}}>
        <input id="qdid" type="text" placeholder="Doctor ID" style={{padding:'0.5rem',fontSize:'0.9rem',width:'180px'}} />
        <input id="qdt" type="date" placeholder="Date" style={{padding:'0.5rem',fontSize:'0.9rem'}} />
        <button type="submit" style={{padding:'0.5rem 1rem',background:'#1a5c7a',color:'#fff',border:'none',borderRadius:'4px',cursor:'pointer'}}>{T('ld')}</button>
      </form>
      <div id="qr"><p>{T('na')}</p></div>
      <div style={{textAlign:'right',marginTop:'0.5rem',fontSize:'0.85rem'}}>
        <a href="#" onClick={(e)=>{e.preventDefault();const c=sessionStorage.getItem('locale')||'bn';sessionStorage.setItem('locale',c==='bn'?'en':'bn');window.location.reload();}}>English / বাংলা</a>
      </div>
    </div>
  );
}
