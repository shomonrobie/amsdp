import React from 'react';

function getUser(){
  try{return JSON.parse(typeof window!=='undefined'?sessionStorage.getItem('amsdp_user')||'{}':'{}');}
  catch(e){return {};}
}
function T(k){
  const l=typeof window!=='undefined'?(sessionStorage.getItem('locale')||'bn'):'bn';
  const L={bn:{d:'\u09a1\u09cd\u09af\u09be\u09b6\u09ac\u09cb\u09b0\u09cd\u09a1',w:'\u09b8\u09cd\u09ac\u09be\u0997\u09a4\u09ae',r:'\u09ad\u09c2\u09ae\u09bf\u0995\u09be',q:'\u0995\u09bf\u0989',p:'\u09b0\u09cb\u0997\u09c0 \u0985\u09a8\u09c1\u09b8\u09a8\u09cd\u09a7\u09be\u09a8',a:'\u0985\u09cd\u09af\u09be\u09aa\u0995\u09be\u09af\u09bc\u09c7\u09a8\u09cd\u099f\u09ae\u09c7\u09a8\u09cd\u099f',lo:'\u09b2\u0997\u0986\u0989\u099f',lr:'\u09b2\u0997\u0987\u09a8 \u09aa\u09cd\u09b0\u09af\u09bc\u09cb\u099c\u09a8',lg:'\u09b2\u0997\u0987\u09a8 \u09aa\u09c3\u09b7\u09cd\u09a0\u09be\u09af\u09bc \u09af\u09be\u09a8',pt:'\u09b0\u09cb\u0997\u09c0',dc:'\u09a1\u09be\u0995\u09cd\u09a4\u09b0',sc:'\u09b8\u09be\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09c0',qu:'\u0995\u09bf\u0989',ap:'\u0985\u09cd\u09af\u09be\u09aa\u0995\u09be\u09af\u09bc\u09c7\u09a8\u09cd\u099f',st:'\u09b8\u09be\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09c0'},
  en:{d:'Dashboard',w:'Welcome',r:'Role',q:'Queue',p:'Search Patients',a:'Appointments',lo:'Logout',lr:'Login Required',lg:'Go to login',pt:'Patients',dc:'Doctors',sc:'Schedules',qu:'Queue',ap:'Appointments',st:'Schedules'}};
  return(L[l]||L.bn)[k]||k;
}

export default function Dashboard(){
  const u=getUser();
  if(!u.id)return<div style={{padding:'2rem',textAlign:'center'}}><h1>{T('lr')}</h1><p><a href="/">{T('lg')}</a></p></div>;
  const nav=[
    {href:'/patients',label:T('pt')},{href:'/doctors',label:T('dc')},{href:'/schedules',label:T('st')},
    {href:'/appointments',label:T('ap')},{href:'/queue',label:T('qu')},
  ];
  return(
    <div style={{padding:'0',margin:'0 auto',maxWidth:'960px',fontFamily:'sans-serif'}}>
      <nav style={{display:'flex',gap:'0.25rem',flexWrap:'wrap',background:'#1a5c7a',padding:'0.5rem',alignItems:'center'}}>
        {nav.map(n=><a key={n.href} href={n.href} style={{color:'#fff',padding:'0.3rem 0.6rem',background:'rgba(255,255,255,0.15)',borderRadius:'4px',textDecoration:'none',fontSize:'0.9rem'}}>{n.label}</a>)}
        <span style={{color:'#ddd',padding:'0.3rem 0.6rem',fontSize:'0.8rem'}}>{u.display_name} ({u.role})</span>
        <span style={{color:'#ddd',fontSize:'0.8rem',padding:'0.3rem 0'}}>|</span>
        <a href="#" onClick={()=>{sessionStorage.clear();window.location.href='/';}} style={{color:'#ff8',padding:'0.3rem 0.6rem',fontSize:'0.85rem',textDecoration:'none'}}>{T('lo')}</a>
      </nav>
      <div style={{padding:'1rem'}}>
        <h1 style={{color:'#1a5c7a',margin:'0.5rem 0'}}>{T('d')}</h1>
        <p style={{color:'#555'}}><strong>{T('w')}:</strong> {u.display_name} | <strong>Org:</strong> {u.organization_id} | <strong>{T('r')}:</strong> {u.role}</p>
        <hr />
        <p>Select a module from the navigation above.</p>
      </div>
    </div>
  );
}
