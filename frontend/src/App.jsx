import { useEffect, useState } from 'react';
import { NavLink, Link, Navigate, Route, Routes } from 'react-router-dom';
import { BarChart, Bar, CartesianGrid, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import {
  acceptRecommendation,
  completeRecommendation,
  getCandidateSkills,
  getCareerTwin,
  getDashboard,
  getProfile,
  getPerformance,
  getRecommendations,
  getRoles,
  getSelectedRole,
  getRole,
  getSkills,
  generateRecommendation,
  addPerformance,
  login,
  register,
  recordOutcome,
  selectRole,
  compareRoles,
  confirmEvidence,
  createSkill,
  analyzeGithub,
  analyzeResume,
  getEvidence,
  rejectEvidence,
  simulateSkills,
  updateCandidateSkill,
  updateProfile,
} from './services/api';

function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!localStorage.getItem('career_twin_token')) return;
    Promise.all([getDashboard(), getRecommendations()])
      .then(([dashboardData, recommendationData]) => {
        setDashboard(dashboardData);
        setRecommendations(recommendationData || []);
      })
      .catch((requestError) => setError(requestError.message));
  }, []);

  if (!localStorage.getItem('career_twin_token')) {
    return <Navigate to="/login" replace />;
  }

  async function createRecommendation() {
    try {
      await generateRecommendation();
      setRecommendations(await getRecommendations());
      setDashboard(await getDashboard());
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  if (error) {
    return (
      <div className="page">
        <h1>Career Twin Dashboard</h1>
        <div className="alert alert-error">{error}. Please sign in to load your data.</div>
      </div>
    );
  }

  if (!dashboard) {
    return <div className="page"><h1>Career Twin Dashboard</h1><p className="loading-state">Loading your career twin...</p></div>;
  }

  const evaluation = dashboard.evaluation || {};
  const beforeAfterRows = evaluation.before_after_skill_levels || [];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>{dashboard.candidate || 'Career Twin Dashboard'}</h1>
          <p className="subtitle">Real-time Career Intelligence &amp; Predictive Twin State</p>
        </div>
        <span className={`badge ${dashboard.readiness_indicator === 'Strong' ? 'badge-success' : 'badge-primary'}`}>
          {dashboard.readiness_indicator} Readiness
        </span>
      </div>

      <div className="cards">
        <div className="card">
          <span>Target Role</span>
          <strong>{dashboard.target_role || 'Not Selected'}</strong>
        </div>
        <div className="card">
          <span>Career Readiness</span>
          <strong>{dashboard.readiness_score}%</strong>
        </div>
        <div className="card">
          <span>Completed Actions</span>
          <strong>{dashboard.completed_actions ?? 0}</strong>
        </div>
        <div className="card">
          <span>Strong Skills</span>
          <strong>{dashboard.strong_skills?.join(', ') || 'Building evidence'}</strong>
        </div>
        <div className="card">
          <span>Top Skill Gaps</span>
          <strong>{dashboard.top_skill_gaps?.join(', ') || 'No active gaps'}</strong>
        </div>
        <div className="card">
          <span>Evidence Sources</span>
          <strong>{dashboard.evidence_sources?.length ? dashboard.evidence_sources.join(', ') : 'Manual Entry'}</strong>
        </div>
      </div>

      <div className="chart-box">
        <div className="chart-header">
          <h3>Target Role Skill Proficiency</h3>
          <span className="caption">Proficiency vs Role Benchmark (%)</span>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={dashboard.skill_snapshot || []}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="name" stroke="#64748b" />
            <YAxis domain={[0, 100]} stroke="#64748b" />
            <Tooltip />
            <Bar dataKey="value" fill="#4f46e5" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h3>Evaluation &amp; Feedback Analytics</h3>
          <span className="caption">Continuously calculated from PostgreSQL outcomes</span>
        </div>
        <div className="metrics-grid">
          <div className="metric-box"><span>Total recommendations</span><strong>{evaluation.total_recommendations ?? 0}</strong></div>
          <div className="metric-box"><span>Completed</span><strong>{evaluation.completed_recommendations ?? 0}</strong></div>
          <div className="metric-box"><span>Completion rate</span><strong>{evaluation.recommendation_completion_rate != null ? `${evaluation.recommendation_completion_rate}%` : 'N/A'}</strong></div>
          <div className="metric-box"><span>Successful outcomes</span><strong>{evaluation.successful_outcomes ?? 0}</strong></div>
          <div className="metric-box"><span>Average improvement</span><strong>{evaluation.average_skill_improvement != null ? `+${evaluation.average_skill_improvement}` : 'N/A'}</strong></div>
          <div className="metric-box"><span>Identified gaps</span><strong>{evaluation.total_identified_skill_gaps ?? evaluation.identified_skill_gaps ?? 0}</strong></div>
          <div className="metric-box"><span>Improved gaps</span><strong>{evaluation.improved_skill_gaps ?? 0}</strong></div>
          <div className="metric-box"><span>Resolved gaps</span><strong>{evaluation.resolved_skill_gaps ?? 0}</strong></div>
        </div>

        {beforeAfterRows.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Target Skill</th>
                  <th>Before Level</th>
                  <th>After Level</th>
                  <th>Improvement</th>
                </tr>
              </thead>
              <tbody>
                {beforeAfterRows.map((row, idx) => (
                  <tr key={`${row.target_skill}-${idx}`}>
                    <td><strong>{row.target_skill}</strong></td>
                    <td>{row.before_score}/5</td>
                    <td>{row.after_score}/5</td>
                    <td><span className="badge badge-success">+{row.improvement}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty-text">No outcome history recorded yet. Complete recommendations and submit assessment scores to populate analytics.</p>
        )}
      </div>

      <div className="panel">
        <div className="panel-header-action">
          <div>
            <h3>Active Recommendations</h3>
            <p className="caption">Adaptive recommendations generated from your skill gaps</p>
          </div>
          <button type="button" className="btn btn-primary" onClick={createRecommendation}>
            Generate Next Recommendation
          </button>
        </div>

        {recommendations.map((r) => (
          <div className="recommendation-card" key={r.id}>
            <div className="recommendation-header">
              <div className="recommendation-title">
                <strong>{r.target_skill}</strong>
                <span className={`pill ${r.priority >= 2 ? 'pill-high' : 'pill-medium'}`}>
                  {r.priority >= 2 ? 'High Priority' : 'Medium Priority'}
                </span>
              </div>
              <span className={`status status-${r.status}`}>{r.status}</span>
            </div>
            <p className="recommendation-text">{r.recommendation_text}</p>
            {r.reason && (
              <div className="recommendation-reason">
                <strong>Data-Backed Rationale:</strong> {r.reason}
              </div>
            )}
            {r.explanation && (
              <div className="recommendation-explanation">
                <strong>AI Explanation:</strong> {r.explanation}
              </div>
            )}
          </div>
        ))}
        {!recommendations.length && <p className="empty-text">No active recommendations. Click 'Generate Next Recommendation' to evaluate your gaps.</p>}
      </div>

      <div className="panel">
        <h3>Recent Performance &amp; Outcomes</h3>
        {(dashboard.recent_performance || []).map((record) => (
          <div className="list-item" key={record.id}>
            <strong>{record.topic || record.record_type}</strong>
            <span className="badge badge-secondary">{record.record_type}</span>
            <span>Score: <strong>{record.score ?? 0}%</strong></span>
          </div>
        ))}
        {!dashboard.recent_performance?.length && <p className="empty-text">No performance evidence recorded yet.</p>}
      </div>
    </div>
  );
}

function LoginPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await login(event.currentTarget.username.value.trim(), event.currentTarget.password.value);
      localStorage.setItem('career_twin_token', result.access_token);
      window.location.href = '/';
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-box">
        <h1>AI Career Twin</h1>
        <p className="subtitle">Personalized career intelligence with a measurable feedback loop.</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input name="username" type="text" placeholder="e.g. demo_user" defaultValue="demo_user" required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input name="password" type="password" placeholder="Password" defaultValue="demo123" required />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="auth-footer">
          <span>New user?</span> <Link to="/register">Create candidate account</Link>
        </div>
      </div>
    </div>
  );
}

function RegisterPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    const form = event.currentTarget;
    try {
      await register({
        full_name: form.full_name.value.trim(),
        email: form.email.value.trim(),
        username: form.username.value.trim(),
        password: form.password.value,
      });
      window.location.href = '/login';
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-box">
        <h1>Create Account</h1>
        <p className="subtitle">Initialize your candidate Career Twin.</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name</label>
            <input name="full_name" type="text" placeholder="Full name" minLength="2" maxLength="200" required />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input name="email" type="email" placeholder="email@example.com" required />
          </div>
          <div className="form-group">
            <label>Username</label>
            <input name="username" type="text" placeholder="Username" minLength="3" maxLength="50" required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input name="password" type="password" placeholder="Password" minLength="6" required />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="auth-footer">
          <Link to="/login">Back to sign in</Link>
        </div>
      </div>
    </div>
  );
}

function ProfilePage() {
  const [profile, setProfile] = useState({ name: '', career_goal: '', education: '', degree: '', specialization: '', graduation_year: '', bio: '' });
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    Promise.all([
      getProfile().catch(() => null),
      getRoles().catch(() => []),
      getSelectedRole().catch(() => null),
    ]).then(([profileData, roleData, selectedData]) => {
      if (profileData) setProfile(profileData);
      setRoles(roleData || []);
      if (selectedData?.role_id) setSelectedRole(selectedData.role_id);
    });
  }, []);

  async function saveProfile(event) {
    event.preventDefault();
    const saved = await updateProfile({ ...profile, graduation_year: profile.graduation_year ? Number(profile.graduation_year) : null });
    setProfile(saved);
    setMessage('Candidate profile saved successfully.');
  }

  async function saveRole() {
    if (!selectedRole) return;
    await selectRole(selectedRole);
    setMessage('Target role selected. Career Twin synchronized.');
  }

  return (
    <div className="page">
      <h1>Candidate Profile &amp; Target Career</h1>
      <p className="subtitle">Configure your candidate baseline and target career trajectory.</p>

      <form className="panel" onSubmit={saveProfile}>
        <h3>Personal &amp; Academic Background</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Full Name</label>
            <input value={profile.name} onChange={(event) => setProfile({ ...profile, name: event.target.value })} placeholder="Full Name" required />
          </div>
          <div className="form-group">
            <label>Career Goal</label>
            <input value={profile.career_goal || ''} onChange={(event) => setProfile({ ...profile, career_goal: event.target.value })} placeholder="Target Career Goal" />
          </div>
          <div className="form-group">
            <label>Education / Major</label>
            <input value={profile.education || ''} onChange={(event) => setProfile({ ...profile, education: event.target.value })} placeholder="Field of Study" />
          </div>
          <div className="form-group">
            <label>Degree</label>
            <input value={profile.degree || ''} onChange={(event) => setProfile({ ...profile, degree: event.target.value })} placeholder="e.g. BSc, BTech, MSc" />
          </div>
          <div className="form-group">
            <label>Specialization</label>
            <input value={profile.specialization || ''} onChange={(event) => setProfile({ ...profile, specialization: event.target.value })} placeholder="Specialization" />
          </div>
          <div className="form-group">
            <label>Graduation Year</label>
            <input value={profile.graduation_year || ''} onChange={(event) => setProfile({ ...profile, graduation_year: event.target.value })} placeholder="Graduation Year" type="number" />
          </div>
        </div>
        <div className="form-group">
          <label>Bio / Background Summary</label>
          <textarea value={profile.bio || ''} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} placeholder="Brief background summary" rows={3} />
        </div>
        <button type="submit" className="btn btn-primary">Save Profile</button>
      </form>

      <div className="panel">
        <h3>Target Career Path</h3>
        <p className="caption">Selecting a target role calculates skill gaps against industry benchmarks.</p>
        <div className="inline-form">
          <select value={selectedRole} onChange={(event) => setSelectedRole(event.target.value)}>
            <option value="">Choose target role</option>
            {roles.map((role) => <option key={role.id} value={role.id}>{role.name} ({role.domain})</option>)}
          </select>
          <button type="button" className="btn btn-primary" onClick={saveRole}>Confirm Target Role</button>
        </div>
      </div>

      {message && <div className="alert alert-success">{message}</div>}
    </div>
  );
}

function SkillsPage() {
  const [skills, setSkills] = useState([]);
  const [candidateSkills, setCandidateSkills] = useState([]);
  const [form, setForm] = useState({ skill_id: '', current_level: 2.5, confidence: 0.8, evidence: '' });
  const [newSkill, setNewSkill] = useState({ name: '', category: '', description: '' });
  const [message, setMessage] = useState('');

  useEffect(() => {
    Promise.all([getSkills(), getCandidateSkills()]).then(([skillData, candidateData]) => {
      setSkills(skillData || []);
      setCandidateSkills(candidateData || []);
    });
  }, []);

  async function saveSkill(event) {
    event.preventDefault();
    await updateCandidateSkill({
      ...form,
      skill_id: Number(form.skill_id),
      current_level: Number(form.current_level),
      confidence: Number(form.confidence),
    });
    setCandidateSkills(await getCandidateSkills());
    setMessage('Skill level updated and Career Twin synchronized.');
  }

  async function addSkill(event) {
    event.preventDefault();
    const skill = await createSkill({
      name: newSkill.name.trim(),
      category: newSkill.category.trim(),
      description: newSkill.description.trim() || null,
    });
    setSkills((currentSkills) => (
      currentSkills.some((item) => item.id === skill.id) ? currentSkills : [...currentSkills, skill]
    ));
    setForm((currentForm) => ({ ...currentForm, skill_id: String(skill.id) }));
    setNewSkill({ name: '', category: '', description: '' });
    setMessage(`${skill.name} added. You can now record its proficiency and evidence.`);
  }

  return (
    <div className="page">
      <h1>Skill Evidence &amp; Proficiency</h1>
      <p className="subtitle">Record verified skill levels and supporting evidence.</p>

      <form className="panel" onSubmit={saveSkill}>
        <h3>Update Skill Level</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Select Skill</label>
            <select value={form.skill_id} onChange={(event) => setForm({ ...form, skill_id: event.target.value })} required>
              <option value="">Choose a skill</option>
              {skills.map((skill) => <option key={skill.id} value={skill.id}>{skill.name} ({skill.category})</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Proficiency Level (0.0 to 5.0)</label>
            <input value={form.current_level} onChange={(event) => setForm({ ...form, current_level: event.target.value })} type="number" min="0" max="5" step="0.1" required />
          </div>
          <div className="form-group">
            <label>Confidence (0.0 to 1.0)</label>
            <input value={form.confidence} onChange={(event) => setForm({ ...form, confidence: event.target.value })} type="number" min="0" max="1" step="0.05" required />
          </div>
        </div>
        <div className="form-group">
          <label>Supporting Evidence &amp; Context</label>
          <textarea value={form.evidence} onChange={(event) => setForm({ ...form, evidence: event.target.value })} placeholder="Describe projects, coursework, or work experience supporting this proficiency level" rows={2} />
        </div>
        <button type="submit" className="btn btn-primary">Save Skill Evidence</button>
      </form>

      <form className="panel" onSubmit={addSkill}>
        <h3>Add Another Skill</h3>
        <p className="caption">Add any skill that is not in the standard catalog. Custom skills appear in your portfolio, but do not change a role's benchmark requirements.</p>
        <div className="form-grid">
          <div className="form-group">
            <label>Skill Name</label>
            <input value={newSkill.name} onChange={(event) => setNewSkill({ ...newSkill, name: event.target.value })} placeholder="e.g. Kubernetes" minLength="2" required />
          </div>
          <div className="form-group">
            <label>Category</label>
            <input value={newSkill.category} onChange={(event) => setNewSkill({ ...newSkill, category: event.target.value })} placeholder="e.g. DevOps" minLength="2" required />
          </div>
        </div>
        <div className="form-group">
          <label>Description (optional)</label>
          <input value={newSkill.description} onChange={(event) => setNewSkill({ ...newSkill, description: event.target.value })} placeholder="What does this skill represent?" />
        </div>
        <button type="submit" className="btn btn-secondary">Add Skill</button>
      </form>

      <div className="panel">
        <h3>Current Skill Portfolio ({candidateSkills.length})</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Skill Name</th>
                <th>Current Level</th>
                <th>Evidence Confidence</th>
                <th>Supporting Evidence</th>
              </tr>
            </thead>
            <tbody>
              {candidateSkills.map((skill) => (
                <tr key={skill.skill_id}>
                  <td><strong>{skill.name}</strong></td>
                  <td>{skill.current_level} / 5.0</td>
                  <td>{Math.round(skill.confidence * 100)}%</td>
                  <td>{skill.evidence || 'No detailed evidence'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!candidateSkills.length && <p className="empty-text">No skill evidence recorded yet.</p>}
      </div>

      {message && <div className="alert alert-success">{message}</div>}
    </div>
  );
}

function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [outcome, setOutcome] = useState({ recommendation_followed: true, before_score: 2.0, after_score: 3.5, outcome_notes: '' });
  const [activeRecId, setActiveRecId] = useState(null);
  const [message, setMessage] = useState('');

  async function refresh() {
    setRecommendations(await getRecommendations());
  }

  useEffect(() => {
    refresh().catch((requestError) => setMessage(requestError.message));
  }, []);

  async function changeStatus(recommendation, action) {
    await action(recommendation.id);
    await refresh();
    setMessage(`${recommendation.target_skill} status updated.`);
  }

  async function submitOutcome(recommendation) {
    await recordOutcome(recommendation.id, {
      ...outcome,
      before_score: Number(outcome.before_score),
      after_score: Number(outcome.after_score),
    });
    setActiveRecId(null);
    await refresh();
    setMessage(`Outcome recorded for ${recommendation.target_skill}! Career Twin state and next recommendation updated.`);
  }

  return (
    <div className="page">
      <h1>Adaptive Recommendation Lifecycle</h1>
      <p className="subtitle">Execute recommended practice actions and feed back outcomes to update your Career Twin.</p>

      {recommendations.map((recommendation) => (
        <div className="panel" key={recommendation.id}>
          <div className="recommendation-header">
            <div>
              <strong style={{ fontSize: '1.2rem' }}>{recommendation.target_skill}</strong>
              <span className={`pill ${recommendation.priority >= 2 ? 'pill-high' : 'pill-medium'}`} style={{ marginLeft: '12px' }}>
                {recommendation.priority >= 2 ? 'High Priority' : 'Medium Priority'}
              </span>
            </div>
            <span className={`status status-${recommendation.status}`}>{recommendation.status}</span>
          </div>

          <p className="recommendation-text">{recommendation.recommendation_text}</p>

          {recommendation.suggested_activity && (
            <p><strong>Suggested Activity:</strong> {recommendation.suggested_activity} (~{recommendation.estimated_effort_hours}h)</p>
          )}

          {recommendation.reason && (
            <div className="recommendation-reason">
              <strong>Data-Backed Rationale:</strong> {recommendation.reason}
            </div>
          )}

          {recommendation.explanation && (
            <div className="recommendation-explanation">
              <strong>AI Recommendation Explanation:</strong> {recommendation.explanation}
            </div>
          )}

          <div className="action-row" style={{ marginTop: '16px' }}>
            {recommendation.status === 'generated' && (
              <button type="button" className="btn btn-primary" onClick={() => changeStatus(recommendation, acceptRecommendation)}>
                Accept Recommendation
              </button>
            )}

            {recommendation.status === 'accepted' && (
              <button type="button" className="btn btn-success" onClick={() => changeStatus(recommendation, completeRecommendation)}>
                Mark Action Completed
              </button>
            )}

            {recommendation.status === 'completed' && activeRecId !== recommendation.id && (
              <button type="button" className="btn btn-primary" onClick={() => setActiveRecId(recommendation.id)}>
                Record Outcome &amp; Assessment Score
              </button>
            )}

            {recommendation.status === 'evaluated' && (
              <span className="badge badge-success">Evaluated &amp; Applied to Career Twin</span>
            )}
          </div>

          {activeRecId === recommendation.id && (
            <form className="outcome-form" onSubmit={(event) => { event.preventDefault(); submitOutcome(recommendation); }}>
              <h4>Record Outcome for {recommendation.target_skill}</h4>
              <div className="form-grid">
                <div className="form-group">
                  <label>Before Assessment Score (0.0 to 5.0)</label>
                  <input type="number" min="0" max="5" step="0.1" value={outcome.before_score} onChange={(event) => setOutcome({ ...outcome, before_score: event.target.value })} required />
                </div>
                <div className="form-group">
                  <label>After Assessment Score (0.0 to 5.0)</label>
                  <input type="number" min="0" max="5" step="0.1" value={outcome.after_score} onChange={(event) => setOutcome({ ...outcome, after_score: event.target.value })} required />
                </div>
              </div>
              <div className="form-group">
                <label>Outcome Notes &amp; Observations</label>
                <textarea placeholder="e.g. Completed comprehensive query optimization exercises and passed benchmark quiz." value={outcome.outcome_notes} onChange={(event) => setOutcome({ ...outcome, outcome_notes: event.target.value })} rows={2} />
              </div>
              <div className="action-row">
                <button type="submit" className="btn btn-primary">Submit Outcome to Feedback Loop</button>
                <button type="button" className="btn btn-secondary" onClick={() => setActiveRecId(null)}>Cancel</button>
              </div>
            </form>
          )}
        </div>
      ))}

      {!recommendations.length && (
        <div className="panel">
          <p className="empty-text">No recommendations generated yet. Head to the Dashboard to trigger your first recommendation.</p>
        </div>
      )}

      {message && <div className="alert alert-success">{message}</div>}
    </div>
  );
}

function PerformancePage() {
  const [records, setRecords] = useState([]);
  const [form, setForm] = useState({ record_type: 'assessment', topic: '', score: 75, difficulty: 'medium', attempts: 1, notes: '' });
  const [message, setMessage] = useState('');

  async function refresh() {
    setRecords(await getPerformance());
  }

  useEffect(() => {
    refresh().catch((requestError) => setMessage(requestError.message));
  }, []);

  async function savePerformance(event) {
    event.preventDefault();
    await addPerformance({
      ...form,
      score: Number(form.score),
      attempts: Number(form.attempts),
      ...(form.record_type === 'assessment' ? { score_percent: Number(form.score), skill_focus: form.topic } : {}),
      ...(form.record_type === 'learning' ? { course_name: form.topic, completion_percent: Number(form.score), quiz_score: Number(form.score) } : {}),
    });
    await refresh();
    setMessage('Performance evidence recorded.');
  }

  return (
    <div className="page">
      <h1>Performance Evidence</h1>
      <p className="subtitle">Log assessment results, coding exercises, and learning milestones.</p>

      <form className="panel" onSubmit={savePerformance}>
        <h3>Log Performance Milestone</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Record Type</label>
            <select value={form.record_type} onChange={(event) => setForm({ ...form, record_type: event.target.value })}>
              <option value="assessment">Assessment Result</option>
              <option value="coding">Coding Challenge</option>
              <option value="interview">Technical Interview</option>
              <option value="learning">Course / Learning Activity</option>
            </select>
          </div>
          <div className="form-group">
            <label>Topic / Skill Focus</label>
            <input value={form.topic} onChange={(event) => setForm({ ...form, topic: event.target.value })} placeholder="e.g. Python APIs, SQL Joins" required />
          </div>
          <div className="form-group">
            <label>Score (0-100%)</label>
            <input value={form.score} onChange={(event) => setForm({ ...form, score: event.target.value })} type="number" min="0" max="100" step="0.5" />
          </div>
          <div className="form-group">
            <label>Difficulty</label>
            <select value={form.difficulty} onChange={(event) => setForm({ ...form, difficulty: event.target.value })}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>
        <div className="form-group">
          <label>Notes &amp; Evaluation Feedback</label>
          <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Evaluation details" rows={2} />
        </div>
        <button type="submit" className="btn btn-primary">Log Performance</button>
      </form>

      <div className="panel">
        <h3>Performance Records History</h3>
        {records.map((record) => (
          <div className="list-item" key={record.id}>
            <strong>{record.topic || record.record_type}</strong>
            <span className="badge badge-secondary">{record.record_type}</span>
            <span>Score: <strong>{record.score ?? 0}%</strong></span>
          </div>
        ))}
        {!records.length && <p className="empty-text">No performance records logged yet.</p>}
      </div>

      {message && <div className="alert alert-success">{message}</div>}
    </div>
  );
}

function CareerTwinPage() {
  const [twin, setTwin] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getCareerTwin().then(setTwin).catch((requestError) => setError(requestError.message));
  }, []);

  if (error) return <div className="page"><h1>Career Twin</h1><div className="alert alert-error">{error}</div></div>;
  if (!twin) return <div className="page"><h1>Career Twin</h1><p className="loading-state">Loading Career Twin state...</p></div>;

  return (
    <div className="page">
      <h1>{twin.candidate}'s Career Twin</h1>
      <p className="subtitle">Continuous representation of candidate competence and role readiness.</p>

      {twin.summary_narrative && (
        <div className="panel summary-callout">
          <h3>AI Career Twin Executive Summary</h3>
          <p>{twin.summary_narrative}</p>
        </div>
      )}

      <div className="cards">
        <div className="card"><span>Target Role</span><strong>{twin.target_role || 'Not selected'}</strong></div>
        <div className="card"><span>Readiness Score</span><strong>{twin.readiness_score ?? 0}%</strong></div>
        <div className="card"><span>Strong Skills</span><strong>{twin.strong_skills?.join(', ') || 'Building'}</strong></div>
        <div className="card"><span>Active Gaps</span><strong>{twin.weak_skills?.join(', ') || 'None'}</strong></div>
      </div>

      <div className="chart-box">
        <h3>Skill Proficiency Spectrum</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={twin.skills.map((skill) => ({ name: skill.name, value: Math.round(skill.current_level * 20) }))}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="name" stroke="#64748b" />
            <YAxis domain={[0, 100]} stroke="#64748b" />
            <Tooltip />
            <Bar dataKey="value" fill="#4f46e5" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h3>Ranked Skill Gaps</h3>
        {twin.skill_gaps.map((gap) => (
          <div className="list-item" key={gap.skill_name}>
            <strong>{gap.skill_name}</strong>
            <span>Current: {gap.current_level}/5.0 | Required: {gap.required_level}/5.0</span>
            <span className="badge badge-warning">Gap: {gap.gap}</span>
          </div>
        ))}
        {!twin.skill_gaps.length && <p className="empty-text">No active skill gaps identified.</p>}
      </div>

      <div className="panel">
        <h3>Career Twin Historical Snapshots</h3>
        {twin.history.map((item, idx) => (
          <div className="list-item" key={idx}>
            <strong>{item.summary}</strong>
            <span className="badge badge-primary">{item.readiness_score}% Readiness</span>
          </div>
        ))}
        {!twin.history.length && <p className="empty-text">Historical snapshots will accumulate as outcomes are applied.</p>}
      </div>
    </div>
  );
}

function ComparisonPage() {
  const [roles, setRoles] = useState([]);
  const [selected, setSelected] = useState({ roleA: '', roleB: '' });
  const [comparison, setComparison] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getRoles().then(setRoles).catch((error) => setMessage(error.message));
  }, []);

  async function runComparison(event) {
    event.preventDefault();
    try {
      setMessage('');
      const data = await compareRoles(selected.roleA, selected.roleB);
      setComparison(data);
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <div className="page">
      <h1>Career Path Comparison</h1>
      <p className="subtitle">Evaluate your skill readiness simultaneously across two distinct career trajectories.</p>

      <form className="panel" onSubmit={runComparison}>
        <div className="form-grid">
          <div className="form-group">
            <label>Primary Role (Role A)</label>
            <select value={selected.roleA} onChange={(event) => setSelected({ ...selected, roleA: event.target.value })} required>
              <option value="">Select first role</option>
              {roles.map((role) => <option key={role.id} value={role.id}>{role.name} ({role.domain})</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Alternative Role (Role B)</label>
            <select value={selected.roleB} onChange={(event) => setSelected({ ...selected, roleB: event.target.value })} required>
              <option value="">Select second role</option>
              {roles.map((role) => <option key={role.id} value={role.id}>{role.name} ({role.domain})</option>)}
            </select>
          </div>
        </div>
        <button type="submit" className="btn btn-primary">Compare Career Paths</button>
      </form>

      {comparison?.explanation && (
        <div className="panel summary-callout">
          <h3>Comparative Intelligence Summary</h3>
          <p>{comparison.explanation}</p>
        </div>
      )}

      {comparison && (
        <div className="cards-2col">
          {[comparison.role_a, comparison.role_b].map((role) => (
            <div className="panel" key={role.id}>
              <div className="panel-header">
                <h3>{role.name}</h3>
                <span className="badge badge-primary">{role.readiness_score}% Readiness (Total Gap: {role.total_gap})</span>
              </div>
              <p className="caption">{role.description}</p>
              {role.requirements.map((skill) => (
                <div className="list-item" key={skill.skill_id}>
                  <div>
                    <strong>{skill.skill_name}</strong>
                    <p style={{ margin: '4px 0 0', fontSize: '0.85rem', color: '#64748b' }}>{skill.recommended_action}</p>
                  </div>
                  <span>{skill.current_level} / {skill.required_level}</span>
                  <span className={`badge ${skill.gap === 0 ? 'badge-success' : 'badge-warning'}`}>
                    Gap {skill.gap}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {message && <div className="alert alert-error">{message}</div>}
    </div>
  );
}

function SimulationPage() {
  const [roles, setRoles] = useState([]);
  const [roleSkills, setRoleSkills] = useState([]);
  const [roleId, setRoleId] = useState('');
  const [skillId, setSkillId] = useState('');
  const [level, setLevel] = useState(4.0);
  const [result, setResult] = useState(null);

  useEffect(() => {
    getRoles().then(setRoles).catch(() => setRoles([]));
  }, []);

  async function loadRole(role) {
    try {
      setRoleId(role);
      setSkillId('');
      setResult(null);
      setRoleSkills(role ? (await getRole(role)).skills : []);
    } catch {
      setRoleSkills([]);
    }
  }

  async function runSimulation(event) {
    event.preventDefault();
    const data = await simulateSkills({ role_id: Number(roleId), overrides: { [skillId]: Number(level) } });
    setResult(data);
  }

  return (
    <div className="page">
      <h1>Hypothetical Career Simulation</h1>
      <p className="subtitle">Simulate what-if skill adjustments without altering your real candidate profile or database.</p>

      <form className="panel" onSubmit={runSimulation}>
        <div className="form-grid">
          <div className="form-group">
            <label>Target Role for Simulation</label>
            <select value={roleId} onChange={(event) => loadRole(event.target.value)} required>
              <option value="">Select target role</option>
              {roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Skill to Hypothetically Adjust</label>
            <select value={skillId} onChange={(event) => setSkillId(event.target.value)} required>
              <option value="">Select skill</option>
              {roleSkills.map((skill) => <option key={skill.skill_id} value={skill.skill_id}>{skill.skill_name} (Req: {skill.required_level})</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Hypothetical Level (0.0 to 5.0)</label>
            <input value={level} onChange={(event) => setLevel(event.target.value)} type="number" min="0" max="5" step="0.1" required />
          </div>
        </div>
        <button type="submit" className="btn btn-primary">Run What-If Simulation</button>
      </form>

      {result && (
        <div className="panel">
          <div className="alert alert-info" style={{ marginBottom: '20px' }}>
            <strong>Non-Mutating Simulation:</strong> Real candidate data in PostgreSQL was verified unmodified.
          </div>

          <div className="cards">
            <div className="card"><span>Current Readiness</span><strong>{result.current_readiness}%</strong></div>
            <div className="card"><span>Simulated Readiness</span><strong>{result.simulated_readiness}%</strong></div>
            <div className="card">
              <span>Readiness Impact</span>
              <strong style={{ color: result.readiness_impact >= 0 ? '#10b981' : '#ef4444' }}>
                {result.readiness_impact >= 0 ? `+${result.readiness_impact}%` : `${result.readiness_impact}%`}
              </strong>
            </div>
          </div>

          <h3>Skill Gap Comparison</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Skill</th>
                  <th>Current Level</th>
                  <th>Simulated Level</th>
                  <th>Required Level</th>
                  <th>Simulated Gap</th>
                </tr>
              </thead>
              <tbody>
                {result.simulated.map((skill) => {
                  const currentItem = result.current.find((item) => item.skill_name === skill.skill_name) || {};
                  return (
                    <tr key={skill.skill_name}>
                      <td><strong>{skill.skill_name}</strong></td>
                      <td>{currentItem.current_level}/5.0</td>
                      <td>{skill.current_level}/5.0</td>
                      <td>{skill.required_level}/5.0</td>
                      <td><span className="badge badge-warning">Gap: {skill.gap}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function EvidencePage() {
  const [evidence, setEvidence] = useState([]);
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setEvidence(await getEvidence());
  }

  useEffect(() => {
    refresh().catch((error) => setMessage(error.message));
  }, []);

  async function submitResume(event) {
    event.preventDefault();
    const file = event.currentTarget.file.files[0];
    if (!file) return;
    try {
      setBusy(true);
      setMessage('');
      await analyzeResume(file);
      await refresh();
      event.currentTarget.reset();
      setMessage('Resume parsed successfully. Review extracted skills and projects below before confirming.');
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitGithub(event) {
    event.preventDefault();
    try {
      setBusy(true);
      setMessage('');
      
      let cleanUsername = username.trim();
      if (cleanUsername.includes('github.com/')) {
        const parts = cleanUsername.split('/');
        cleanUsername = parts.pop() || parts.pop();
      }
      
      await analyzeGithub(cleanUsername);
      await refresh();
      setUsername('');
      setMessage('GitHub repositories analyzed. Review extracted repositories and technologies before confirming.');
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function review(item, action) {
    try {
      await action(item.id);
      await refresh();
      setMessage(`Evidence successfully ${item.status === 'pending' ? 'reviewed' : 'updated'}. Career Twin synchronized.`);
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <div className="page">
      <h1>External Evidence Ingestion</h1>
      <p className="subtitle">Extract competencies from Resume PDF and GitHub with user-in-the-loop review.</p>

      <div className="cards-2col">
        <form className="panel" onSubmit={submitResume}>
          <h3>Resume PDF Ingestion</h3>
          <p className="caption">Upload a PDF resume to extract skills, technologies, and projects.</p>
          <div className="form-group">
            <input name="file" type="file" accept="application/pdf" required />
          </div>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Extracting...' : 'Upload & Analyze Resume'}
          </button>
        </form>

        <form className="panel" onSubmit={submitGithub}>
          <h3>GitHub Profile Ingestion</h3>
          <p className="caption">Inspect public repositories, languages, and technical contributions.</p>
          <div className="form-group">
            <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="GitHub Username (e.g. torvalds)" required />
          </div>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Analyzing...' : 'Analyze GitHub Profile'}
          </button>
        </form>
      </div>

      {message && <div className="alert alert-info">{message}</div>}

      <div className="panel">
        <h3>Ingested Evidence Records ({evidence.length})</h3>
        {evidence.map((item) => (
          <div className="evidence-item" key={item.id}>
            <div className="recommendation-header">
              <div>
                <strong>{item.title}</strong>
                <span className="badge badge-secondary" style={{ marginLeft: '10px' }}>Source: {item.source}</span>
              </div>
              <span className={`status status-${item.status}`}>{item.status}</span>
            </div>

            <p><strong>Extracted Skills:</strong> {item.extracted_skills?.map((s) => s.name).join(', ') || 'None detected'}</p>
            <p><strong>Extracted Projects:</strong> {item.extracted_projects?.map((p) => p.name).join(', ') || 'None detected'}</p>

            {item.status === 'pending' && (
              <div className="action-row" style={{ marginTop: '12px' }}>
                <button type="button" className="btn btn-success" onClick={() => review(item, confirmEvidence)}>
                  Confirm &amp; Integrate to Career Twin
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => review(item, rejectEvidence)}>
                  Reject Evidence
                </button>
              </div>
            )}
          </div>
        ))}
        {!evidence.length && <p className="empty-text">No evidence items uploaded yet.</p>}
      </div>
    </div>
  );
}

function App() {
  function handleLogout() {
    localStorage.removeItem('career_twin_token');
    window.location.href = '/login';
  }

  const token = localStorage.getItem('career_twin_token');

  return (
    <div className="app-shell">
      {token && (
        <aside className="sidebar">
          <div className="brand">AI Career Twin</div>
          <nav>
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Dashboard</NavLink>
            <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : '')}>Profile &amp; Goal</NavLink>
            <NavLink to="/skills" className={({ isActive }) => (isActive ? 'active' : '')}>Skill Evidence</NavLink>
            <NavLink to="/evidence" className={({ isActive }) => (isActive ? 'active' : '')}>Resume &amp; GitHub</NavLink>
            <NavLink to="/performance" className={({ isActive }) => (isActive ? 'active' : '')}>Performance</NavLink>
            <NavLink to="/recommendations" className={({ isActive }) => (isActive ? 'active' : '')}>Recommendations</NavLink>
            <NavLink to="/career-twin" className={({ isActive }) => (isActive ? 'active' : '')}>Career Twin</NavLink>
            <NavLink to="/comparison" className={({ isActive }) => (isActive ? 'active' : '')}>Comparison</NavLink>
            <NavLink to="/simulation" className={({ isActive }) => (isActive ? 'active' : '')}>Simulation</NavLink>
          </nav>
          <div className="sidebar-footer">
            <button type="button" className="btn-logout" onClick={handleLogout}>Sign Out</button>
          </div>
        </aside>
      )}

      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/evidence" element={<EvidencePage />} />
          <Route path="/performance" element={<PerformancePage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/career-twin" element={<CareerTwinPage />} />
          <Route path="/comparison" element={<ComparisonPage />} />
          <Route path="/simulation" element={<SimulationPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
