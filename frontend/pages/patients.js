import React from 'react';

const L = {
  bn:{t:'রোগী',s:'অনুসন্ধান',q:'নাম / মোবাইল',n:'নাম',m:'মোবাইল',a:'ঠিকানা',
      g:'লিঙ্গ',i:'আইডি',na:'কোন রোগী পাওয়া যায়নি',ns:'উপরে টাইপ করুন ও অনুসন্ধান ক্লিক করুন'},
  en:{t:'Patients',s:'Search',q:'Name / Mobile',n:'Name',m:'Mobile',a:'Address',
      g:'Gender',i:'ID',na:'No patients found',ns:'Type above and click Search'},
};
function T(k){const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';return (L[l]||L.bn)[k]||k;}

export default function Patients(){
  const u=typeof window!=='undefined'?JSON.parse(sessionStorage.getItem('amsdp_user')||'{}'):{};
  if(!u||!u.id)return<div style={{padding:'2rem',textAlign:'center'}}><h1>Login Required</h1><p><a href="/">Go to login</a></p></div>;

  // Client-side search handler using same pattern as login page
  async function doSearch(e){
    e.preventDefault();
    const el=document.getElementById('pq');
    const q=el?el.value.trim():'';
    if(!q)return;
    const tkn=sessionStorage.getItem('amsdp_token');
    const pr=document.getElementById('pr');
    try{
      const r=await fetch('/api/v1/patients?organization_id='+encodeURIComponent(u.organization_id)+'&q='+encodeURIComponent(q)+'&page=1&limit=20',{
        headers:{'Authorization':'Bearer '+tkn}
      });
      if(!r.ok){pr.innerHTML='<p style="color:#d32f2f">Error: '+r.status+'</p>';return;}
      const d=await r.json();
      const items=d.items||[];
      if(!items.length){pr.innerHTML='<p>'+T('na')+'</p>';return;}
      let html='<table style="width:100%;borderCollapse:collapse"><thead><tr style="background:#eef">'+
        '<th style="padding:0.5rem;textAlign:left">'+T('i')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('n')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('m')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('g')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('a')+'</th></tr></thead><tbody>';
      for(let i=0;i<items.length;i++){
        const p=items[i];
        html+='<tr style="borderBottom:1px solid #ddd">'+
          '<td style="padding:0.5rem">'+(p.id||p.patient_id||'').substring(0,8)+'</td>'+
          '<td style="padding:0.5rem">'+(p.name||'')+'</td>'+
          '<td style="padding:0.5rem">'+(p.mobile||'')+'</td>'+
          '<td style="padding:0.5rem">'+(p.gender||p.sex||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(p.address||'')+'</td></tr>';
      }
      html+='</tbody></table>';
      pr.innerHTML=html;
    }catch(err){pr.innerHTML='<p style="color:#d32f2f">Connection failed</p>';}
  }

  return(
    <div>
      <h1>{T('t')}</h1>
      <form onSubmit={doSearch} style={{display:'flex',gap:'0.5rem',marginBottom:'1rem'}}>
        <input id="pq" type="text" placeholder={T('q')} style={{flex:1,padding:'0.5rem',fontSize:'1rem'}} />
        <button type="submit" style={{padding:'0.5rem 1rem',background:'#1a5c7a',color:'#fff',border:'none',borderRadius:'4px',cursor:'pointer'}}>{T('s')}</button>
      </form>
      <div id="pr"><p>{T('ns')}</p></div>
      <div style={{textAlign:'right',marginTop:'0.5rem',fontSize:'0.85rem'}}>
        <a href="#" onClick={(e)=>{e.preventDefault();const c=sessionStorage.getItem('locale')||'bn';sessionStorage.setItem('locale',c==='bn'?'en':'bn');window.location.reload();}}>English / বাংলা</a>
      </div>
    </div>
  );
}
