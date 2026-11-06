import React from 'react';

const L = {
  bn: { n:'\u098f\u098f\u09ae\u098f\u09b8\u09a1\u09bf\u09aa\u09bf', s:'AMSDP \u2014 Appointment Management',
        u:'Username / \u09ac\u09cd\u09af\u09ac\u09b9\u09be\u09b0\u0995\u09be\u09b0\u09c0 \u09a8\u09be\u09ae',
        p:'Password / \u09aa\u09be\u09b8\u0993\u09af\u09bc\u09be\u09b0\u09cd\u09a1', l:'\u09b2\u0997\u0987\u09a8',
        f:'Login failed / \u09b2\u0997\u0987\u09a8 \u09ac\u09cd\u09af\u09b0\u09cd\u09a5',
        c:'Connection failed / \u09b8\u0982\u09af\u09cb\u0997 \u09ac\u09cd\u09af\u09b0\u09cd\u09a5',
        t:'English' },
  en: { n:'AMSDP', s:'AMSDP \u2014 Appointment Management',
        u:'Username', p:'Password', l:'Login', f:'Login failed',
        c:'Connection failed', t:'\u09ac\u09be\u0982\u09b2\u09be' },
};

function T(k){const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';return(L[l]||L.bn)[k]||k;}

export default function Login(){
  const h=async(e)=>{
    e.preventDefault();
    const u=document.getElementById('lu').value,p=document.getElementById('lp').value;
    const er=document.getElementById('lerr');
    try{
      const r=await fetch('/api/v1/staff/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
      if(!r.ok){er.textContent=T('f');er.style.display='block';return;}
      const d=await r.json();
      sessionStorage.setItem('amsdp_token',d.token);
      sessionStorage.setItem('amsdp_user',JSON.stringify(d.user));
      window.location.href='/dashboard';
    }catch(e){er.textContent=T('c');er.style.display='block';}
  };
  const tg=(e)=>{e.preventDefault();const c=sessionStorage.getItem('locale')||'bn';sessionStorage.setItem('locale',c==='bn'?'en':'bn');window.location.reload();};
  return(
    <div style={{maxWidth:'400px',margin:'4rem auto',background:'#fff',padding:'2rem',borderRadius:'8px',boxShadow:'0 2px 8px rgba(0,0,0,0.1)'}}>
      <h1 style={{color:'#1a5c7a',textAlign:'center'}}>{T('n')}</h1>
      <h2 style={{fontSize:'0.9rem',color:'#666',textAlign:'center',marginBottom:'1.5rem'}}>{T('s')}</h2>
      <form onSubmit={h} style={{display:'flex',flexDirection:'column',gap:'0.5rem'}}>
        <label style={{fontWeight:'bold'}}>{T('u')}</label>
        <input id="lu" type="text" required style={{padding:'0.5rem',border:'1px solid #ccc',borderRadius:'4px',fontSize:'1rem'}} />
        <label style={{fontWeight:'bold'}}>{T('p')}</label>
        <input id="lp" type="password" required style={{padding:'0.5rem',border:'1px solid #ccc',borderRadius:'4px',fontSize:'1rem'}} />
        <button type="submit" style={{cursor:'pointer',background:'#1a5c7a',color:'#fff',border:'none',padding:'0.5rem 1.5rem',borderRadius:'4px',fontSize:'1rem'}}>{T('l')}</button>
      </form>
      <p id="lerr" style={{display:'none',color:'#d32f2f'}}></p>
      <div style={{marginTop:'1.5rem',textAlign:'center'}}><a href="#" onClick={tg} style={{color:'#1a5c7a'}}>{T('t')}</a></div>
      <div style={{marginTop:'0.75rem',fontSize:'0.75rem',color:'#888',textAlign:'center'}}>Demo: <b>admin / admin123</b> (super_admin)</div>
    </div>
  );
}
