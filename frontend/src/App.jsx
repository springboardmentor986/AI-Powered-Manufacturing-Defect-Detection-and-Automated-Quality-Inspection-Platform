import React, { useState, useEffect } from 'react'

function App() {
  const [email, setEmail] = useState('engineer@gmail.com')
  const [password, setPassword] = useState('password123')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [loggedIn, setLoggedIn] = useState(false)
  const [user, setUser] = useState(null)
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [inspections, setInspections] = useState([])
  const [stats, setStats] = useState({ total: 0, defective: 0, passed: 0, failed: 0, defect_rate: 0, pass_rate: 0, by_severity: {} })
  const [products, setProducts] = useState([])
  const [selectedProduct, setSelectedProduct] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [categoryImages, setCategoryImages] = useState([])
  const [selectedInspection, setSelectedInspection] = useState(null)

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
        setLoggedIn(true)
        fetchInspections(); fetchStats(); fetchProducts(); fetchCategories()
      } catch (e) {}
    }
  }, [])

  const fetchInspections = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('http://127.0.0.1:8000/inspections/', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) setInspections(await res.json())
    } catch (e) {}
  }

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('http://127.0.0.1:8000/inspections/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) setStats(await res.json())
    } catch (e) {}
  }

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('http://127.0.0.1:8000/auth/products', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) setProducts(await res.json())
    } catch (e) {
      setProducts([
        { id: 'MC-001', product_name: 'Metal Component', product_code: 'MC-001' },
        { id: 'PP-001', product_name: 'Plastic Part', product_code: 'PP-001' },
        { id: 'EB-001', product_name: 'Electronic Board', product_code: 'EB-001' },
      ])
    }
  }

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('http://127.0.0.1:8000/dataset/categories', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setCategories(data.categories || [])
      }
    } catch (e) {}
  }

  const fetchCategoryImages = async (category) => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`http://127.0.0.1:8000/dataset/category/${category}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setCategoryImages(data.images || [])
      }
    } catch (e) {}
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const formData = new URLSearchParams()
      formData.append('email', email)
      formData.append('password', password)
      const res = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setLoggedIn(true)
        setUser(data.user)
        setMessage('✅ Login successful!')
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        fetchInspections(); fetchStats(); fetchProducts(); fetchCategories()
      } else {
        setMessage('❌ Login failed')
      }
    } catch (error) {
      setMessage('❌ Cannot connect to server')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setLoggedIn(false); setUser(null); setMessage(''); setCurrentPage('dashboard')
    localStorage.removeItem('token'); localStorage.removeItem('user')
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
    }
  }

  const handleInspect = async (e) => {
    e.preventDefault()
    if (!selectedProduct || !selectedFile) {
      setResult({ type: 'error', message: 'Please select product and image' })
      return
    }
    setLoading(true); setResult(null)
    try {
      const formData = new FormData()
      formData.append('product_id', selectedProduct)
      formData.append('image', selectedFile)
      const token = localStorage.getItem('token')
      
      const res = await fetch('http://127.0.0.1:8000/inspections/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })
      
      const data = await res.json()
      if (res.ok) {
        setResult({ type: 'success', data })
        fetchInspections(); fetchStats()
        setSelectedProduct(''); setSelectedFile(null); setPreview(null)
        const fi = document.getElementById('fileInput')
        if (fi) fi.value = ''
      } else {
        setResult({ type: 'error', message: data.detail || 'Inspection failed' })
      }
    } catch (error) {
      setResult({ type: 'error', message: '❌ Error: ' + error.message })
    } finally {
      setLoading(false)
    }
  }

  const getBadge = (v) => {
    const c = { pending: 'badge-pending', processing: 'badge-processing', completed: 'badge-completed',
      passed: 'badge-passed', failed: 'badge-failed', Critical: 'badge-failed', High: 'badge-pending',
      Medium: 'badge-processing', Low: 'badge-passed', PASSED: 'badge-passed', FAILED: 'badge-failed' }
    return <span className={c[v] || 'badge-pending'}>{v}</span>
  }

  const Navbar = () => (
    <nav className="nav">
      <div className="nav-left">
        <div className="logo">V</div>
        <div>
          <h1 className="nav-title">VisionInspect <span style={{color:'#3b82f6'}}>AI</span></h1>
          <span className="nav-sub">MILESTONE 2</span>
        </div>
      </div>
      <div className="nav-right">
        <span className="nav-user">{user?.name}</span>
        <span className="nav-role">{user?.role?.replace('_', ' ')}</span>
        <button onClick={handleLogout} className="btn-logout">Logout</button>
      </div>
    </nav>
  )

  const Sidebar = () => {
    const isSup = user?.role === 'supervisor'
    const items = [
      { id: 'dashboard', label: 'Dashboard', icon: '📊' },
      ...(isSup ? [] : [{ id: 'inspect', label: 'AI Inspect', icon: '🔍' }]),
      { id: 'inspections', label: 'History', icon: '📋' },
      { id: 'dataset', label: 'Dataset', icon: '🗄️' }
    ]
    return (
      <div className="sidebar">
        {items.map(i => (
          <button key={i.id} className={`side-item ${currentPage === i.id ? 'active' : ''}`}
            onClick={() => {
              setCurrentPage(i.id)
              if (i.id === 'dashboard') { fetchStats(); fetchInspections() }
              if (i.id === 'dataset') fetchCategories()
              if (i.id === 'inspect') fetchProducts()
              if (i.id === 'inspections') fetchInspections()
            }}>
            <span className="side-icon">{i.icon}</span>{i.label}
          </button>
        ))}
      </div>
    )
  }

  const DashboardPage = () => {
    const isSup = user?.role === 'supervisor'
    return (
      <div className="page">
        <div className="page-header">
          <h2>{isSup ? 'Production Overview' : 'Dashboard'}</h2>
          <p>AI Powered defect detection analytics</p>
        </div>

        <div className="stat-grid">
          <div className="stat-card" style={{borderColor:'#3b82f633'}}>
            <div className="stat-label">Total Inspections</div>
            <div className="stat-value" style={{color:'#3b82f6'}}>{stats.total}</div>
          </div>
          <div className="stat-card" style={{borderColor:'#f8717133'}}>
            <div className="stat-label">Defective</div>
            <div className="stat-value" style={{color:'#f87171'}}>{stats.defective}</div>
          </div>
          <div className="stat-card" style={{borderColor:'#34d39933'}}>
            <div className="stat-label">Passed</div>
            <div className="stat-value" style={{color:'#34d399'}}>{stats.passed}</div>
          </div>
          <div className="stat-card" style={{borderColor:'#fbbf2433'}}>
            <div className="stat-label">Failed</div>
            <div className="stat-value" style={{color:'#fbbf24'}}>{stats.failed}</div>
          </div>
        </div>

        <div className="rate-grid">
          <div className="rate-card">
            <div className="rate-label">Defect Rate</div>
            <div className="rate-value" style={{color:'#f87171'}}>{stats.defect_rate}%</div>
          </div>
          <div className="rate-card">
            <div className="rate-label">Pass Rate</div>
            <div className="rate-value" style={{color:'#34d399'}}>{stats.pass_rate}%</div>
          </div>
        </div>

        {stats.by_severity && (
          <div className="section">
            <h3 className="section-title">Severity Distribution</h3>
            <div className="severity-grid">
              {['Critical', 'High', 'Medium', 'Low'].map(s => (
                <div key={s} className="sev-card">
                  <div className="sev-label">{s}</div>
                  <div className="sev-count">{stats.by_severity[s] || 0}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!isSup && (
          <div className="section">
            <h3 className="section-title">⚡ Quick Actions</h3>
            <div className="btn-row">
              <button className="btn-primary" onClick={() => { setCurrentPage('inspect'); setResult(null) }}>🔍 Start Inspection</button>
              <button className="btn-secondary" onClick={() => { setCurrentPage('inspections'); fetchInspections() }}>📋 View History</button>
            </div>
          </div>
        )}
      </div>
    )
  }

  const InspectPage = () => (
    <div className="page">
      <div className="page-header">
        <h2>🔍 AI Inspection</h2>
        <p>Upload image for AI-powered defect detection</p>
      </div>

      <div className="inspect-wrapper">
        <form onSubmit={handleInspect} className="form-card">
          <div className="form-group">
            <label className="form-label">Select Product</label>
            <select className="form-select" value={selectedProduct} onChange={e => setSelectedProduct(e.target.value)} required>
              <option value="">Choose product...</option>
              {products.map(p => <option key={p.id} value={p.id}>{p.product_name} ({p.product_code})</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Upload Image</label>
            <div className="dropzone">
              {preview ? (
                <div>
                  <img src={preview} alt="preview" className="preview-img" />
                  <p className="file-name">📎 {selectedFile?.name}</p>
                  <button type="button" className="btn-remove" onClick={() => { setPreview(null); setSelectedFile(null); setResult(null) }}>✕ Remove</button>
                </div>
              ) : (
                <div>
                  <p className="drop-text">📁 Drop image here or click</p>
                  <p className="drop-sub">JPG, PNG, BMP, TIFF</p>
                  <input id="fileInput" type="file" onChange={handleFileChange} accept="image/*" className="file-input" />
                </div>
              )}
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary btn-full">
            {loading ? '🤖 AI Analyzing...' : '🚀 Run AI Inspection'}
          </button>
        </form>

        {result?.type === 'success' && <ResultDisplay data={result.data} previewUrl={preview} />}
        {result?.type === 'error' && (
          <div className="error-box"><p>{result.message}</p></div>
        )}
      </div>
    </div>
  )

  const ResultDisplay = ({ data, previewUrl }) => {
    const ai = data.ai_detection || {}
    const qa = data.quality_analysis || {}
    const detected = ai.defect_detected

    return (
      <div className="result-wrapper">
        <div className="result-header" style={{ background: detected ? 'rgba(239,68,68,0.08)' : 'rgba(34,197,94,0.08)',
          borderColor: detected ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)' }}>
          <div className="result-icon">{detected ? '❌' : '✅'}</div>
          <h2 className="result-title" style={{ color: detected ? '#f87171' : '#34d399' }}>
            {detected ? 'DEFECT DETECTED' : 'PASSED'}
          </h2>
          <p className="result-id">Inspection #{String(data.inspection?.id || '').padStart(4, '0').slice(-4)}</p>
        </div>

        <div className="section">
          <h3 className="section-title">📸 Image Comparison</h3>
          <div className="image-compare">
            <div className="img-box">
              <p className="img-label">Original</p>
              <img src={previewUrl || ''} alt="original" className="compare-img" />
            </div>
            <div className="img-arrow">→</div>
            <div className="img-box">
              <p className="img-label">AI Detection Result</p>
              <img src={data.result_image_url} alt="result" className="compare-img"
                onError={e => e.target.src = previewUrl || ''} />
              {detected && ai.location && (
                <div className="loc-info">
                  <p>X: {ai.location.x} | Y: {ai.location.y}</p>
                  <p>W: {ai.location.width} | H: {ai.location.height}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">⚙️ Image Preprocessing</h3>
          <div className="steps-grid">
            {(data.preprocessing?.steps || []).map((s, i) => (
              <div key={i} className="step-item">
                <span className="step-check">✓</span>
                <span>{s}</span>
              </div>
            ))}
          </div>
          <div className="preprocess-info">
            <span>Original: {data.preprocessing?.original_size}</span>
            <span>→</span>
            <span>Processed: {data.preprocessing?.processed_size}</span>
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">📊 Image Quality Analysis</h3>
          <div className="qa-grid">
            <QACard label="Resolution" value={`${qa.resolution?.width}×${qa.resolution?.height}`} status={qa.resolution?.status} />
            <QACard label="Brightness" value={qa.brightness?.value} status={qa.brightness?.status} />
            <QACard label="Sharpness" value={qa.sharpness?.value} status={qa.sharpness?.status} />
            <QACard label="Noise" value={qa.noise?.value} status={qa.noise?.status} />
          </div>
          <div className="qa-overall">
            <div className="qa-score">Overall: {qa.overall?.score}%</div>
            <div className="qa-status">{qa.overall?.status}</div>
            <p className="qa-rec">{qa.overall?.recommendation}</p>
          </div>
        </div>

        {detected && (
          <div className="section">
            <h3 className="section-title">🤖 AI Detection Results</h3>
            <div className="ai-grid">
              <InfoBox label="Defect Type" value={ai.defect_type} color="#f87171" />
              <InfoBox label="Confidence" value={`${Math.round((ai.confidence || 0) * 100)}%`} color="white" />
              <InfoBox label="Severity Score" value={`${ai.severity_score}/100`} color="#fbbf24" />
              <InfoBox label="Severity Level" value={ai.severity_level} color="#f87171" />
            </div>

            {ai.all_defects && ai.all_defects.length > 0 && (
              <div className="all-defects">
                <p className="all-defects-title">All Detected Defects:</p>
                {ai.all_defects.map((d, i) => (
                  <div key={i} className="defect-item">
                    <span>• {d.type}</span>
                    <span style={{color:'#94a3b8'}}>{Math.round(d.confidence * 100)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {ai.timing && (
          <div className="section">
            <h3 className="section-title">⚡ Processing Performance</h3>
            <div className="timing-grid">
              <div className="timing-box">
                <p className="timing-label">Preprocessing</p>
                <p className="timing-value">{ai.timing.preprocessing_ms} ms</p>
              </div>
              <div className="timing-box">
                <p className="timing-label">AI Inference</p>
                <p className="timing-value">{ai.timing.inference_ms} ms</p>
              </div>
              <div className="timing-box">
                <p className="timing-label">Total</p>
                <p className="timing-value" style={{color:'#60a5fa'}}>{ai.timing.total_ms} ms</p>
              </div>
            </div>
          </div>
        )}

        {ai.model_info && (
          <div className="section">
            <h3 className="section-title">🤖 Model Information</h3>
            <div className="model-grid">
              <div className="model-item"><span className="model-label">Model</span><span>{ai.model_info.name}</span></div>
              <div className="model-item"><span className="model-label">Version</span><span>{ai.model_info.version}</span></div>
              <div className="model-item"><span className="model-label">Input Size</span><span>{ai.model_info.input_size}</span></div>
              <div className="model-item"><span className="model-label">Threshold</span><span>{ai.model_info.confidence_threshold}</span></div>
            </div>
          </div>
        )}

        <div className={`decision-box ${detected ? 'decision-fail' : 'decision-pass'}`}>
          <h3 className="decision-title">QUALITY DECISION</h3>
          <div className="decision-result" style={{ color: detected ? '#f87171' : '#34d399' }}>
            {detected ? '❌ FAIL' : '✅ PASS'}
          </div>
          <p className="decision-reason">{ai.recommendation || 'No critical defect detected.'}</p>
        </div>

        <button className="btn-secondary" onClick={() => { setCurrentPage('inspections'); fetchInspections() }}>
          📋 View All Inspections
        </button>
      </div>
    )
  }

  const QACard = ({ label, value, status }) => {
    const isGood = status === 'Good' || status === 'Low' || status === 'Suitable'
    return (
      <div className="qa-card">
        <p className="qa-label">{label}</p>
        <p className="qa-value">{value}</p>
        <p className="qa-status-txt" style={{ color: isGood ? '#34d399' : '#fbbf24' }}>
          {isGood ? '✓' : '⚠'} {status}
        </p>
      </div>
    )
  }

  const InfoBox = ({ label, value, color }) => (
    <div className="info-box">
      <p className="info-label">{label}</p>
      <p className="info-value" style={{ color }}>{value || '-'}</p>
    </div>
  )

  const InspectionsPage = () => (
    <div className="page">
      <div className="page-header">
        <h2>📋 Inspection History</h2>
        <p>All AI inspection records</p>
      </div>

      <div className="section">
        {inspections.length === 0 ? (
          <p className="empty">No inspections yet. Run your first AI inspection!</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th><th>Image</th><th>Product</th><th>Defect</th>
                <th>Confidence</th><th>Severity</th><th>Decision</th><th>Date</th>
              </tr>
            </thead>
            <tbody>
              {inspections.map(i => (
                <tr key={i.id} onClick={() => setSelectedInspection(i)}>
                  <td className="td-id">#{String(i.id).padStart(4, '0').slice(-4)}</td>
                  <td>{i.image_filename}</td>
                  <td>{i.product_name || '-'}</td>
                  <td>{i.defect_detected ? <span style={{color:'#f87171', fontWeight:600}}>{i.defect_type}</span> : <span style={{color:'#34d399'}}>None</span>}</td>
                  <td>{i.confidence ? `${Math.round(i.confidence * 100)}%` : '-'}</td>
                  <td>{i.severity_level && i.severity_level !== 'None' ? getBadge(i.severity_level) : '-'}</td>
                  <td>{i.decision ? getBadge(i.decision) : '-'}</td>
                  <td className="td-date">{new Date(i.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedInspection && (
        <div className="modal-overlay" onClick={() => setSelectedInspection(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🔍 Inspection #{String(selectedInspection.id).padStart(4, '0').slice(-4)}</h3>
              <button className="btn-close" onClick={() => setSelectedInspection(null)}>✕</button>
            </div>

            <div className="modal-body">
              <p><strong>Product:</strong> {selectedInspection.product_name}</p>
              <p><strong>Image:</strong> {selectedInspection.image_filename}</p>
              <p><strong>Date:</strong> {new Date(selectedInspection.created_at).toLocaleString()}</p>

              <div className={`modal-result ${selectedInspection.defect_detected ? 'result-fail' : 'result-pass'}`}>
                <p style={{ color: selectedInspection.defect_detected ? '#f87171' : '#34d399', fontSize: 18, fontWeight: 600 }}>
                  {selectedInspection.defect_detected ? '❌ DEFECT DETECTED' : '✅ PASSED'}
                </p>
                {selectedInspection.defect_detected && (
                  <>
                    <p><strong>Type:</strong> {selectedInspection.defect_type}</p>
                    <p><strong>Confidence:</strong> {Math.round((selectedInspection.confidence || 0) * 100)}%</p>
                    <p><strong>Severity:</strong> {selectedInspection.severity_score}/100 ({selectedInspection.severity_level})</p>
                    <p><strong>Recommendation:</strong> {selectedInspection.recommendation}</p>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const DatasetPage = () => (
    <div className="page">
      <div className="page-header">
        <h2>🗄️ MVTec AD Dataset</h2>
        <p>Browse industrial anomaly detection dataset</p>
      </div>

      <div className="dataset-layout">
        <div className="dataset-sidebar">
          <h4 className="dataset-heading">📁 Categories</h4>
          {categories.map(c => (
            <button key={c} className={`cat-btn ${selectedCategory === c ? 'active' : ''}`}
              onClick={() => { setSelectedCategory(c); fetchCategoryImages(c) }}>
              {c.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="dataset-main">
          {selectedCategory ? (
            <>
              <h4 className="dataset-title">📷 {selectedCategory.replace('_', ' ')}</h4>
              {categoryImages.length === 0 ? (
                <p className="empty">No images found</p>
              ) : (
                <>
                  <p className="dataset-count">{categoryImages.length} images</p>
                  <div className="img-grid">
                    {categoryImages.slice(0, 20).map((img, idx) => (
                      <div key={idx} className="img-cell">
                        <img src={`http://127.0.0.1:8000/dataset/image/${selectedCategory}/${img}`}
                          alt={img} className="grid-img"
                          onError={e => { e.target.style.display='none'; e.target.parentElement.innerHTML=`<div class="no-img">📷<br>${img}</div>` }} />
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          ) : (
            <p className="empty">Select a category to view images</p>
          )}
        </div>
      </div>
    </div>
  )

  if (loggedIn && user) {
    return (
      <div className="app">
        <Navbar />
        <div className="app-body">
          <Sidebar />
          <div className="app-content">
            {currentPage === 'dashboard' && <DashboardPage />}
            {currentPage === 'inspect' && <InspectPage />}
            {currentPage === 'inspections' && <InspectionsPage />}
            {currentPage === 'dataset' && <DatasetPage />}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">V</div>
        <h1 className="login-title">VisionInspect <span style={{color:'#3b82f6'}}>AI</span></h1>
        <p className="login-sub">Manufacturing Quality Control</p>
        <span className="login-badge">Milestone 2</span>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" className="form-input" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input type="password" className="form-input" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" disabled={loading} className="btn-primary btn-full">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {message && <div className="login-msg">{message}</div>}

        <div className="login-demo">
          <p>🔵 engineer@gmail.com / password123</p>
          <p>🟣 supervisor@gmail.com / password123</p>
        </div>
      </div>
    </div>
  )
}

export default App
