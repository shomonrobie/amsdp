import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
const L={bn:{t:'স্টাফ',un:'ব্যবহারকারীর নাম',n:'নাম',r:'ভূমিকা',s:'অবস্থা',b:'শাখা',na:'কোন স্টাফ নেই',cr:'তৈরি করুন'},
  en:{t:'Staff',un:'Username',n:'Name',r:'Role',s:'Status',b:'Branch',na:'No staff',cr:'Create Staff'}};
const ROLES={super_admin:'Super Admin',org_admin:'Org Admin',branch_admin:'Branch Admin',receptionist:'Receptionist',doctor:'Doctor',assistant:'Assistant'};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Staff(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[showForm,setShowForm]=React.useState(false);const[f,setF]=React.useState({username:'',password:'',display_name:'',role:'receptionist',branch_id:''});
  const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
  const load=()=>{fetch('/api/v1/staff/users?organization_id='+u.organization_id,{headers:h}).then(r=>r.ok?r.json():[]).then(d=>{setItems(d);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})};
  React.useEffect(load,[]);
  const create=async()=>{
    const r=await fetch('/api/v1/staff/users',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify({...f,organization_id:u.organization_id})});
    if(r.ok){const d=await r.json();load();setShowForm(false);setF({username:'',password:'',display_name:'',role:'receptionist',branch_id:''});}else{const e=await r.text();setErr('Error: '+e);}
  };
  if(!u.id)return null;
  if(loading)return<div className='loading'>Loading...</div>;
  return(<RequireLogin><AppShell active="/staff" breadcrumbs={[{ label: T('t') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{T('t')}</h1>
      {(u.role==='super_admin'||u.role==='org_admin')&&<button className='btn' onClick={()=>setShowForm(true)}>{T('cr')}</button>}</div>
    {err&&<div className='error'>{err}</div>}
    {items.length===0?<div className='empty'>{T('na')}</div>:
    <table><thead><tr><th>{T('un')}</th><th>{T('n')}</th><th>{T('r')}</th><th>{T('s')}</th></tr></thead><tbody>
      {items.map(s=><tr key={s.id}><td>{s.username}</td><td>{s.display_name}</td><td>{ROLES[s.role]||s.role}</td><td><span className={'badge '+(s.status==='active'?'badge-active':'badge-inactive')}>{s.status}</span></td></tr>)}
    </tbody></table>}
    {showForm&&<div className='modal-overlay' onClick={()=>setShowForm(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('cr')}</h3>
      <div className='form-group'><label>{T('un')}</label><input value={f.username} onChange={e=>setF({...f,username:e.target.value})}/></div>
      <div className='form-group'><label>{T('n')}</label><input value={f.display_name} onChange={e=>setF({...f,display_name:e.target.value})}/></div>
      <div className='form-group'><label>Password</label><input type='password' value={f.password} onChange={e=>setF({...f,password:e.target.value})}/></div>
      <div className='form-group'><label>{T('r')}</label><select value={f.role} onChange={e=>setF({...f,role:e.target.value})}>
        {Object.entries(ROLES).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowForm(false)}>Cancel</button><button className='btn' onClick={create}>Save</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}