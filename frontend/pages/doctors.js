import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
const L={bn:{t:'ডাক্তার',n:'নাম',m:'মোবাইল',sp:'বিশেষত্ব',q:'ডিগ্রি',s:'অবস্থা',na:'কোন ডাক্তার নেই',rg:'নিবন্ধন',br:'শাখা'},
  en:{t:'Doctors',n:'Name',m:'Mobile',sp:'Speciality',q:'Qualification',s:'Status',na:'No doctors',rg:'Register',br:'Branches'}};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
export default function Doctors(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[showForm,setShowForm]=React.useState(false);const[query,setQuery]=React.useState('');
  const[f,setF]=React.useState({name:'',mobile:'',speciality:'',qualification:'',branch_ids:[]});
  const[branches,setBranches]=React.useState([]);
  const u=usr();const h={'Authorization':'Bearer '+(typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':'')};
  const load=async(q)=>{setLoading(true);
    let url='/api/v1/doctors';if(q)url+='?q='+encodeURIComponent(q);
    fetch(url,{headers:h}).then(r=>r.ok?r.json():{items:[]}).then(d=>{setItems(d.items||[]);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})};
  React.useEffect(()=>{load();fetch('/api/v1/orgs/'+u.organization_id+'/branches',{headers:h}).then(r=>r.ok?r.json():[]).then(setBranches).catch(()=>{})},[]);
  const toggleBranch=(bid)=>{const b=f.branch_ids;if(b.includes(bid))setF({...f,branch_ids:b.filter(x=>x!==bid)});else setF({...f,branch_ids:[...b,bid]})};
  const create=async()=>{
    const r=await fetch('/api/v1/doctors',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(f)});
    if(r.ok){const d=await r.json();setItems([d,...items]);setShowForm(false);setF({name:'',mobile:'',speciality:'',qualification:'',branch_ids:[]});}
    else setErr('Registration failed');
  };
  if(!u.id)return null;
  return(<RequireLogin><AppShell active="/doctors" breadcrumbs={[{ label: T('t') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{T('t')}</h1>
      {(u.role==='branch_admin'||u.role==='org_admin'||u.role==='super_admin')&&<button className='btn' onClick={()=>setShowForm(true)}>{T('rg')}</button>}</div>
    <div className='flex mb-2'><input placeholder={T('n')} value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&load(query)}/>
      <button className='btn' onClick={()=>load(query)} style={{marginLeft:'0.5rem',width:'auto'}}>{T('t')}</button></div>
    {err&&<div className='error'>{err}</div>}
    {loading?<div className='loading'>Loading...</div>:items.length===0?<div className='empty'>{T('na')}</div>:
    <table><thead><tr><th>{T('n')}</th><th>{T('m')}</th><th>{T('sp')}</th><th>{T('q')}</th><th>{T('s')}</th></tr></thead><tbody>
      {items.map(d=><tr key={d.id}><td>{d.name}</td><td>{d.mobile}</td><td>{d.speciality||'-'}</td><td>{d.qualification||'-'}</td><td><span className={'badge '+(d.status==='active'?'badge-active':'badge-inactive')}>{d.status}</span></td></tr>)}
    </tbody></table>}
    {showForm&&<div className='modal-overlay' onClick={()=>setShowForm(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('rg')}</h3>
      <div className='form-group'><label>{T('n')}*</label><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></div>
      <div className='form-group'><label>{T('m')}*</label><input value={f.mobile} onChange={e=>setF({...f,mobile:e.target.value})}/></div>
      <div className='form-group'><label>{T('sp')}</label><input value={f.speciality} onChange={e=>setF({...f,speciality:e.target.value})}/></div>
      <div className='form-group'><label>{T('q')}</label><input value={f.qualification} onChange={e=>setF({...f,qualification:e.target.value})}/></div>
      <div className='form-group'><label>{T('br')}</label>{branches.map(b=>
        <label key={b.id} style={{fontWeight:'normal',display:'flex',alignItems:'center',gap:'0.5rem',margin:'0.25rem 0'}}>
          <input type='checkbox' checked={f.branch_ids.includes(b.id)} onChange={()=>toggleBranch(b.id)}/>{b.name}</label>)}</div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowForm(false)}>Cancel</button><button className='btn' onClick={create}>Save</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}