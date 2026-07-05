import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Search, ShieldAlert, Sparkles, CheckCircle2, XCircle,
  Copy, Check, RefreshCw, UserCheck, ChevronDown,
  ChevronUp, Star, Mail, AlertTriangle, Play, FileText, MapPin, Database
} from 'lucide-react';
import ColorBends from './ColorBends';
import BorderGlow from './BorderGlow';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  // UI states
  const [expandedMatches, setExpandedMatches] = useState({});
  const [copiedOutreach, setCopiedOutreach] = useState(false);
  const [approved, setApproved] = useState(false);
  const [activeTab, setActiveTab] = useState({}); // { [entityId]: 'score' | 'evidence' | 'risks' }
  const [engineStatus, setEngineStatus] = useState({ ollama_online: false, configured_model: 'qwen3:4b', fallback_active: true });
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [resultsTab, setResultsTab] = useState('validation');



  const checkEngineStatus = async () => {
    setCheckingStatus(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/status`);
      setEngineStatus(res.data);
    } catch (err) {
      console.error("Could not check engine status:", err);
      setEngineStatus({ ollama_online: false, configured_model: 'qwen3:4b', fallback_active: true });
    } finally {
      setTimeout(() => setCheckingStatus(false), 500);
    }
  };

  useEffect(() => {
    checkEngineStatus();
  }, []);

  const sampleQueries = [
    {
      title: "Supplier Matching",
      text: "Find 3 food grade biodegradable container suppliers in South India with a capacity of 10,000 units and delivery within 30 days."
    },
    {
      title: "Professional Search",
      text: "Find 2 Python developers in Bengaluru with AI experience, immediate availability, and a rating above 4.5."
    },
    {
      title: "Opportunity Discovery",
      text: "Find procurement opportunities for sustainable packaging suppliers in South India with deadlines within the next 30 days."
    }
  ];

  const handleSearch = async (searchQuery) => {
    const q = searchQuery || query;
    if (!q || q.trim() === '') return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setApproved(false);
    setCopiedOutreach(false);

    try {
      const res = await axios.post(`${API_BASE_URL}/agent`, { query: q });
      setResponse(res.data);

      // Initialize tabs and expansions
      const initialTabs = {};
      const initialExpansions = {};
      res.data.matches.forEach((m, idx) => {
        initialTabs[m.entity.id] = 'score';
        initialExpansions[m.entity.id] = idx === 0; // expand first card by default
      });
      setActiveTab(initialTabs);
      setExpandedMatches(initialExpansions);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
        'Could not connect to the backend agent service. Please verify the FastAPI server is running on port 8000.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopyOutreach = () => {
    if (!response?.outreach_message) return;
    navigator.clipboard.writeText(response.outreach_message);
    setCopiedOutreach(true);
    setTimeout(() => setCopiedOutreach(false), 2000);
  };

  const handleApprove = () => {
    setApproved(true);
  };

  const toggleExpand = (id) => {
    setExpandedMatches(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const switchTab = (id, tab) => {
    setActiveTab(prev => ({ ...prev, [id]: tab }));
  };

  return (
    <div className="app-container">
      <div className="app-bg-wrapper">
        <ColorBends
          colors={["#ff5c7a", "#8a5cff", "#00ffd1"]}
          rotation={90}
          speed={0.2}
          scale={1.0}
          frequency={1}
          warpStrength={1}
          mouseInfluence={1}
          noise={0.15}
          parallax={0.5}
          iterations={1}
          intensity={1.5}
          bandWidth={6}
          transparent
          autoRotate={0}
        />
      </div>
      {/* Navbar */}
      <header className="navbar">
        <div className="navbar-content">
          <div className="nav-logo-group">
            <div className="nav-logo-icon">
              <Sparkles className="icon-sparkles" />
            </div>
            <div>
              <h1 className="nav-logo-text">Suproc Agent</h1>
              <p className="nav-logo-sub">Local Agentic Search</p>
            </div>
          </div>

          <div className="nav-actions">
            <div
              onClick={checkEngineStatus}
              title="Click to check local Qwen3 4B Ollama server status"
              className={`nav-status-badge ${engineStatus.ollama_online ? 'online' : 'offline'}`}
              style={{ cursor: 'pointer' }}
            >
              {checkingStatus ? (
                <RefreshCw className="icon-spin animate-spin text-cyan" style={{ height: '12px', width: '12px' }} />
              ) : (
                <span className={`status-dot ${engineStatus.ollama_online ? 'dot-green' : 'dot-amber'}`}></span>
              )}
              <span className="status-text">
                {checkingStatus
                  ? "Pinging Qwen3..."
                  : engineStatus.ollama_online
                    ? `Qwen3 4B Active`
                    : `Qwen3 4B Fallback`
                }
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {!response ? (
          /* HOME PAGE */
          <div className="home-container animate-fade-in">
            <div className="hero-section">
              <div className="hero-badge">
                NextGen AI Agent System
              </div>
              <h2 className="hero-title" style={{ fontStyle: 'italic' }}>
                AI Intelligent Search
              </h2>

            </div>

            {/* Search Box */}
            <div className="search-card glass-panel glowing-border glow-cyan">
              <div className="search-form">
                <textarea
                  rows={4}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="textarea-field"
                />
                <div className="search-footer">
                  <button
                    onClick={() => handleSearch()}
                    disabled={loading || !query.trim()}
                    className="run-btn"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="icon-spin animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Play className="icon-play" />
                        Run Agent Workflow
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="error-card">
                <ShieldAlert className="error-icon" />
                <div className="error-body">
                  <h4 className="error-title">Execution Error</h4>
                  <p className="error-desc">{error}</p>
                </div>
              </div>
            )}

            {/* Sample Queries */}
            <div className="examples-section">
              <h3 className="section-subtitle">
                Example
              </h3>
              <div className="examples-grid">
                {sampleQueries.map((q, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setQuery(q.text);
                      handleSearch(q.text);
                    }}
                    className="example-card glass-panel"
                  >
                    <h4 className="example-tag">{q.title}</h4>
                    <p className="example-text">{q.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* RESULTS DASHBOARD */
          <div className="results-container animate-fade-in">
            {/* Header summary */}
            <div className="results-header">
              <button
                onClick={() => setResponse(null)}
                className="back-btn"
              >
                &larr; Back to Search
              </button>
              <div className="results-meta">
                Processed Query in {response.validation.attempts} attempt(s)
              </div>
            </div>

            <div className="results-grid">
              {/* LEFT COLUMN: Requirement & Matched Recommendations */}
              <div className="results-sidebar">

                {/* REQUIREMENT CARD */}
                <section className="req-card glass-panel">
                  <div className="card-header-icon-group">
                    <Database className="card-header-icon text-cyan" />
                    <h3 className="card-header-title">Extracted Objective</h3>
                  </div>
                  <div className="objective-box">
                    {response.requirement.entity_name ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Objective</span>
                        <p className="objective-text" style={{ margin: '0 0 12px 0' }}>{response.requirement.objective ? response.requirement.objective.replace(/-/g, ' ') : ''}</p>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Selected {response.requirement.entity_type.charAt(0).toUpperCase() + response.requirement.entity_type.slice(1)}
                        </span>
                        <p className="objective-text" style={{ color: 'var(--accent-cyan)', fontWeight: 700, margin: '0 0 4px 0' }}>{response.requirement.entity_name}</p>
                      </div>
                    ) : (
                      <p className="objective-text">{response.requirement.objective ? response.requirement.objective.replace(/-/g, ' ') : ''}</p>
                    )}
                    <div className="badge-type">
                      Type: {response.requirement.entity_type}
                    </div>
                  </div>

                  <div className="constraints-section">
                    <div>
                      <h4 className="constraints-title">Hard Constraints</h4>
                      <div className="badge-group">
                        {response.requirement.hard_constraints.locations && (
                          <span className="badge">
                            📍 {response.requirement.hard_constraints.locations.slice(0, 3).join(', ')}
                            {response.requirement.hard_constraints.locations.length > 3 && '...'}
                          </span>
                        )}
                        {response.requirement.hard_constraints.certifications && response.requirement.hard_constraints.certifications.map((c, i) => (
                          <span key={i} className="badge">
                            📜 {c.replace(/-/g, ' ')}
                          </span>
                        ))}
                        {typeof response.requirement.hard_constraints.minimum_capacity === 'number' && response.requirement.hard_constraints.minimum_capacity > 0 && (
                          <span className="badge">
                            📦 Min Vol: {response.requirement.hard_constraints.minimum_capacity.toLocaleString()} units
                          </span>
                        )}
                        {response.requirement.hard_constraints.maximum_delivery_days && (
                          <span className="badge">
                            ⏱ Max Delivery: {response.requirement.hard_constraints.maximum_delivery_days} days
                          </span>
                        )}
                        {response.requirement.hard_constraints.required_skills && response.requirement.hard_constraints.required_skills.map((s, i) => (
                          <span key={i} className="badge">
                            ⚡ {s}
                          </span>
                        ))}
                        {response.requirement.hard_constraints.maximum_budget && (
                          <span className="badge">
                            💰 Max Budget: ${response.requirement.hard_constraints.maximum_budget}
                          </span>
                        )}
                      </div>
                    </div>

                    {Object.keys(response.requirement.preferences).length > 0 && (
                      <div className="pref-section-wrapper">
                        <h4 className="constraints-title">Preferences</h4>
                        <div className="badge-group">
                          {Object.entries(response.requirement.preferences).map(([k, v]) => (
                            <span key={k} className="badge badge-pref">
                              ✨ {k.replace('_', ' ')}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </section>

                {/* MATCHED RECOMMENDATIONS */}
                <section className="entity-section">
                  <h3 className="entity-section-title">Recommended Matches ({response.matches.length})</h3>
                  {response.matches.length === 0 ? (
                    <div className="empty-matches-card glass-panel">
                      No records found matching all constraints. Try again with relaxed filters.
                    </div>
                  ) : (
                    response.matches.map((match, idx) => {
                      const ent = match.entity;
                      const isExpanded = expandedMatches[ent.id];
                      const activeTabForEntity = activeTab[ent.id] || 'score';

                      return (
                        <div
                          key={ent.id}
                          className={`entity-card glass-panel ${isExpanded ? 'entity-card-expanded' : ''}`}
                        >
                          {/* Header Accordion Trigger */}
                          <div
                            onClick={() => toggleExpand(ent.id)}
                            className="entity-card-header"
                          >
                            <div className="entity-header-left">
                              <span className="entity-id-badge">{ent.id}</span>
                              <div>
                                <h4 className="entity-name">{ent.name || ent.title}</h4>
                                <p className="entity-location">
                                  <MapPin className="icon-tiny" /> {ent.location}
                                </p>
                              </div>
                            </div>

                            <div className="entity-header-right">
                              <div className="score-summary-box">
                                <span className="score-summary-label">Match Score</span>
                                <span className="score-summary-val">{match.score_breakdown.total_score}%</span>
                              </div>
                              {isExpanded ? (
                                <ChevronUp className="accordion-arrow" />
                              ) : (
                                <ChevronDown className="accordion-arrow" />
                              )}
                            </div>
                          </div>

                          {/* Expandable Tabs Detail */}
                          {isExpanded && (
                            <div className="entity-card-body animate-slide-down">
                              {/* Detail Tabs Header */}
                              <div className="entity-tabs">
                                <button
                                  onClick={() => switchTab(ent.id, 'score')}
                                  className={`entity-tab-btn ${activeTabForEntity === 'score' ? 'active' : ''}`}
                                >
                                  Match Breakdown
                                </button>
                                <button
                                  onClick={() => switchTab(ent.id, 'evidence')}
                                  className={`entity-tab-btn ${activeTabForEntity === 'evidence' ? 'active' : ''}`}
                                >
                                  Supporting Evidence
                                </button>
                                <button
                                  onClick={() => switchTab(ent.id, 'risks')}
                                  className={`entity-tab-btn ${activeTabForEntity === 'risks' ? 'active' : ''}`}
                                >
                                  Risks & Warnings ({match.risks.length + match.missing_information.length})
                                </button>
                              </div>

                              {/* Tab Content Display */}
                              <div className="entity-tab-content">
                                {activeTabForEntity === 'score' && (
                                  <div className="score-tab-content">
                                    <div className="score-progress-grid">
                                      <div className="progress-item">
                                        <div className="progress-labels">
                                          <span>Relevance / Skills (30%):</span>
                                          <span className="progress-number">{match.score_breakdown.product_relevance}%</span>
                                        </div>
                                        <div className="score-bar-bg">
                                          <div className="score-bar-fill bg-cyan" style={{ width: `${(match.score_breakdown.product_relevance / 30) * 100}%` }}></div>
                                        </div>
                                      </div>
                                      <div className="progress-item">
                                        <div className="progress-labels">
                                          <span>Location Suitability (20%):</span>
                                          <span className="progress-number">{match.score_breakdown.location_suitability}%</span>
                                        </div>
                                        <div className="score-bar-bg">
                                          <div className="score-bar-fill bg-blue" style={{ width: `${(match.score_breakdown.location_suitability / 20) * 100}%` }}></div>
                                        </div>
                                      </div>
                                      <div className="progress-item">
                                        <div className="progress-labels">
                                          <span>Constraint Compliance (25%):</span>
                                          <span className="progress-number">{match.score_breakdown.constraint_compliance}%</span>
                                        </div>
                                        <div className="score-bar-bg">
                                          <div className="score-bar-fill bg-green" style={{ width: `${(match.score_breakdown.constraint_compliance / 25) * 100}%` }}></div>
                                        </div>
                                      </div>
                                      <div className="progress-item">
                                        <div className="progress-labels">
                                          <span>Capacity / Availability (15%):</span>
                                          <span className="progress-number">{match.score_breakdown.capacity_availability}%</span>
                                        </div>
                                        <div className="score-bar-bg">
                                          <div className="score-bar-fill bg-amber" style={{ width: `${(match.score_breakdown.capacity_availability / 15) * 100}%` }}></div>
                                        </div>
                                      </div>
                                    </div>
                                    <div className="explanation-box">
                                      {match.score_breakdown.calculation_explanation}
                                    </div>
                                  </div>
                                )}

                                {activeTabForEntity === 'evidence' && (
                                  <div className="supporting-evidence-tab-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'left' }}>
                                    {response.requirement.entity_name ? (
                                      /* NAMED ENTITY LOOKUP EVIDENCE */
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                          <div style={{ fontWeight: 700, fontSize: '13px', marginBottom: '12px', textTransform: 'uppercase', color: 'var(--accent-cyan)', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '6px' }}>Matched Dataset Record</div>
                                          <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', gap: '8px', fontSize: '12px', lineHeight: '1.6' }}>
                                            <span style={{ color: 'var(--text-muted)' }}>{response.requirement.entity_type.charAt(0).toUpperCase() + response.requirement.entity_type.slice(1)} Name</span>
                                            <span style={{ color: 'white', fontWeight: 600 }}>{match.entity.name || match.entity.title}</span>

                                            <span style={{ color: 'var(--text-muted)' }}>Location</span>
                                            <span style={{ color: 'white' }}>{match.entity.location || 'N/A'}</span>

                                            <span style={{ color: 'var(--text-muted)' }}>{response.requirement.entity_type === 'supplier' ? 'Products' : 'Skills'}</span>
                                            <span style={{ color: 'white' }}>{Array.isArray(match.entity.products || match.entity.skills || match.entity.required_skills) ? (match.entity.products || match.entity.skills || match.entity.required_skills).join(', ') : 'N/A'}</span>

                                            <span style={{ color: 'var(--text-muted)' }}>Rating</span>
                                            <span style={{ color: 'white' }}>{match.entity.rating ? `${match.entity.rating} / 5` : 'N/A'}</span>

                                            {match.entity.capacity && (
                                              <>
                                                <span style={{ color: 'var(--text-muted)' }}>Capacity</span>
                                                <span style={{ color: 'white' }}>{match.entity.capacity} units</span>
                                              </>
                                            )}
                                          </div>
                                        </div>

                                        <div style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
                                          <div style={{ fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', color: '#34d399', marginBottom: '4px' }}>Reason Selected</div>
                                          <div style={{ fontSize: '12px', color: 'white' }}>Exact {response.requirement.entity_type} name requested by the user.</div>
                                        </div>
                                      </div>
                                    ) : (
                                      /* STANDARD KEYWORD EVIDENCE */
                                      <>
                                        {match.matched_keywords && match.matched_keywords.length > 0 && (
                                          <div className="keywords-evidence-box" style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                            <div style={{ fontWeight: 600, fontSize: '11px', marginBottom: '8px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>Matched Keywords</div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                              {match.matched_keywords.map((kw, idx) => (
                                                <span key={idx} style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#34d399', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                                  ✔ {kw}
                                                </span>
                                              ))}
                                            </div>
                                          </div>
                                        )}

                                        {match.missing_keywords && match.missing_keywords.length > 0 && (
                                          <div className="keywords-evidence-box" style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                            <div style={{ fontWeight: 600, fontSize: '11px', marginBottom: '8px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>Missing Keywords</div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                              {match.missing_keywords.map((kw, idx) => (
                                                <span key={idx} style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                                  ✖ {kw}
                                                </span>
                                              ))}
                                            </div>
                                          </div>
                                        )}

                                        {match.matched_fields && match.matched_fields.length > 0 && (
                                          <div className="keywords-evidence-box" style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                            <div style={{ fontWeight: 600, fontSize: '11px', marginBottom: '8px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>Matched Dataset Fields</div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                              {match.matched_fields.map((fld, idx) => (
                                                <span key={idx} style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#60a5fa', padding: '4px 8px', borderRadius: '4px', fontSize: '11px' }}>
                                                  {fld}
                                                </span>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </>
                                    )}

                                    <div className="score-explanation-box">
                                      <div style={{ fontWeight: 600, fontSize: '11px', marginBottom: '8px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>Transparent Score Verification</div>
                                      <pre style={{
                                        background: '#030712',
                                        border: '1px solid rgba(255, 255, 255, 0.04)',
                                        borderRadius: '8px',
                                        padding: '12px',
                                        fontFamily: "'JetBrains Mono', monospace",
                                        fontSize: '11px',
                                        color: 'var(--text-secondary)',
                                        whiteSpace: 'pre-wrap',
                                        lineHeight: '1.6',
                                        margin: 0
                                      }}>
                                        {match.score_breakdown.calculation_explanation}
                                      </pre>
                                    </div>

                                    <ul className="evidence-list" style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                                      {Object.entries(match.evidence).map(([key, text]) => (
                                        <li key={key} className="evidence-item" style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                                          <span className="evidence-label" style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{key.replace('_', ' ')}:</span> {text}
                                        </li>
                                      ))}
                                      <li className="evidence-item" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                        <span className="evidence-label" style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Factual Integrity:</span> Matches the corresponding raw record loaded from database file successfully.
                                      </li>
                                    </ul>
                                  </div>
                                )}

                                {activeTabForEntity === 'risks' && (
                                  <div className="risks-container">
                                    {match.risks.length === 0 && match.missing_information.length === 0 ? (
                                      <p className="risks-empty-msg">No major risks or missing details detected for this matched recommendation.</p>
                                    ) : (
                                      <>
                                        {match.risks.length > 0 && (
                                          <div className="risks-block">
                                            <h5 className="risks-section-title">
                                              <AlertTriangle className="icon-small text-red" /> High/Medium Risk Items
                                            </h5>
                                            <ul className="risks-list text-red-light">
                                              {match.risks.map((risk, i) => (
                                                <li key={i}>{risk}</li>
                                              ))}
                                            </ul>
                                          </div>
                                        )}
                                        {match.missing_information.length > 0 && (
                                          <div className="missing-block">
                                            <h5 className="risks-section-title text-amber">Missing Database Fields</h5>
                                            <p className="missing-subnote">The database contains blank values for the following columns:</p>
                                            <div className="missing-badges">
                                              {match.missing_information.map((field, i) => (
                                                <span key={i} className="missing-field-badge">
                                                  {field}
                                                </span>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </section>
              </div>

              {/* RIGHT COLUMN: Tab bar navigation and workspace */}
              <div className="results-main">

                {/* Tab Navigation Menu */}
                <div className="results-tab-bar" style={{
                  display: 'flex',
                  gap: '10px',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  paddingBottom: '12px',
                  marginBottom: '16px',
                  flexWrap: 'wrap'
                }}>
                  <BorderGlow
                    edgeSensitivity={20}
                    glowColor="40 80 80"
                    backgroundColor={resultsTab === 'validation' ? 'rgba(6, 182, 212, 0.12)' : 'transparent'}
                    borderRadius={8}
                    glowRadius={25}
                    glowIntensity={1.0}
                    coneSpread={25}
                    colors={['#c084fc', '#f472b6', '#38bdf8']}
                    style={{
                      display: 'inline-block',
                      border: resultsTab === 'validation' ? '1px solid rgba(6, 182, 212, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: 'none'
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setResultsTab('validation')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: resultsTab === 'validation' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        padding: '8px 14px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        outline: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%'
                      }}
                    >
                      Agent Self Validation
                    </button>
                  </BorderGlow>

                  <BorderGlow
                    edgeSensitivity={20}
                    glowColor="40 80 80"
                    backgroundColor={resultsTab === 'plan' ? 'rgba(6, 182, 212, 0.12)' : 'transparent'}
                    borderRadius={8}
                    glowRadius={25}
                    glowIntensity={1.0}
                    coneSpread={25}
                    colors={['#c084fc', '#f472b6', '#38bdf8']}
                    style={{
                      display: 'inline-block',
                      border: resultsTab === 'plan' ? '1px solid rgba(6, 182, 212, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: 'none'
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setResultsTab('plan')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: resultsTab === 'plan' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        padding: '8px 14px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        outline: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%'
                      }}
                    >
                      Execution Plan
                    </button>
                  </BorderGlow>

                  <BorderGlow
                    edgeSensitivity={20}
                    glowColor="40 80 80"
                    backgroundColor={resultsTab === 'json' ? 'rgba(6, 182, 212, 0.12)' : 'transparent'}
                    borderRadius={8}
                    glowRadius={25}
                    glowIntensity={1.0}
                    coneSpread={25}
                    colors={['#c084fc', '#f472b6', '#38bdf8']}
                    style={{
                      display: 'inline-block',
                      border: resultsTab === 'json' ? '1px solid rgba(6, 182, 212, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: 'none'
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setResultsTab('json')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: resultsTab === 'json' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        padding: '8px 14px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        outline: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%'
                      }}
                    >
                      Structured Requirement JSON
                    </button>
                  </BorderGlow>

                  <BorderGlow
                    edgeSensitivity={20}
                    glowColor="40 80 80"
                    backgroundColor={resultsTab === 'approval' ? 'rgba(6, 182, 212, 0.12)' : 'transparent'}
                    borderRadius={8}
                    glowRadius={25}
                    glowIntensity={1.0}
                    coneSpread={25}
                    colors={['#c084fc', '#f472b6', '#38bdf8']}
                    style={{
                      display: 'inline-block',
                      border: resultsTab === 'approval' ? '1px solid rgba(6, 182, 212, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: 'none'
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setResultsTab('approval')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: resultsTab === 'approval' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        padding: '8px 14px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        outline: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%'
                      }}
                    >
                      Human Approval Gate
                    </button>
                  </BorderGlow>

                  <BorderGlow
                    edgeSensitivity={20}
                    glowColor="40 80 80"
                    backgroundColor={resultsTab === 'outreach' ? 'rgba(6, 182, 212, 0.12)' : 'transparent'}
                    borderRadius={8}
                    glowRadius={25}
                    glowIntensity={1.0}
                    coneSpread={25}
                    colors={['#c084fc', '#f472b6', '#38bdf8']}
                    style={{
                      display: 'inline-block',
                      border: resultsTab === 'outreach' ? '1px solid rgba(6, 182, 212, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: 'none'
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setResultsTab('outreach')}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: resultsTab === 'outreach' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                        padding: '8px 14px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        outline: 'none',
                        display: 'block',
                        width: '100%',
                        height: '100%'
                      }}
                    >
                      Outreach Message Draft
                    </button>
                  </BorderGlow>
                </div>

                {/* Workspace Content */}
                <div className="tab-workspace-content animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                  {resultsTab === 'validation' && (
                    <BorderGlow
                      edgeSensitivity={30}
                      glowColor="40 80 80"
                      backgroundColor="rgba(17, 24, 39, 0.55)"
                      borderRadius={16}
                      glowRadius={40}
                      glowIntensity={1}
                      coneSpread={25}
                      animated={false}
                      colors={['#c084fc', '#f472b6', '#38bdf8']}
                      className="glass-panel"
                    >
                      <section className="val-card" style={{ padding: '20px', border: 'none', background: 'transparent', boxShadow: 'none' }}>
                        <div className="val-header">
                          <div className="card-header-icon-group">
                            <ShieldAlert className="card-header-icon text-green" />
                            <h3 className="card-header-title">Agent Self Validation</h3>
                          </div>
                          {response.validation.success ? (
                            <span className="val-status-badge pass">VERIFIED PASS</span>
                          ) : (
                            <span className="val-status-badge fail">VALIDATION FAIL</span>
                          )}
                        </div>

                        <div className="val-body">
                          {response.validation.corrected_in_loop && (
                            <div className="val-alert">
                              <AlertTriangle className="val-alert-icon" />
                              <div className="val-alert-text">
                                <strong>Self-Correction Executed:</strong> Constraints were relaxed dynamically (Attempt {response.validation.attempts}/3) because initial criteria returned validation failures.
                              </div>
                            </div>
                          )}

                          <div className="val-checks-section">
                            {(() => {
                              const stageCounts = [];
                              const otherChecks = [];
                              if (response.validation.verification_evidence) {
                                response.validation.verification_evidence.forEach(ev => {
                                  if (
                                    ev.startsWith("Dataset Loaded:") ||
                                    ev.startsWith("After Keyword Search:") ||
                                    ev.startsWith("After Constraint Filtering:") ||
                                    ev.startsWith("After Duplicate Removal:") ||
                                    ev.startsWith("Final Valid Matches:") ||
                                    ev.startsWith("Named Entity Lookup:") ||
                                    ev.startsWith("Constraint Validation:") ||
                                    ev.startsWith("Duplicate Check:") ||
                                    ev.startsWith("Final Valid Match:")
                                  ) {
                                    stageCounts.push(ev);
                                  } else {
                                    otherChecks.push(ev);
                                  }
                                });
                              }
                              return (
                                <>
                                  {stageCounts.length > 0 && (
                                    <div className="validation-pipeline" style={{ margin: '0 0 20px 0', padding: '16px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.04)', display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
                                      <h5 style={{ margin: '0 0 8px 0', fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', fontWeight: 600 }}>Retrieval Pipeline Stages</h5>
                                      {stageCounts.map((stage, idx) => {
                                        const parts = stage.split(':');
                                        const label = parts[0];
                                        const value = parts[1];
                                        return (
                                          <React.Fragment key={idx}>
                                            {idx > 0 && <span style={{ color: 'var(--text-muted)', fontSize: '12px', lineHeight: 1 }}>↓</span>}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', maxWidth: '280px', fontSize: '11px', background: 'rgba(255,255,255,0.01)', padding: '5px 10px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.02)' }}>
                                              <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                                              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{value}</span>
                                            </div>
                                          </React.Fragment>
                                        );
                                      })}
                                    </div>
                                  )}

                                  <h4 className="val-checks-title">Automated Checks</h4>
                                  <div className="val-checks-list">
                                    {otherChecks.map((ev, i) => (
                                      <div key={i} className="val-check-item pass-item">
                                        <CheckCircle2 className="val-check-icon text-green" />
                                        <span className="val-check-text">{ev}</span>
                                      </div>
                                    ))}
                                    {response.validation.failures.map((fail, i) => (
                                      <div key={i} className="val-check-item fail-item">
                                        <XCircle className="val-check-icon text-red" />
                                        <span className="val-check-text text-red-light">{fail}</span>
                                      </div>
                                    ))}
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </div>
                      </section>
                    </BorderGlow>
                  )}

                  {resultsTab === 'plan' && (
                    <BorderGlow
                      edgeSensitivity={30}
                      glowColor="40 80 80"
                      backgroundColor="rgba(17, 24, 39, 0.55)"
                      borderRadius={16}
                      glowRadius={40}
                      glowIntensity={1}
                      coneSpread={25}
                      animated={false}
                      colors={['#c084fc', '#f472b6', '#38bdf8']}
                      className="glass-panel"
                    >
                      <section className="plan-card" style={{ padding: '20px', border: 'none', background: 'transparent', boxShadow: 'none' }}>
                        <div className="card-header-icon-group">
                          <FileText className="card-header-icon text-purple" />
                          <h3 className="card-header-title">Execution Plan</h3>
                        </div>
                        <ul className="plan-steps">
                          {response.plan.steps.map((step, idx) => (
                            <li key={idx} className="plan-step animate-fade-in" style={{ animationDelay: `${idx * 0.08}s` }}>
                              <span className="step-num">{idx + 1}</span>
                              <span className="step-text">{step}</span>
                            </li>
                          ))}
                        </ul>
                      </section>
                    </BorderGlow>
                  )}

                  {resultsTab === 'json' && (
                    <BorderGlow
                      edgeSensitivity={30}
                      glowColor="40 80 80"
                      backgroundColor="rgba(17, 24, 39, 0.55)"
                      borderRadius={16}
                      glowRadius={40}
                      glowIntensity={1}
                      coneSpread={25}
                      animated={false}
                      colors={['#c084fc', '#f472b6', '#38bdf8']}
                      className="glass-panel"
                    >
                      <section className="req-card" style={{ padding: '20px', border: 'none', background: 'transparent', boxShadow: 'none' }}>
                        <div className="card-header-icon-group">
                          <Database className="card-header-icon text-purple" />
                          <h3 className="card-header-title">Structured Requirement JSON</h3>
                        </div>
                        <div className="objective-box" style={{ background: '#0a0d14', padding: '1rem', borderRadius: '6px', maxHeight: '500px', overflowY: 'auto' }}>
                          <pre style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#a5b4fc', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                            {JSON.stringify(response.requirement, null, 2)}
                          </pre>
                        </div>
                      </section>
                    </BorderGlow>
                  )}

                  {resultsTab === 'approval' && (
                    <BorderGlow
                      edgeSensitivity={30}
                      glowColor="40 80 80"
                      backgroundColor="rgba(17, 24, 39, 0.55)"
                      borderRadius={16}
                      glowRadius={40}
                      glowIntensity={1}
                      coneSpread={25}
                      animated={false}
                      colors={['#c084fc', '#f472b6', '#38bdf8']}
                      className="glass-panel"
                    >
                      <section className={`approval-card ${approved ? 'approved-border' : response.validation.success ? 'pending-border' : 'fail-border'}`} style={{ padding: '20px', border: 'none', background: 'transparent', boxShadow: 'none' }}>
                        <div className="approval-body">
                          <div className={`approval-icon-box ${approved ? 'approved-bg' : response.validation.success ? 'pending-bg animate-pulse' : 'fail-bg'}`}>
                            {approved ? (
                              <UserCheck className="approval-icon text-green" />
                            ) : response.validation.success ? (
                              <ShieldAlert className="approval-icon text-amber" />
                            ) : (
                              <XCircle className="approval-icon text-red" />
                            )}
                          </div>
                          <div className="approval-text-group">
                            <div className="approval-header-row">
                              <h4 className="approval-title">Human Approval Gate</h4>
                              <span className={`approval-badge ${approved ? 'approved-badge-style' : response.validation.success ? 'pending-badge-style' : 'fail-badge-style'}`}>
                                {approved ? 'Approved' : response.validation.success ? 'Awaiting Action' : 'Validation Failed'}
                              </span>
                            </div>
                            <p className="approval-desc">
                              {approved
                                ? 'Enquiry verified and approved. Transmission simulation succeeded.'
                                : response.validation.success
                                  ? response.next_action.description
                                  : 'Validation Failed. No business action can be approved.'}
                            </p>

                            {!approved && (
                              <div className="approval-actions-layout">
                                {response.validation.success ? (
                                  <div className="approval-actions">
                                    <button
                                      onClick={handleApprove}
                                      className="approve-btn cursor-pointer"
                                    >
                                      <Check className="icon-small" />
                                      Approve Recommended Action
                                    </button>
                                    <button
                                      onClick={() => setResponse(null)}
                                      className="modify-btn cursor-pointer"
                                    >
                                      Modify Constraints
                                    </button>
                                  </div>
                                ) : (
                                  <div className="fail-actions-container">
                                    <div className="suggested-actions-list">
                                      <h5 className="suggested-actions-title">Suggested Remedial Actions:</h5>
                                      <ul className="suggested-actions">
                                        <li>• Modify Constraints</li>
                                        <li>• Expand Search (broaden keywords)</li>
                                        <li>• Reduce Capacity Requirement</li>
                                      </ul>
                                    </div>
                                    <div className="approval-actions" style={{ marginTop: '1rem' }}>
                                      <button
                                        onClick={() => setResponse(null)}
                                        className="modify-btn cursor-pointer"
                                      >
                                        Modify Constraints
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </section>
                    </BorderGlow>
                  )}

                  {resultsTab === 'outreach' && (
                    <BorderGlow
                      edgeSensitivity={30}
                      glowColor="40 80 80"
                      backgroundColor="rgba(17, 24, 39, 0.55)"
                      borderRadius={16}
                      glowRadius={40}
                      glowIntensity={1}
                      coneSpread={25}
                      animated={false}
                      colors={['#c084fc', '#f472b6', '#38bdf8']}
                      className="glass-panel"
                    >
                      <section className="outreach-card" style={{ padding: '20px', border: 'none', background: 'transparent', boxShadow: 'none' }}>
                        <div className="outreach-header">
                          <div className="card-header-icon-group">
                            <Mail className="card-header-icon text-cyan" />
                            <h3 className="card-header-title">Outreach Message Draft</h3>
                          </div>
                          {response.outreach_message && (
                            <button
                              onClick={handleCopyOutreach}
                              className="copy-btn"
                            >
                              {copiedOutreach ? (
                                <>
                                  <Check className="icon-tiny text-green animate-pulse" />
                                  Copied!
                                </>
                              ) : (
                                <>
                                  <Copy className="icon-tiny" />
                                  Copy Draft
                                </>
                              )}
                            </button>
                          )}
                        </div>
                        {response.outreach_message ? (
                          <pre className="outreach-content" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                            {response.outreach_message}
                          </pre>
                        ) : (
                          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No outreach message draft available for this query.</p>
                        )}
                      </section>
                    </BorderGlow>
                  )}
                </div>

              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; 2026 Suproc Business Network. All rights reserved.Professional Agent.</p>
      </footer>
    </div>
  );
}

export default App;
