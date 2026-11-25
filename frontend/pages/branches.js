import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import { t } from '../lib/i18n';

function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Branches(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[showForm,setShowForm]=React.useState(false);const[f,setF]=React.useState({name:'',code:'',address:'',phone:''});
  const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
  const load=()=>{const oid=u.organization_id;if(!oid){setItems([]);setLoading(false);return;}
    fetch('/api/v1/orgs/'+oid+'/branches',{headers:h}).then(r=>r.ok?r.json():[]).then(d=>{setItems(d);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})};
  React.useEffect(load,[]);
  const create=async()=>{
    const r=await fetch('/api/v1/branches',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify({...f,organization_id:u.organization_id})});
    if(r.ok){const d=await r.json();setItems([...items,d]);setShowForm(false);setF({name:'',code:'',address:'',phone:''});}else setErr(t('createFailed'));
  };
  if(!u.id)return null;
  if(loading)return<div className='loading'>{t('loading')}</div>;
  return(<RequireLogin><AppShell active="/branches" breadcrumbs={[{ label: t('brnT') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{t('brnT')}</h1>
      {u.role!=='super_admin'&&<button className='btn' onClick={()=>setShowForm(true)}>{t('brnCr')}</button>}</div>
    {err&&<div className='error'>{err}</div>}
    {items.length===0?<div className='empty'>{t('brnNa')}</div>:
    <table><thead><tr><th>{t('brnN')}</th><th>{t('brnC')}</th><th>{t('brnS')}</th><th>{t('brnA')}</th><th>{t('brnP')}</th></tr></thead><tbody>
      {items.map(b=><tr key={b.id}><td>{b.name}</td><td>{b.code}</td><td><span className={'badge '+(b.status==='active'?'badge-active':'badge-inactive')}>{b.status}</span></td><td>{b.address}</td><td>{b.phone||'-'}</td></tr>)}
    </tbody></table>}
    {showForm&&<div className='modal-overlay' onClick={()=>setShowForm(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{t('brnCr')}</h3>
      <div className='form-group'><label>{t('brnN')}</label><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></div>
      <div className='form-group'><label>{t('brnC')}</label><input value={f.code} onChange={e=>setF({...f,code:e.target.value})}/></div>
      <div className='form-group'><label>{t('brnA')}</label><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></div>
      <div className='form-group'><label>{t('brnP')}</label><input value={f.phone} onChange={e=>setF({...f,phone:e.target.value})}/></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowForm(false)}>{t('cancel')}</button><button className='btn' onClick={create}>{t('save')}</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}