import React from 'react';
import AppShell from '../components/AppShell';
import BanglaNameSense from '../components/BanglaNameSense';
import { RequireLogin } from '../components/ui/Alert';
import { t } from '../lib/i18n';

function ageCell(p){if(p.age_source==='dob'&&p.age_from_dob!=null)return p.age_from_dob+' ('+t('patDobHint')+')';if(p.age_source==='reported'&&p.age!=null)return p.age+' ('+t('patRpt')+')';return '-';}
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Patients(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[query,setQuery]=React.useState('');const[showReg,setShowReg]=React.useState(false);
  const[f,setF]=React.useState({name:'',mobile:'',sex:'male',address:'',date_of_birth:'',age:''});const[dupes,setDupes]=React.useState([]);
  const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
  const search=async(q)=>{const qs=q||query;if(!qs){setItems([]);setLoading(false);return;}
    setLoading(true);const r=await fetch('/api/v1/patients?q='+encodeURIComponent(qs)+'&page=1&limit=50',{headers:h});
    if(r.ok){const d=await r.json();setItems(d.items||[])}else setErr(t('searchFailed'));setLoading(false);
  };
  React.useEffect(()=>{search('')},[]);
  const register=async()=>{
    const payload={...f};
    if(!payload.date_of_birth)delete payload.date_of_birth;
    if(payload.age===''||payload.age==null)delete payload.age;
    const r=await fetch('/api/v1/patients',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(payload)});
    if(r.ok){const d=await r.json();setItems([d.patient,...items]);setDupes(d.duplicates||[]);setShowReg(false);setF({name:'',mobile:'',sex:'male',address:'',date_of_birth:'',age:''});}
    else setErr(t('registerFailed'));
  };
  if(!u.id)return null;
  return(<RequireLogin><AppShell active="/patients" breadcrumbs={[{ label: t('patT') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{t('patT')}</h1>
      {(u.role==='receptionist'||u.role==='branch_admin'||u.role==='org_admin'||u.role==='super_admin')&&<button className='btn' onClick={()=>setShowReg(true)}>{t('patRg')}</button>}</div>
    <div className='flex mb-2'><input placeholder={t('patQ')} value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&search()}/>
      <button className='btn' onClick={()=>search()} style={{marginLeft:'0.5rem',width:'auto'}}>{t('patSr')}</button></div>
    {err&&<div className='error'>{err}</div>}
    {dupes.length>0&&<div className='error'>{t('patDup')}: {dupes.map(d=>d.name).join(', ')}</div>}
    {loading?<div className='loading'>{t('loading')}</div>:items.length===0?<div className='empty'>{t('patNa')}</div>:
    <table><thead><tr><th>{t('patN')}</th><th>{t('patM')}</th><th>{t('patAge')}</th><th>{t('patS')}</th><th>{t('patA')}</th></tr></thead><tbody>
      {items.map(p=><tr key={p.id}><td>{p.name}</td><td>{p.mobile}</td><td>{ageCell(p)}</td><td>{p.sex||'-'}</td><td>{p.address||'-'}</td></tr>)}
    </tbody></table>}
    {showReg&&<div className='modal-overlay' onClick={()=>setShowReg(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{t('patRg')}</h3>
      <div className='form-group'><BanglaNameSense id='patient-name' name='name' label={t('patN')} required value={f.name} onChange={v=>setF({...f,name:v})} labels={{count:t('patSg')}} /></div>
      <div className='form-group'><label>{t('patM')}*</label><input value={f.mobile} onChange={e=>setF({...f,mobile:e.target.value})}/></div>
      <div className='form-group'><label>{t('patS')}</label><select value={f.sex} onChange={e=>setF({...f,sex:e.target.value})}><option value='male'>{t('male')}</option><option value='female'>{t('female')}</option></select></div>
      <div className='form-group'><label>{t('patA')}</label><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></div>
      <div className='form-group'><label>{t('patDob')}</label><input type='date' value={f.date_of_birth} onChange={e=>setF({...f,date_of_birth:e.target.value})}/></div>
      <div className='form-group'><label>{t('patAge')} <small>({t('patRpt')})</small></label><input type='number' min='0' max='150' value={f.age} onChange={e=>setF({...f,age:e.target.value})}/></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowReg(false)}>{t('cancel')}</button><button className='btn' onClick={register}>{t('save')}</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}