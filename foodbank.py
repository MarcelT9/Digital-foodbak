/*
Digital Food Bank - Frontend-only React app (single-file)
File: digital_foodbank_web_react.jsx

Features (frontend-only, stores data in localStorage):
- Simple client-side auth (register/login) saved to localStorage (demo only)
- Donor can create donations with geolocation (browser prompt) or manual lat/lon
- Recipient can search nearby donations by radius (km) and claim them
- Donations expire after specified minutes
- Distance calculation uses Haversine formula
- Export/Import JSON for persistence sharing

Usage:
- Paste this file into a React project (e.g., Create React App) and import as <App />
- Tailwind CSS classes are used; if Tailwind isn't available the styling will still be functional but unstyled

Notes:
- This is a frontend-only prototype for a GitHub repo 'web system only' requirement.
- Replace localStorage with API calls when adding a backend.
*/

import React, { useEffect, useState } from 'react';

const LS_KEY = 'digital_foodbank_v1';
const LS_USERS = 'digital_foodbank_users_v1';

// --- Utilities
function haversineKm(lat1, lon1, lat2, lon2) {
  const toRad = (v) => (v * Math.PI) / 180;
  const R = 6371; // km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function nowISO() { return new Date().toISOString(); }

function loadState() {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}'); } catch { return {}; }
}
function saveState(state) { localStorage.setItem(LS_KEY, JSON.stringify(state || {})); }

function loadUsers() {
  try { return JSON.parse(localStorage.getItem(LS_USERS) || '[]'); } catch { return []; }
}
function saveUsers(users) { localStorage.setItem(LS_USERS, JSON.stringify(users || [])); }

// --- Default seed
function seedIfEmpty() {
  const s = loadState();
  if (!s.donations) {
    s.donations = [];
    saveState(s);
  }
  const users = loadUsers();
  if (users.length === 0) {
    saveUsers([
      { id: 1, name: 'Alice Donor', email: 'alice@donor', password: 'pass', role: 'donor' },
      { id: 2, name: 'Bob Recipient', email: 'bob@rec', password: 'pass', role: 'recipient' },
    ]);
  }
}

// --- App
export default function App() {
  seedIfEmpty();
  const [user, setUser] = useState(null);
  const [donations, setDonations] = useState(() => loadState().donations || []);
  const [filter, setFilter] = useState({ lat: '', lon: '', radius: 10 });
  const [view, setView] = useState('browse'); // browse | create | account | admin

  useEffect(() => { saveState({ donations }); }, [donations]);

  // Auth helpers (very simple)
  function register({ name, email, password, role }){
    const users = loadUsers();
    if (users.find(u => u.email === email)) return { error: 'Email exists' };
    const id = (users[users.length-1]?.id || 0) + 1;
    const u = { id, name, email, password, role };
    users.push(u); saveUsers(users); setUser(u); return { ok: true };
  }
  function login({ email, password }){
    const users = loadUsers();
    const u = users.find(x => x.email === email && x.password === password);
    if (!u) return { error: 'Invalid credentials' };
    setUser(u); return { ok: true };
  }
  function logout(){ setUser(null); }

  // Donation operations
  function createDonation(payload){
    const id = (donations[donations.length-1]?.id || 0) + 1;
    const expires_at = payload.expires_in_minutes ? new Date(Date.now() + payload.expires_in_minutes*60000).toISOString() : null;
    const d = {
      id, title: payload.title, description: payload.description, quantity: payload.quantity || 1,
      lat: Number(payload.lat), lon: Number(payload.lon), donor_id: user.id, donor_name: user.name,
      created_at: nowISO(), expires_at, claimed: false, claimed_by: null
    };
    setDonations(prev => [d, ...prev]);
    setView('browse');
  }

  function claimDonation(id){
    if (!user || user.role !== 'recipient') { alert('Only recipients can claim'); return; }
    setDonations(prev => prev.map(d => d.id===id? {...d, claimed:true, claimed_by:user.id, claimed_by_name:user.name}: d));
  }

  function getNearby(lat, lon, radiusKm){
    const now = new Date();
    return donations.filter(d => {
      if (d.claimed) return false;
      if (d.expires_at && new Date(d.expires_at) < now) return false;
      const dist = haversineKm(lat, lon, d.lat, d.lon);
      return dist <= radiusKm;
    }).map(d => ({ ...d, distance_km: haversineKm(lat, lon, d.lat, d.lon).toFixed(2) }));
  }

  // UI components inside App for brevity
  return (
    <div className="min-h-screen p-6 bg-gray-50 font-sans">
      <header className="max-w-4xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Digital Food Bank — Web (Frontend-only)</h1>
          <div className="space-x-2">
            <button onClick={() => setView('browse')} className="px-3 py-1 rounded bg-white border">Browse</button>
            <button onClick={() => setView('create')} className="px-3 py-1 rounded bg-white border">Create</button>
            <button onClick={() => setView('account')} className="px-3 py-1 rounded bg-white border">Account</button>
          </div>
        </div>
        <div className="mt-2 text-sm text-gray-600">Frontend-only demo — data persisted to <code>localStorage</code>. Replace with an API to go production.</div>
      </header>

      <main className="max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <aside className="md:col-span-1 bg-white p-4 rounded shadow">
            <h2 className="font-semibold">Search Nearby Donations</h2>
            <SearchBox filter={filter} setFilter={setFilter} onUseGeolocate={(lat, lon) => setFilter(f => ({...f, lat, lon}))} />

            <div className="mt-4">
              <h3 className="text-sm font-medium">Quick Actions</h3>
              <div className="mt-2 space-y-2">
                <button onClick={() => { navigator.clipboard?.writeText(JSON.stringify(loadState())); alert('Export copied to clipboard'); }} className="w-full px-3 py-2 border rounded">Copy export JSON</button>
                <button onClick={() => { const s = prompt('Paste JSON to import'); try{ if(s){ const data = JSON.parse(s); if (data.donations) { setDonations(data.donations); alert('Imported'); } else alert('No donations found'); } }catch(e){alert('Invalid JSON')}}} className="w-full px-3 py-2 border rounded">Import JSON</button>
                <button onClick={() => { if(confirm('Clear all donations?')) setDonations([]); }} className="w-full px-3 py-2 border rounded text-red-600">Clear donations</button>
              </div>
            </div>
          </aside>

          <section className="md:col-span-2">
            {view === 'browse' && (
              <BrowseView filter={filter} onClaim={claimDonation} donations={donations} />
            )}
            {view === 'create' && (
              <CreateView onCreate={createDonation} user={user} onNeedLogin={() => setView('account')} />
            )}
            {view === 'account' && (
              <AccountView user={user} onLogin={login} onRegister={register} onLogout={logout} />
            )}
          </section>
        </div>
      </main>

      <footer className="max-w-4xl mx-auto mt-8 text-sm text-gray-500">Built as a frontend-only prototype — convert to full web system by connecting to a backend API.</footer>
    </div>
  );
}

// --- Subcomponents
function SearchBox({ filter, setFilter, onUseGeolocate }){
  const [lat, setLat] = useState(filter.lat||'');
  const [lon, setLon] = useState(filter.lon||'');
  const [radius, setRadius] = useState(filter.radius||10);
  useEffect(()=>{ setLat(filter.lat); setLon(filter.lon); setRadius(filter.radius); }, [filter]);
  return (
    <div>
      <label className="block text-sm">Latitude</label>
      <input value={lat} onChange={e=>setLat(e.target.value)} className="w-full border rounded px-2 py-1" placeholder="e.g. -1.286389" />
      <label className="block text-sm mt-2">Longitude</label>
      <input value={lon} onChange={e=>setLon(e.target.value)} className="w-full border rounded px-2 py-1" placeholder="e.g. 36.817223" />
      <label className="block text-sm mt-2">Radius (km)</label>
      <input type="number" value={radius} onChange={e=>setRadius(e.target.value)} className="w-full border rounded px-2 py-1" />
      <div className="flex gap-2 mt-3">
        <button onClick={()=>{ setFilter({ lat, lon, radius }); }} className="flex-1 px-3 py-2 border rounded">Apply</button>
        <button onClick={()=>{ if(navigator.geolocation){ navigator.geolocation.getCurrentPosition(pos=>{ const {latitude, longitude}=pos.coords; setLat(latitude); setLon(longitude); setFilter({lat:latitude, lon:longitude, radius}); onUseGeolocate(latitude, longitude); }, err=>alert('Geolocation failed: '+err.message)) }else alert('Geolocation not supported'); }} className="px-3 py-2 border rounded">Use my location</button>
      </div>
    </div>
  );
}

function BrowseView({ filter, onClaim, donations }){
  const lat = Number(filter.lat);
  const lon = Number(filter.lon);
  const radius = Number(filter.radius||10);
  const [list, setList] = useState([]);
  useEffect(()=>{
    if (!isFinite(lat) || !isFinite(lon)) {
      setList(donations.filter(d=>!d.claimed && !(d.expires_at && new Date(d.expires_at) < new Date())));
    } else {
      const results = donations
        .filter(d=> !d.claimed && !(d.expires_at && new Date(d.expires_at) < new Date()))
        .map(d=> ({...d, distance_km: haversineKm(lat, lon, d.lat, d.lon)}))
        .filter(d=> d.distance_km <= radius)
        .sort((a,b)=> a.distance_km - b.distance_km);
      setList(results);
    }
  }, [filter, donations]);

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold">Available Donations</h2>
      <div className="mt-3 space-y-3">
        {list.length===0 && <div className="text-sm text-gray-500">No available donations in range.</div>}
        {list.map(d=> (
          <div key={d.id} className="border rounded p-3">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-medium">{d.title}</div>
                <div className="text-sm text-gray-600">by {d.donor_name} • Qty {d.quantity}</div>
                <div className="text-sm mt-1">{d.description}</div>
              </div>
              <div className="text-right">
                <div className="text-sm">{d.distance_km ? Number(d.distance_km).toFixed(2)+' km' : ''}</div>
                <div className="text-xs text-gray-500">Expires: {d.expires_at ? new Date(d.expires_at).toLocaleString() : '—'}</div>
              </div>
            </div>
            <div className="mt-2 flex gap-2">
              <button onClick={()=>{ if(confirm('Claim this donation?')) onClaim(d.id) }} className="px-3 py-1 border rounded">Claim</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CreateView({ onCreate, user, onNeedLogin }){
  const [form, setForm] = useState({ title:'', description:'', quantity:1, lat:'', lon:'', expires_in_minutes:240 });
  function tryGeolocate(){ if(navigator.geolocation){ navigator.geolocation.getCurrentPosition(pos=> setForm(f=>({...f, lat: pos.coords.latitude, lon: pos.coords.longitude})), err=> alert('Geolocation failed: '+err.message)); } else alert('Geolocation not supported'); }
  function submit(){ if(!user){ onNeedLogin(); return; } if(!form.title||!form.lat||!form.lon){ alert('Please provide title and location'); return; } onCreate(form); }
  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold">Create Donation</h2>
      <div className="mt-3 space-y-2">
        <input placeholder="Title" value={form.title} onChange={e=>setForm({...form, title:e.target.value})} className="w-full border rounded px-2 py-1" />
        <textarea placeholder="Description" value={form.description} onChange={e=>setForm({...form, description:e.target.value})} className="w-full border rounded px-2 py-1" />
        <input type="number" value={form.quantity} onChange={e=>setForm({...form, quantity: Number(e.target.value)})} className="w-full border rounded px-2 py-1" />
        <div className="grid grid-cols-2 gap-2">
          <input placeholder="Latitude" value={form.lat} onChange={e=>setForm({...form, lat:e.target.value})} className="border rounded px-2 py-1" />
          <input placeholder="Longitude" value={form.lon} onChange={e=>setForm({...form, lon:e.target.value})} className="border rounded px-2 py-1" />
        </div>
        <div className="flex gap-2">
          <button onClick={tryGeolocate} className="px-3 py-1 border rounded">Use my location</button>
          <input type="number" value={form.expires_in_minutes} onChange={e=>setForm({...form, expires_in_minutes: Number(e.target.value)})} className="border rounded px-2 py-1" />
          <div className="text-sm text-gray-500">minutes</div>
        </div>
        <div className="flex gap-2">
          <button onClick={submit} className="px-3 py-2 bg-green-600 text-white rounded">Create</button>
        </div>
      </div>
    </div>
  );
}

function AccountView({ user, onLogin, onRegister, onLogout }){
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name:'', email:'', password:'', role:'recipient' });
  function submitLogin(){ const r = onLogin({ email: form.email, password: form.password }); if(r.error) alert(r.error); }
  function submitRegister(){ const r = onRegister({ name: form.name, email: form.email, password: form.password, role: form.role }); if(r.error) alert(r.error); }
  if (user) return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold">My Account</h2>
      <div className="mt-2">Name: {user.name}</div>
      <div>Email: {user.email}</div>
      <div>Role: {user.role}</div>
      <div className="mt-3"><button onClick={()=>{ onLogout(); }} className="px-3 py-2 border rounded">Logout</button></div>
    </div>
  );
  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold">{mode==='login' ? 'Login' : 'Register'}</h2>
      {mode==='register' && <input placeholder="Name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} className="w-full border rounded px-2 py-1 mt-2" />}
      <input placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} className="w-full border rounded px-2 py-1 mt-2" />
      <input placeholder="Password" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} className="w-full border rounded px-2 py-1 mt-2" />
      {mode==='register' && (
        <select value={form.role} onChange={e=>setForm({...form,role:e.target.value})} className="w-full border rounded px-2 py-1 mt-2">
          <option value="recipient">Recipient</option>
          <option value="donor">Donor</option>
        </select>
      )}
      <div className="mt-3 flex gap-2">
        {mode==='login' ? <button onClick={submitLogin} className="px-3 py-2 border rounded">Login</button> : <button onClick={submitRegister} className="px-3 py-2 border rounded">Register</button>}
        <button onClick={()=>setMode(mode==='login'?'register':'login')} className="px-3 py-2 border rounded">Switch</button>
      </div>
      <div className="text-xs text-gray-500 mt-2">Demo accounts: alice@donor / pass (donor), bob@rec / pass (recipient)</div>
    </div>
  );
}
