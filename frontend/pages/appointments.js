import React from 'react';
const L = {
  bn:{t:'অ্যাপয়েন্টমেন্ট',p:'রোগী',d:'ডাক্তার',dt:'তারিখ',tm:'সময়',st:'অবস্থা',na:'কোন অ্যাপয়েন্টমেন্ট পাওয়া যায়নি'},
  en:{t:'Appointments',p:'Patient',d:'Doctor',dt:'Date',tm:'Time',st:'Status',na:'No appointments found'},
};
function T(k){const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';return (L[l]||L.bn)[k]||k;}

export default function Appointments(){
  const u=typeof window!=='undefined'?JSON.parse(sessionStorage.getItem('amsdp_user')||'{}'):{};
  if(!u||!u.id)return<div style={{padding:'2rem',textAlign:'center'}}><h1>Login Required</h1><p><a href="/">Go to login</a></p></div>;

  async function load(e){
    e.preventDefault();
    const tkn=sessionStorage.getItem('amsdp_token');
    const pr=document.getElementById('apr');
    try{
      const r=await fetch('/api/v1/appointments?organization_id='+encodeURIComponent(u.organization_id),{
        headers:{'Authorization':'Bearer '+tkn}
      });
      if(!r.ok){pr.innerHTML='<p style="color:#d32f2f">Error: '+r.status+'</p>';return;}
      const items=await r.json();
      if(!items.length){pr.innerHTML='<p>'+T('na')+'</p>';return;}
      let html='<table style="width:100%;borderCollapse:collapse"><thead><tr style="background:#eef">'+
        '<th style="padding:0.5rem;textAlign:left">Token</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('p')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('d')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('dt')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('tm')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('st')+'</th></tr></thead><tbody>';
      for(let i=0;i<items.length;i++){
        const a=items[i];
        html+='<tr style="borderBottom:1px solid #ddd">'+
          '<td style="padding:0.5rem">'+(a.token_number||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(a.patient_id||'').substring(0,8)+'</td>'+
          '<td style="padding:0.5rem">'+(a.doctor_id||'').substring(0,8)+'</td>'+
          '<td style="padding:0.5rem">'+(a.appointment_date||'')+'</td>'+
          '<td style="padding:0.5rem">'+(a.start_time||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(a.status||'scheduled')+'</td></tr>';
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
      <div id="apr"><p>{T('na')}</p></div>
      <div style={{textAlign:'right',marginTop:'0.5rem',fontSize:'0.85rem'}}>
        <a href="#" onClick={(e)=>{e.preventDefault();const c=sessionStorage.getItem('locale')||'bn';sessionStorage.setItem('locale',c==='bn'?'en':'bn');window.location.reload();}}>English / বাংলা</a>
      </div>
    </div>
  );
}
