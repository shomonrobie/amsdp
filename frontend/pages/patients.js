import React from 'react';
import AppShell from '../components/AppShell';
import BanglaNameSense from '../components/BanglaNameSense';
import { RequireLogin } from '../components/ui/Alert';
const L={bn:{t:'রোগী',n:'নাম',m:'মোবাইল',s:'লিঙ্গ',a:'ঠিকানা',na:'কোন রোগী নেই',sr:'অনুসন্ধান',rg:'নিবন্ধন',q:'নাম বা মোবাইল',dup:'সতর্কতা: এই মোবাইলে আগের রোগী আছে',age:'বয়স',dob:'জন্ম তারিখ (ঐচ্ছিক)',dobHint:'জন্ম তারিখ থেকে বয়স',rpt:'রিপোর্টকৃত বয়স',sg:'নাম প্রস্তাব'},
  en:{t:'Patients',n:'Name',m:'Mobile',s:'Sex',a:'Address',na:'No patients',sr:'Search',rg:'Register',q:'Name or Mobile',dup:'Warning: existing patient with this mobile',age:'Age',dob:'Date of Birth (optional)',dobHint:'age from DOB',rpt:'reported age',sg:'Name suggestions'}};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}
function ageCell(p){if(p.age_source==='dob'&&p.age_from_dob!=null)return p.age_from_dob+' ('+T('dobHint')+')';if(p.age_source==='reported'&&p.age!=null)return p.age+' ('+T('rpt')+')';return '-';}
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Patients(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[query,setQuery]=React.useState('');const[showReg,setShowReg]=React.useState(false);
  const[f,setF]=React.useState({name:'',mobile:'',sex:'male',address:'',date_of_birth:'',age:''});const[dupes,setDupes]=React.useState([]);
  const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
  const search=async(q)=>{const qs=q||query;if(!qs){setItems([]);setLoading(false);return;}
    setLoading(true);const r=await fetch('/api/v1/patients?q='+encodeURIComponent(qs)+'&page=1&limit=50',{headers:h});
    if(r.ok){const d=await r.json();setItems(d.items||[])}else setErr('Search failed');setLoading(false);
  };
  React.useEffect(()=>{search('')},[]);
  const register=async()=>{
    const payload={...f};
    if(!payload.date_of_birth)delete payload.date_of_birth;
    if(payload.age===''||payload.age==null)delete payload.age;
    const r=await fetch('/api/v1/patients',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(payload)});
    if(r.ok){const d=await r.json();setItems([d.patient,...items]);setDupes(d.duplicates||[]);setShowReg(false);setF({name:'',mobile:'',sex:'male',address:'',date_of_birth:'',age:''});}
    else setErr('Registration failed');
  };
  if(!u.id)return null;
  return(<RequireLogin><AppShell active="/patients" breadcrumbs={[{ label: T('t') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{T('t')}</h1>
      {(u.role==='receptionist'||u.role==='branch_admin'||u.role==='org_admin'||u.role==='super_admin')&&<button className='btn' onClick={()=>setShowReg(true)}>{T('rg')}</button>}</div>
    <div className='flex mb-2'><input placeholder={T('q')} value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&search()}/>
      <button className='btn' onClick={()=>search()} style={{marginLeft:'0.5rem',width:'auto'}}>{T('sr')}</button></div>
    {err&&<div className='error'>{err}</div>}
    {dupes.length>0&&<div className='error'>{T('dup')}: {dupes.map(d=>d.name).join(', ')}</div>}
    {loading?<div className='loading'>Loading...</div>:items.length===0?<div className='empty'>{T('na')}</div>:
    <table><thead><tr><th>{T('n')}</th><th>{T('m')}</th><th>{T('age')}</th><th>{T('s')}</th><th>{T('a')}</th></tr></thead><tbody>
      {items.map(p=><tr key={p.id}><td>{p.name}</td><td>{p.mobile}</td><td>{ageCell(p)}</td><td>{p.sex||'-'}</td><td>{p.address||'-'}</td></tr>)}
    </tbody></table>}
    {showReg&&<div className='modal-overlay' onClick={()=>setShowReg(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('rg')}</h3>
      <div className='form-group'><BanglaNameSense id='patient-name' name='name' label={T('n')} required value={f.name} onChange={v=>setF({...f,name:v})} labels={{count:T('sg')}} /></div>
      <div className='form-group'><label>{T('m')}*</label><input value={f.mobile} onChange={e=>setF({...f,mobile:e.target.value})}/></div>
      <div className='form-group'><label>{T('s')}</label><select value={f.sex} onChange={e=>setF({...f,sex:e.target.value})}><option value='male'>Male</option><option value='female'>Female</option></select></div>
      <div className='form-group'><label>{T('a')}</label><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></div>
      <div className='form-group'><label>{T('dob')}</label><input type='date' value={f.date_of_birth} onChange={e=>setF({...f,date_of_birth:e.target.value})}/></div>
      <div className='form-group'><label>{T('age')} <small>({T('rpt')})</small></label><input type='number' min='0' max='150' value={f.age} onChange={e=>setF({...f,age:e.target.value})}/></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowReg(false)}>Cancel</button><button className='btn' onClick={register}>Save</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}