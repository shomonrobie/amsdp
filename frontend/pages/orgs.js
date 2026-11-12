import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
export async function getServerSideProps(){return{props:{}}}
const L={bn:{t:'প্রতিষ্ঠান',n:'নাম',c:'কোড',s:'অবস্থা',a:'ঠিকানা',na:'কোন প্রতিষ্ঠান নেই',cr:'তৈরি করুন'},
  en:{t:'Organizations',n:'Name',c:'Code',s:'Status',a:'Address',na:'No organizations',cr:'Create'}};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}
function usr(){try{return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Orgs(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[showForm,setShowForm]=React.useState(false);const[f,setF]=React.useState({name:'',code:'',address:''});
  const u=usr();const h={'Authorization':'Bearer '+sessionStorage.getItem('amsdp_token')};
  React.useEffect(()=>{fetch('/api/v1/orgs',{headers:h}).then(r=>r.ok?r.json():[]).then(d=>{setItems(d);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})},[]);
  const create=async()=>{
    const r=await fetch('/api/v1/orgs',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(f)});
    if(r.ok){const d=await r.json();setItems([...items,d]);setShowForm(false);setF({name:'',code:'',address:''});}else setErr('Create failed');
  };
  if(!u.id)return null;
  if(loading)return<div className='loading'>Loading...</div>;
  return(<RequireLogin><AppShell active="/orgs" breadcrumbs={[{ label: T('t') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{T('t')}</h1>
      {(u.role==='super_admin')&&<button className='btn' onClick={()=>setShowForm(true)}>{T('cr')}</button>}</div>
    {err&&<div className='error'>{err}</div>}
    {items.length===0?<div className='empty'>{T('na')}</div>:
    <table><thead><tr><th>{T('n')}</th><th>{T('c')}</th><th>{T('s')}</th><th>{T('a')}</th></tr></thead><tbody>
      {items.map(o=><tr key={o.id}><td>{o.name}</td><td>{o.code}</td><td><span className={'badge '+(o.status==='active'?'badge-active':'badge-inactive')}>{o.status}</span></td><td>{o.address}</td></tr>)}
    </tbody></table>}
    {showForm&&<div className='modal-overlay' onClick={()=>setShowForm(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('cr')}</h3>
      <div className='form-group'><label>{T('n')}</label><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></div>
      <div className='form-group'><label>{T('c')}</label><input value={f.code} onChange={e=>setF({...f,code:e.target.value})}/></div>
      <div className='form-group'><label>{T('a')}</label><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowForm(false)}>Cancel</button><button className='btn' onClick={create}>Save</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}