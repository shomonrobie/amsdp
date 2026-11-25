import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import { t } from '../lib/i18n';
export async function getServerSideProps(){return{props:{}}}

function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Orgs(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[showForm,setShowForm]=React.useState(false);const[f,setF]=React.useState({name:'',code:'',address:''});
  const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
  React.useEffect(()=>{fetch('/api/v1/orgs',{headers:h}).then(r=>r.ok?r.json():[]).then(d=>{setItems(d);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})},[]);
  const create=async()=>{
    const r=await fetch('/api/v1/orgs',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(f)});
    if(r.ok){const d=await r.json();setItems([...items,d]);setShowForm(false);setF({name:'',code:'',address:''});}else setErr(t('createFailed'));
  };
  if(!u.id)return null;
  if(loading)return<div className='loading'>{t('loading')}</div>;
  return(<RequireLogin><AppShell active="/orgs" breadcrumbs={[{ label: t('orgT') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{t('orgT')}</h1>
      {(u.role==='super_admin')&&<button className='btn' onClick={()=>setShowForm(true)}>{t('orgCr')}</button>}</div>
    {err&&<div className='error'>{err}</div>}
    {items.length===0?<div className='empty'>{t('orgNa')}</div>:
    <table><thead><tr><th>{t('orgN')}</th><th>{t('orgC')}</th><th>{t('orgS')}</th><th>{t('orgA')}</th></tr></thead><tbody>
      {items.map(o=><tr key={o.id}><td>{o.name}</td><td>{o.code}</td><td><span className={'badge '+(o.status==='active'?'badge-active':'badge-inactive')}>{o.status}</span></td><td>{o.address}</td></tr>)}
    </tbody></table>}
    {showForm&&<div className='modal-overlay' onClick={()=>setShowForm(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{t('orgCr')}</h3>
      <div className='form-group'><label>{t('orgN')}</label><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></div>
      <div className='form-group'><label>{t('orgC')}</label><input value={f.code} onChange={e=>setF({...f,code:e.target.value})}/></div>
      <div className='form-group'><label>{t('orgA')}</label><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowForm(false)}>{t('cancel')}</button><button className='btn' onClick={create}>{t('save')}</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}