import React from 'react';
const L = {
  bn:{t:'ডাক্তার',n:'নাম',s:'বিশেষত্ব',m:'মোবাইল',na:'কোন ডাক্তার পাওয়া যায়নি'},
  en:{t:'Doctors',n:'Name',s:'Speciality',m:'Mobile',na:'No doctors found'},
};
function T(k){const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';return (L[l]||L.bn)[k]||k;}

export default function Doctors(){
  const u=typeof window!=='undefined'?JSON.parse(sessionStorage.getItem('amsdp_user')||'{}'):{};
  if(!u||!u.id)return<div style={{padding:'2rem',textAlign:'center'}}><h1>Login Required</h1><p><a href="/">Go to login</a></p></div>;

  async function doSearch(e){
    e.preventDefault();
    const tkn=sessionStorage.getItem('amsdp_token');
    const pr=document.getElementById('dr');
    try{
      const r=await fetch('/api/v1/doctors?organization_id='+encodeURIComponent(u.organization_id),{
        headers:{'Authorization':'Bearer '+tkn}
      });
      if(!r.ok){pr.innerHTML='<p style="color:#d32f2f">Error: '+r.status+'</p>';return;}
      const d=await r.json();
      const items=d.items||[];
      if(!items.length){pr.innerHTML='<p>'+T('na')+'</p>';return;}
      let html='<table style="width:100%;borderCollapse:collapse"><thead><tr style="background:#eef">'+
        '<th style="padding:0.5rem;textAlign:left">ID</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('n')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('s')+'</th>'+
        '<th style="padding:0.5rem;textAlign:left">'+T('m')+'</th></tr></thead><tbody>';
      for(let i=0;i<items.length;i++){
        const p=items[i];
        html+='<tr style="borderBottom:1px solid #ddd">'+
          '<td style="padding:0.5rem">'+(p.id||p.doctor_id||'').substring(0,8)+'</td>'+
          '<td style="padding:0.5rem">'+(p.name||'')+'</td>'+
          '<td style="padding:0.5rem">'+(p.speciality||'-')+'</td>'+
          '<td style="padding:0.5rem">'+(p.mobile||'-')+'</td></tr>';
      }
      html+='</tbody></table>';
      pr.innerHTML=html;
    }catch(err){pr.innerHTML='<p style="color:#d32f2f">Connection failed</p>';}
  }

  return(
    <div>
      <h1>{T('t')}</h1>
      <form onSubmit={doSearch}>
        <button type="submit" style={{padding:'0.5rem 1.5rem',background:'#1a5c7a',color:'#fff',border:'none',borderRadius:'4px',cursor:'pointer'}}>{T('t')} — {T('s')}</button>
      </form>
      <div id="dr"><p>{T('na')}</p></div>
      <div style={{textAlign:'right',marginTop:'0.5rem',fontSize:'0.85rem'}}>
        <a href="#" onClick={(e)=>{e.preventDefault();const c=sessionStorage.getItem('locale')||'bn';sessionStorage.setItem('locale',c==='bn'?'en':'bn');window.location.reload();}}>English / বাংলা</a>
      </div>
    </div>
  );
}
