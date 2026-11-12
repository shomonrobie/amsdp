export async function getServerSideProps(){return{props:{}}}
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
const L={bn:{t:'অ্যাপয়েন্টমেন্ট',p:'রোগী',d:'ডাক্তার',dt:'তারিখ',tm:'সময়',st:'অবস্থা',tk:'টোকেন',na:'কোন অ্যাপয়েন্টমেন্ট নেই',bk:'বুকিং',wi:'ওয়াক-ইন',cc:'বাতিল',ci:'চেক-ইন',cr:'তৈরি করুন'},
  en:{t:'Appointments',p:'Patient',d:'Doctor',dt:'Date',tm:'Time',st:'Status',tk:'Token',na:'No appointments',bk:'Book',wi:'Walk-in',cc:'Cancel',ci:'Check-in',cr:'Create'}};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
function tok(){return typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':''}
const STATUSES={BOOKED:'Booked',CONFIRMED:'Confirmed',CHECKED_IN:'Checked In',IN_QUEUE:'In Queue',IN_CONSULTATION:'In Consultation',COMPLETED:'Completed',CANCELLED:'Cancelled',NO_SHOW:'No-Show',RESCHEDULED:'Rescheduled'};
const ACTIONS={BOOKED:['CONFIRMED','CANCELLED'],CONFIRMED:['CHECKED_IN','CANCELLED'],CHECKED_IN:['IN_QUEUE'],IN_QUEUE:['IN_CONSULTATION','CANCELLED'],IN_CONSULTATION:['COMPLETED']};

export default function Appointments(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[doctors,setDoctors]=React.useState([]);const[patients,setPatients]=React.useState([]);
  const[showBook,setShowBook]=React.useState(false);const[showWalkin,setShowWalkin]=React.useState(false);
  const[filterDate,setFilterDate]=React.useState('');const[filterDoctor,setFilterDoctor]=React.useState('');
  const[reason,setReason]=React.useState('');const[actionTarget,setActionTarget]=React.useState(null);
  const u=usr();const h={'Authorization':'Bearer '+tok()};
  const load=()=>{let url='/api/v1/appointments';const q=[];if(filterDate)q.push('date='+filterDate);if(filterDoctor)q.push('doctor_id='+filterDoctor);if(q.length)url+='?'+q.join('&');
    fetch(url,{headers:h}).then(r=>r.ok?r.json():[]).then(d=>{setItems(Array.isArray(d)?d:[]);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})};
  React.useEffect(()=>{load();fetch('/api/v1/doctors',{headers:h}).then(r=>r.ok?r.json():{items:[]}).then(d=>setDoctors(d.items||[]));
    fetch('/api/v1/patients?page=1&limit=100',{headers:h}).then(r=>r.ok?r.json():{items:[]}).then(d=>setPatients(d.items||[]))},[filterDate,filterDoctor]);

  const doAction=async(id,status,r)=>{const resp=await fetch('/api/v1/appointments/'+id+'/status',{method:'PATCH',headers:{'Content-Type':'application/json',...h},body:JSON.stringify({status,reason:r||''})});
    if(resp.ok){setActionTarget(null);setReason('');load()}else{const e=await resp.json();setErr('Action failed: '+(e.detail||resp.status))}};
  const cancel=(id)=>{doAction(id,'CANCELLED',reason)};
  const checkin=(id)=>{fetch('/api/v1/appointments/'+id+'/check-in',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify({status:'CHECKED_IN',reason:''})}).then(r=>{if(r.ok)load();else setErr('Check-in failed')})};

  const[fBook,setFBook]=React.useState({patient_id:'',doctor_id:'',appointment_date:'',start_time:'',notes:''});
  const book=async()=>{const r=await fetch('/api/v1/appointments',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(fBook)});
    if(r.ok){setShowBook(false);setFBook({patient_id:'',doctor_id:'',appointment_date:'',start_time:'',notes:''});load()}else{const e=await r.json();setErr('Booking failed: '+(e.detail||r.status))}};
  const[fWalk,setFWalk]=React.useState({patient_id:'',doctor_id:'',notes:''});
  const walkin=async()=>{const r=await fetch('/api/v1/appointments/walk-in',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(fWalk)});
    if(r.ok){setShowWalkin(false);setFWalk({patient_id:'',doctor_id:'',notes:''});load()}else{const e=await r.json();setErr('Walk-in failed: '+(e.detail||r.status))}};
if(!u.id)return null;
  return(<RequireLogin><AppShell active="/appointments" breadcrumbs={[{ label: T('t') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{T('t')}</h1>
      <div className='flex'>{['super_admin','org_admin','branch_admin','receptionist'].includes(u.role)&&<>
        <button className='btn' onClick={()=>setShowBook(true)}>{T('bk')}</button>
        <button className='btn' onClick={()=>setShowWalkin(true)}>{T('wi')}</button></>}</div></div>
    <div className='flex mb-2 flex-wrap'>
      <input type='date' value={filterDate} onChange={e=>{setFilterDate(e.target.value);setLoading(true)}} style={{width:'160px'}}/>
      <select value={filterDoctor} onChange={e=>{setFilterDoctor(e.target.value);setLoading(true)}} style={{width:'180px'}}>
        <option value=''>All Doctors</option>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select>
      <button className='btn' onClick={load}>{T('t')}</button></div>
    {err&&<div className='error'>{err}</div>}
    {loading?<div className='loading'>Loading...</div>:items.length===0?<div className='empty'>{T('na')}</div>:
    <table><thead><tr><th>{T('tk')}</th><th>{T('p')}</th><th>{T('d')}</th><th>{T('dt')}</th><th>{T('tm')}</th><th>{T('st')}</th><th>Actions</th></tr></thead><tbody>
      {items.slice(0,50).map(a=>{const dn=doctors.find(d=>d.id===a.doctor_id);const pn=patients.find(p=>p.id===a.patient_id);
        const isBad=a.status==='CANCELLED'||a.status==='NO_SHOW';
        return <tr key={a.id} style={{opacity:isBad?0.6:1,background:isBad?'#f5f5f5':''}}>
          <td>{a.token_number||'-'}</td><td>{pn?pn.name:a.patient_id.substring(0,8)}</td>
          <td>{dn?dn.name:a.doctor_id.substring(0,8)}</td><td>{a.appointment_date}</td><td>{a.start_time||'-'}</td>
          <td><span className={'badge '+(isBad?'badge-inactive':'badge-active')}>{STATUSES[a.status]||a.status}</span></td>
          <td><div className='flex flex-wrap'>
            {ACTIONS[a.status]&&ACTIONS[a.status].map(act=>{
              const lb={CONFIRMED:'Confirm',CHECKED_IN:'CheckIn',IN_QUEUE:'To Cons',IN_CONSULTATION:'Complete',CANCELLED:'Cancel'}[act]||act;
              return <button key={act} className='btn btn-sm' onClick={()=>{if(act==='CANCELLED'){setActionTarget(a.id);setReason('')}else doAction(a.id,act,'')}}
                style={{margin:2,background:act==='CANCELLED'?'#c62828':'#1a5c7a'}}>{lb}</button>
            })}
            <button className='btn btn-sm btn-outline' onClick={()=>checkin(a.id)} style={{margin:2}}>{T('ci')}</button>
          </div></td>
        </tr>})}
    </tbody></table>}

    {showBook&&<div className='modal-overlay' onClick={()=>setShowBook(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('bk')}</h3>
      <div className='form-group'><label>{T('p')}</label><select value={fBook.patient_id} onChange={e=>setFBook({...fBook,patient_id:e.target.value})}>
        <option value=''>Select...</option>{patients.map(p=><option key={p.id} value={p.id}>{p.name} ({p.mobile})</option>)}</select></div>
      <div className='form-group'><label>{T('d')}</label><select value={fBook.doctor_id} onChange={e=>setFBook({...fBook,doctor_id:e.target.value})}>
        <option value=''>Select...</option>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
      <div className='form-group'><label>{T('dt')}</label><input type='date' value={fBook.appointment_date} onChange={e=>setFBook({...fBook,appointment_date:e.target.value})}/></div>
      <div className='form-group'><label>{T('tm')}</label><input type='time' value={fBook.start_time} onChange={e=>setFBook({...fBook,start_time:e.target.value})}/></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowBook(false)}>Cancel</button><button className='btn' onClick={book}>Save</button></div>
    </div></div>}

    {showWalkin&&<div className='modal-overlay' onClick={()=>setShowWalkin(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('wi')}</h3>
      <div className='form-group'><label>{T('p')}</label><select value={fWalk.patient_id} onChange={e=>setFWalk({...fWalk,patient_id:e.target.value})}>
        <option value=''>Select existing...</option>{patients.map(p=><option key={p.id} value={p.id}>{p.name} ({p.mobile})</option>)}</select></div>
      <div className='form-group'><label>{T('d')}</label><select value={fWalk.doctor_id} onChange={e=>setFWalk({...fWalk,doctor_id:e.target.value})}>
        <option value=''>Select...</option>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowWalkin(false)}>Cancel</button><button className='btn' onClick={walkin}>Save</button></div>
    </div></div>}

    {actionTarget&&<div className='modal-overlay' onClick={()=>setActionTarget(null)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('cc')}</h3><p>Cancellation reason:</p>
      <input value={reason} onChange={e=>setReason(e.target.value)} placeholder='Required'/>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setActionTarget(null)}>Back</button>
        <button className='btn btn-danger' onClick={()=>cancel(actionTarget)}>Confirm Cancel</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}
    