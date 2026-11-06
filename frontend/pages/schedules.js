import React from 'react';
const L = {
  bn:{t:'সাময়সূচী',n:'নাম',d:'ডাক্তার',na:'কোন সাময়সূচী পাওয়া যায়নি'},
  en:{t:'Schedules',n:'Name',d:'Doctor',na:'No schedules found'},
};
function T(k){const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';return (L[l]||L.bn)[k]||k;}

export default function Schedules(){
  const u=typeof window!=='undefined'?JSON.parse(sessionStorage.getItem('amsdp_user')||'{}'):{};
  if(!u||!u.id)return<div style={{padding:'2rem',textAlign:'center'}}><h1>Login Required</h1><p><a href="/">Go to login</a></p></div>;

  async function load(e){
    e.preventDefault();
    const tkn=sessionStorage.getItem('amsdp_token');
    const pr=document.getElementById('sr');
    try{
      const r=await fetch('/api/v1/schedules?organization_id='+encodeURIComponent(u.organization_id),{
        headers:{'Authorization':'Bearer '+tkn}
      });
      if(!r.ok){pr.innerHTML='<p style="color:#d32f2f">Error: '+r.status+'</p>';return;}
      const items=await r.json();
      if(!items.length){pr.innerHTML='<p>'+T('na')+'</p>';return;}
      let html='<table style="width:100%;borderCollapse:collapse"><thead><tr style="background:#eef">'+
        '<th style="padding:0.5rem;textAlign:left">'+T('d')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">Day</th>'+
        '<th style="padding:0.5rem;textAlign:left">Start</th>'+
        '<th style="padding:0.5rem;textAlign:left">End</th>'+
        '<th style="padding:0.5rem;textAlign:left">Slot (min)</th></tr></thead><tbody>';
      for(let i=0;i<items.length;i++){
        const s=items[i];
        const tmpl=s.slot_templates&&s.slot_templates[0]?s.slot_templates[0]:{};
        html+='<tr style="borderBottom:1px solid #ddd">'+
          '<td style="padding:0.5rem">'+(s.doctor_id||'').substring(0,8)+'</td>'+
          '<td style="padding:0.5rem">'+(tmpl.day_of_week!==undefined?['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][tmpl.day_of_week]:'-')+'</td>'+
          '<td style="padding:0.5rem">'+(tmpl.start_time||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(tmpl.end_time||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(tmpl.slot_duration_minutes||'-')+'</td></tr>';
      }
      html+='</tbody></table>';
      pr.innerHTML=html;
    }catch(err){pr.innerHTML='<p style="color:#d32f2f">Connection failed</p>';}
  }

  return(
    <div>
      <h1>{T('t')}</h1>
      <form onSubmit={load}>
        <button type="submit" style={{padding:'0.5rem 1.5rem',background:'#1a5c7a',color:'#fff',border:'none',borderRadius:'4px',cursor:'pointer'}}>{T('t')}</button>
      </form>
      <div id="sr"><p>{T('na')}</p></div>
      <div style={{textAlign:'right',marginTop:'0.5rem',fontSize:'0.85rem'}}>
        <a href="#" onClick={(e)=>{e.preventDefault();const c=sessionStorage.getItem('locale')||'bn';sessionStorage.setItem('locale',c==='bn'?'en':'bn');window.location.reload();}}>English / বাংলা</a>
      </div>
    </div>
  );
}
