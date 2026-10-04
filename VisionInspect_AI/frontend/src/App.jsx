import { useEffect, useState } from 'react';
import './App.css';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const demoAccounts = {
  engineer: { email: 'engineer@factory.com', password: 'password123' },
  supervisor: { email: 'supervisor@factory.com', password: 'supervisor123' },
  admin: { email: 'admin@factory.com', password: 'admin12345' },
};

function formatType(value) {
  return String(value || '').replaceAll('_', ' ');
}

function Login({ onLogin }) {
  const [account, setAccount] = useState('engineer');
  const [email, setEmail] = useState(demoAccounts.engineer.email);
  const [password, setPassword] = useState(demoAccounts.engineer.password);
  const [error, setError] = useState('');

  const chooseAccount = (type) => {
    setAccount(type);
    setEmail(demoAccounts[type].email);
    setPassword(demoAccounts[type].password);
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const response = await fetch(`${API}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error('Invalid credentials');
      onLogin(await response.json());
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="brand-mark">VI</div>
        <p className="eyebrow">VISIONINSPECT AI / CONTROL ROOM</p>
        <h1>Make every inspection count.</h1>
        <p className="login-copy">Computer vision for bottle quality, defect intelligence, and decisive action.</p>
        <div className="role-switcher" role="tablist" aria-label="Account role">
          <button className={account === 'engineer' ? 'active' : ''} onClick={() => chooseAccount('engineer')}>Quality engineer</button>
          <button className={account === 'supervisor' ? 'active' : ''} onClick={() => chooseAccount('supervisor')}>Factory supervisor</button>
          <button className={account === 'admin' ? 'active' : ''} onClick={() => chooseAccount('admin')}>Administrator</button>
        </div>
        <form onSubmit={submit} className="login-form">
          <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button className="primary-button" type="submit">Enter control room <span>→</span></button>
        </form>
        {error && <p className="error-text">{error}</p>}
        <p className="login-footnote">Demo access is preloaded for both roles.</p>
      </section>
      <aside className="login-visual"><div className="scan-line" /><span>LIVE QUALITY SIGNAL</span><strong>98.4%</strong><small>inspection confidence</small></aside>
    </main>
  );
}

function StatCard({ label, value, detail, tone = '' }) {
  return <div className={`stat-card ${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function InspectionView({ user, onComplete }) {
  const [files, setFiles] = useState([]);
  const [source, setSource] = useState('Manual upload');
  const [batchId, setBatchId] = useState('LINE-A / SHIFT-1');
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  const inspect = async () => {
    if (!files.length) return;
    setBusy(true); setError(''); setResults([]);
    try {
      const inspected = [];
      for (const file of files) {
        const form = new FormData();
        form.append('file', file); form.append('operator', user.role); form.append('source', source); form.append('batch_id', batchId);
        const response = await fetch(`${API}/api/inspect`, { method: 'POST', headers: { Authorization: `Bearer ${user.token}` }, body: form });
        if (!response.ok) throw new Error((await response.json()).detail || 'Inspection failed');
        inspected.push(await response.json());
      }
      setResults(inspected); onComplete();
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  };

  return <section className="workspace-grid">
    <div className="content-column">
          <div className="page-heading"><div><p className="eyebrow">BOTTLE IMAGE / INSPECTION</p><h2>Bottle inspection workspace</h2><p>Upload bottle photos for defect detection and quality scoring.</p></div><span className="status-dot">SYSTEM READY</span></div>
      <div className="upload-panel">
        <label className="drop-zone"><input type="file" accept="image/*" multiple onChange={(event) => setFiles([...event.target.files])} /><span className="upload-icon">＋</span><strong>{files.length ? `${files.length} image${files.length > 1 ? 's' : ''} selected` : 'Drop bottle images here'}</strong><small>JPG, PNG, BMP, or WebP · max 10 MB each</small></label>
        <div className="form-row"><label>Capture source<select value={source} onChange={(event) => setSource(event.target.value)}><option>Manual upload</option><option>Camera simulation</option><option>Production line capture</option><option>Historical repository</option></select></label><label>Batch / line ID<input value={batchId} onChange={(event) => setBatchId(event.target.value)} /></label><button className="primary-button inspect-button" onClick={inspect} disabled={!files.length || busy}>{busy ? 'Processing...' : 'Run inspection →'}</button></div>
      </div>
      {error && <p className="error-text">{error}</p>}
      {results.length > 0 && <div className="results-stack">{results.map((result) => <InspectionResult key={result.id} result={result} />)}</div>}
      {!results.length && <div className="empty-state"><span>◎</span><strong>Ready for a bottle image</strong><p>The inspection pipeline will preprocess, compare, classify, and score the selected bottle.</p></div>}
    </div>
    <aside className="side-column"><div className="side-card"><p className="eyebrow">PIPELINE STATUS</p>{['Image validation', 'Preprocessing & enhancement', 'Anomaly detection', 'Classification & severity', 'Quality decision'].map((step, index) => <div className="pipeline-step" key={step}><span>{String(index + 1).padStart(2, '0')}</span><strong>{step}</strong><i>Ready</i></div>)}</div><div className="side-card accent-card"><p className="eyebrow">QUALITY RULE</p><strong>Good products pass. Every bad product gets a reason.</strong><p>Critical results trigger rejection and quality review.</p></div></aside>
  </section>;
}

function InspectionResult({ result }) {
  const isGood = result.classification === 'good';
  return <article className="result-card"><div className="result-top"><div><span className={`decision ${isGood ? 'good' : 'bad'}`}>{isGood ? 'GOOD' : 'BAD'}</span><h3>{isGood ? 'Inspection clean' : formatType(result.defect_type)}</h3><small>{result.filename} · {result.id}</small></div><div className="severity"><span>SEVERITY</span><strong>{result.severity_level}</strong><b>{result.severity_score}</b></div></div><div className="result-body"><img src={result.annotated_image_base64} alt="Annotated inspection" /><div className="score-grid"><div><span>Anomaly score</span><strong>{(result.anomaly_score * 100).toFixed(1)}%</strong></div><div><span>Model confidence</span><strong>{((result.model_confidence || 0) * 100).toFixed(1)}%</strong></div><div><span>Detection confidence</span><strong>{result.confidence_score}%</strong></div><div><span>Defect count</span><strong>{result.defect_count}</strong></div><div><span>Action</span><strong>{result.recommended_action}</strong></div></div></div></article>;
}

function AnalyticsView({ analytics, history, onRefresh }) {
  const maxDefect = Math.max(1, ...Object.values(analytics.defect_counts));
  return <section className="content-column analytics-view"><div className="page-heading"><div><p className="eyebrow">PRODUCTION INTELLIGENCE / LIVE</p><h2>Quality analytics</h2><p>Operational signals from the current inspection run.</p></div><button className="secondary-button" onClick={onRefresh}>Refresh data ↻</button></div><div className="stats-grid"><StatCard label="Total inspected" value={analytics.total_inspections} detail="images processed" /><StatCard label="Pass rate" value={`${analytics.pass_rate}%`} detail="good product yield" tone="green" /><StatCard label="Bad products" value={analytics.bad_count} detail="requiring action" tone="red" /><StatCard label="Average severity" value={analytics.average_severity} detail="weighted risk score" /></div><div className="analytics-grid"><div className="chart-card"><div className="card-heading"><div><p className="eyebrow">DEFECT MIX</p><h3>Classification trend</h3></div><span>Current period</span></div>{Object.entries(analytics.defect_counts).map(([name, count]) => <div className="bar-row" key={name}><span>{formatType(name)}</span><div><i style={{ width: `${(count / maxDefect) * 100}%` }} /></div><strong>{count}</strong></div>)}</div><div className="chart-card decision-card"><p className="eyebrow">QUALITY DECISION</p><div className="donut" style={{ '--pass': `${analytics.pass_rate}%` }}><strong>{analytics.pass_rate}%</strong><span>pass rate</span></div><p>Inspection results are automatically logged for reporting and review.</p></div></div><HistoryTable items={history} /></section>;
}

function HistoryTable({ items }) {
  return <div className="history-card"><div className="card-heading"><div><p className="eyebrow">INSPECTION LOG</p><h3>Recent decisions</h3></div><span>{items.length} records</span></div><div className="table-wrap"><table><thead><tr><th>Record</th><th>Decision</th><th>Defect type</th><th>Severity</th><th>Operator</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><strong>{item.id}</strong><small>{item.filename}</small></td><td><span className={`table-status ${item.classification}`}>{item.classification}</span></td><td>{formatType(item.defect_type)}</td><td>{item.severity_level} <small>{item.severity_score}</small></td><td>{item.operator}</td></tr>)}</tbody></table>{!items.length && <div className="table-empty">No inspections logged yet.</div>}</div></div>;
}

function AdminView({ user }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ email: '', name: '', role: 'Quality Engineer', password: '' });
  const [message, setMessage] = useState('');
  const headers = { Authorization: `Bearer ${user.token}` };
  const loadUsers = async () => { const response = await fetch(`${API}/api/users`, { headers }); if (response.ok) setUsers((await response.json()).items); };
  useEffect(() => { loadUsers(); }, []);
  const createUser = async (event) => { event.preventDefault(); setMessage(''); const response = await fetch(`${API}/api/users`, { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify(form) }); const data = await response.json(); if (!response.ok) { setMessage(data.detail || 'Could not create user'); return; } setForm({ email: '', name: '', role: 'Quality Engineer', password: '' }); setMessage('User created successfully'); loadUsers(); };
  return <section className="content-column"><div className="page-heading"><div><p className="eyebrow">USER MANAGEMENT / ADMIN</p><h2>People & access</h2><p>Create and review role-based factory accounts.</p></div></div><div className="admin-grid"><form className="chart-card admin-form" onSubmit={createUser}><p className="eyebrow">NEW ACCOUNT</p><label>Name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><label>Email<input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label><label>Role<select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}><option>Quality Engineer</option><option>Factory Supervisor</option><option>Administrator</option></select></label><label>Temporary password<input required minLength="8" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label><button className="primary-button" type="submit">Create account →</button>{message && <p className="error-text">{message}</p>}</form><div className="history-card"><div className="card-heading"><div><p className="eyebrow">DIRECTORY</p><h3>Factory accounts</h3></div><span>{users.length} users</span></div><div className="table-wrap"><table><thead><tr><th>Name</th><th>Role</th><th>Status</th></tr></thead><tbody>{users.map((person) => <tr key={person.email}><td><strong>{person.name}</strong><small>{person.email}</small></td><td>{person.role}</td><td><span className="table-status good">{person.active ? 'active' : 'disabled'}</span></td></tr>)}</tbody></table></div></div></div></section>;
}

function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('inspect');
  const [analytics, setAnalytics] = useState({ total_inspections: 0, good_count: 0, bad_count: 0, pass_rate: 0, average_severity: 0, defect_counts: { contamination: 0, broken_small: 0, broken_large: 0 }, recent: [] });
  const refresh = async () => { const response = await fetch(`${API}/api/analytics`, { headers: { Authorization: `Bearer ${user?.token}` } }); if (response.ok) setAnalytics(await response.json()); };
  useEffect(() => { if (user) refresh(); }, [user]);
  if (!user) return <Login onLogin={setUser} />;
  return <div className="app-shell"><header className="topbar"><div className="brand"><div className="brand-mark small">VI</div><div><strong>VisionInspect <em>AI</em></strong><small>QUALITY OPERATIONS</small></div></div><nav><button className={view === 'inspect' ? 'active' : ''} onClick={() => setView('inspect')}>Inspect</button><button className={view === 'analytics' ? 'active' : ''} onClick={() => setView('analytics')}>Analytics</button>{user.role === 'Administrator' && <button className={view === 'admin' ? 'active' : ''} onClick={() => setView('admin')}>People</button>}</nav><div className="user-menu"><span className="avatar">{user.name.split(' ').map((part) => part[0]).join('')}</span><div><strong>{user.name}</strong><small>{user.role}</small></div><button title="Sign out" onClick={() => setUser(null)}>↗</button></div></header><main className="main-content">{view === 'inspect' ? <InspectionView user={user} onComplete={refresh} /> : view === 'analytics' ? <AnalyticsView analytics={analytics} history={analytics.recent} onRefresh={refresh} /> : <AdminView user={user} />}</main><footer><span>VISIONINSPECT AI · INDUSTRIAL QUALITY SYSTEM</span><span>● API CONNECTED · v1.0</span></footer></div>;
}

export default App;
