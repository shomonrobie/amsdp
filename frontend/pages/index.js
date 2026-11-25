import React from 'react';
import { t, getLocale, setLocale } from '../lib/i18n';

export default function Login(){
  const h=async(e)=>{
    e.preventDefault();
    const u=document.getElementById('lu').value,p=document.getElementById('lp').value;
    const er=document.getElementById('lerr');
    try{
      const r=await fetch('/api/v1/staff/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
      if(!r.ok){er.textContent=t('homeF');er.style.display='block';return;}
      const d=await r.json();
      sessionStorage.setItem('amsdp_token',d.token);
      sessionStorage.setItem('amsdp_user',JSON.stringify(d.user));
      window.location.href='/dashboard';
    }catch(e){er.textContent=t('homeC');er.style.display='block';}
  };
  const tg=(e)=>{e.preventDefault();setLocale(getLocale()==='bn'?'en':'bn');window.location.reload();};
  return(
    <div style={{maxWidth:'400px',margin:'4rem auto',background:'#fff',padding:'2rem',borderRadius:'8px',boxShadow:'0 2px 8px rgba(0,0,0,0.1)'}}>
      <h1 style={{color:'#1a5c7a',textAlign:'center'}}>{t('homeN')}</h1>
      <h2 style={{fontSize:'0.9rem',color:'#666',textAlign:'center',marginBottom:'1.5rem'}}>{t('homeS')}</h2>
      <form onSubmit={h} style={{display:'flex',flexDirection:'column',gap:'0.5rem'}}>
        <label style={{fontWeight:'bold'}}>{t('homeU')}</label>
        <input id="lu" type="text" required style={{padding:'0.5rem',border:'1px solid #ccc',borderRadius:'4px',fontSize:'1rem'}} />
        <label style={{fontWeight:'bold'}}>{t('homeP')}</label>
        <input id="lp" type="password" required style={{padding:'0.5rem',border:'1px solid #ccc',borderRadius:'4px',fontSize:'1rem'}} />
        <button type="submit" style={{cursor:'pointer',background:'#1a5c7a',color:'#fff',border:'none',padding:'0.5rem 1.5rem',borderRadius:'4px',fontSize:'1rem'}}>{t('homeL')}</button>
      </form>
      <p id="lerr" style={{display:'none',color:'#d32f2f'}}></p>
      <div style={{marginTop:'1.5rem',textAlign:'center'}}><a href="#" onClick={tg} style={{color:'#1a5c7a'}}>{t('homeT')}</a></div>
      <div style={{marginTop:'0.75rem',fontSize:'0.75rem',color:'#888',textAlign:'center'}}>Demo: <b>admin</b> · password in <code>.env</code> (<code>AMSDP_DEMO_PASSWORD_ADMIN</code>)</div>
    </div>
  );
}
