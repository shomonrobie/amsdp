export async function getServerSideProps(){return{props:{}}}
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
const L={bn:{t:'শিডিউল',d:'ডাক্তার',m:'মডেল',s:'অবস্থা',na:'কোন শিডিউল নেই',cr:'তৈরি করুন',av:'উপলব্ধ স্লট',da:'তারিখ',ti:'সময়',ca:'ধারণক্ষমता'},
  en:{t:'Schedules',d:'Doctor',m:'Model',s:'Status',na:'No schedules',cr:'Create Schedule',av:'Available Slots',da:'Date',ti:'Time',ca:'Capacity'}};
function T(k){const l=typeof window!=='undefined'?sessionStorage.getItem('locale')||'bn':'bn';return(L[l]||L.bn)[k]||k;}
function usr(){try{if(typeof window==='undefined')return{};return JSON.parse(sessionStorage.getItem('amsdp_user')||'{}')}catch(e){return{}}}
function tok(){return typeof window!=='undefined'?sessionStorage.getItem('amsdp_token')||'':''}
export default function Schedules(){
  const[items,setItems]=React.useState([]);const[loading,setLoading]=React.useState(true);const[err,setErr]=React.useState('');
  const[slots,setSlots]=React.useState(null);const[slotDate,setSlotDate]=React.useState('');
  const[doctors,setDoctors]=React.useState([]);const[showForm,setShowForm]=React.useState(false);
  const[f,setF]=React.useState({doctor_id:'',slot_templates:[{day_of_week:0,start_time:'09:00',end_time:'17:00',slot_duration_minutes:15,max_patients:4}],appointment_model:'time_slot'});
  const u=usr();const h={'Authorization':'Bearer '+tok()};
  const load=()=>{fetch('/api/v1/schedules',{headers:h}).then(r=>r.ok?r.json():[]).then(d=>{setItems(d);setLoading(false)}).catch(e=>{setErr(String(e));setLoading(false)})};
  React.useEffect(()=>{load();fetch('/api/v1/doctors',{headers:h}).then(r=>r.ok?r.json():{items:[]}).then(d=>setDoctors(d.items||[]))},[]);
  const loadSlots=(sid,dt)=>{if(!dt)return;fetch('/api/v1/schedules/'+sid+'/available-slots?date_str='+dt,{headers:h}).then(r=>r.ok?r.json():null).then(setSlots)};
  const create=async()=>{const r=await fetch('/api/v1/schedules',{method:'POST',headers:{'Content-Type':'application/json',...h},body:JSON.stringify(f)});if(r.ok){const d=await r.json();setItems([d,...items]);setShowForm(false)}else setErr('Create failed')};
  if(!u.id)return null;
  return(<RequireLogin><AppShell active="/schedules" breadcrumbs={[{ label: T('t') }]}><div>
    <div className='flex justify-between mb-2'><h1 className='page-title'>{T('t')}</h1>
      {['branch_admin','org_admin','super_admin'].includes(u.role)&&<button className='btn' onClick={()=>setShowForm(true)}>{T('cr')}</button>}</div>
    {err&&<div className='error'>{err}</div>}
    {loading?<div className='loading'>Loading...</div>:items.length===0?<div className='empty'>{T('na')}</div>:
    <table><thead><tr><th>{T('d')}</th><th>{T('m')}</th><th>{T('s')}</th><th>Actions</th></tr></thead><tbody>
      {items.map(s=>{const dn=doctors.find(d=>d.id===s.doctor_id);return <tr key={s.id}>
        <td>{dn?dn.name:s.doctor_id.substring(0,8)}</td><td>{s.appointment_model}</td>
        <td><span className={'badge '+(s.status==='active'?'badge-active':'badge-inactive')}>{s.status}</span></td>
        <td><input type='date' onChange={e=>{setSlotDate(e.target.value);loadSlots(s.id,e.target.value)}} style={{width:'140px',display:'inline',marginRight:'0.5rem'}}/>
          <span style={{fontSize:'0.8rem',color:'#888'}}>{T('av')}</span></td>
      </tr>})}
    </tbody></table>}
    {slots&&<div className='card mt-2'><h3 className='page-title'>{T('av')} - {slotDate}</h3>
    <table><thead><tr><th>{T('ti')}</th><th>{T('ca')}</th><th>Booked</th><th>Available</th></tr></thead><tbody>
      {slots.slots.filter(s=>s.available>0).slice(0,20).map(s=><tr key={s.start_time}><td>{s.start_time}-{s.end_time}</td><td>{s.max_patients}</td><td>{s.booked}</td><td style={{color:'green',fontWeight:'bold'}}>{s.available}</td></tr>)}
    </tbody></table></div>}
    {showForm&&<div className='modal-overlay' onClick={()=>setShowForm(false)}><div className='modal' onClick={e=>e.stopPropagation()}>
      <h3>{T('cr')}</h3>
      <div className='form-group'><label>{T('d')}</label><select value={f.doctor_id} onChange={e=>setF({...f,doctor_id:e.target.value})}>
        <option value=''>Select...</option>{doctors.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
      <div className='form-group'><label>Model</label><select value={f.appointment_model} onChange={e=>setF({...f,appointment_model:e.target.value})}>
        <option value='time_slot'>Time Slot</option><option value='serial'>Serial</option><option value='hybrid'>Hybrid</option></select></div>
      <div className='form-actions'><button className='btn-outline' onClick={()=>setShowForm(false)}>Cancel</button><button className='btn' onClick={create}>Save</button></div>
    </div></div>}
  </div></AppShell></RequireLogin>);
}