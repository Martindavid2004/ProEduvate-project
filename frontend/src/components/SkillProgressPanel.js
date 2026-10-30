import React, { useEffect, useState } from 'react';
import { skillAPI, API_URL, BACKEND_URL } from '../services/api';
import {
  Users, RefreshCw, Download, AlertCircle, Loader2, Trophy, BarChart3,
} from 'lucide-react';

/**
 * Faculty view of the Placement Training Skill Card System:
 * batch-wide topic progress, filters (topic / progress / inactivity),
 * "needs support" flags and CSV export (Excel-friendly).
 */
export default function SkillProgressPanel() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [topic, setTopic] = useState('');
  const [minPct, setMinPct] = useState('');
  const [maxPct, setMaxPct] = useState('');
  const [inactiveDays, setInactiveDays] = useState('');
  const [needsSupportOnly, setNeedsSupportOnly] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (topic) params.topic = topic;
      if (minPct !== '') params.min_pct = minPct;
      if (maxPct !== '') params.max_pct = maxPct;
      if (inactiveDays !== '') params.inactive_days = inactiveDays;
      const res = await skillAPI.teacherProgress(params);
      setRows(res.data.students || []);
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to load batch progress.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const exportCsv = () => {
    const token = localStorage.getItem('authToken');
    const url = BACKEND_URL.replace(/\/$/, '') + '/api/skills/teacher/export';

    fetch(`${API_URL}/skills/teacher/export`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((resp) => {
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return resp.blob();
      })
      .then((blob) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `skill_progress_export.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
      })
      .catch((e) => setError(e.message || 'Export failed'));
  };

  const filtered = needsSupportOnly ? rows.filter((r) => r.needs_support) : rows;

  const topics = Array.from(new Set(
    rows.flatMap((r) => r.cards.map((c) => c.topic))
  )).sort();

  return (
    <div className="fade-in">
      <div className="flex items-center gap-3 mb-6">
        <Trophy className="text-blue-600" size={28} />
        <h2 className="text-2xl font-bold text-gray-800">Placement Skill Progress</h2>
        <button onClick={load} className="ml-auto text-gray-500 hover:text-blue-600 flex items-center gap-1 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
        <button
          onClick={exportCsv}
          className="bg-green-500 hover:bg-green-600 text-white text-sm px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Download size={16} /> Export CSV (Excel)
        </button>
      </div>

      {/* Filters - progress / score / inactivity / topic */}
      <div className="bg-white rounded-xl border shadow-sm p-4 mb-5 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
        <select value={topic} onChange={(e) => setTopic(e.target.value)} className="border rounded-lg px-3 py-2">
          <option value="">All topics</option>
          {topics.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <input type="number" placeholder="Min % progress" value={minPct} onChange={(e) => setMinPct(e.target.value)} className="border rounded-lg px-3 py-2" />
        <input type="number" placeholder="Max % progress" value={maxPct} onChange={(e) => setMaxPct(e.target.value)} className="border rounded-lg px-3 py-2" />
        <input type="number" placeholder="Inactive (days)" value={inactiveDays} onChange={(e) => setInactiveDays(e.target.value)} className="border rounded-lg px-3 py-2" />
        <label className="flex items-center gap-2 px-1">
          <input type="checkbox" checked={needsSupportOnly} onChange={(e) => setNeedsSupportOnly(e.target.checked)} />
          Needs support only
        </label>
        <button onClick={load} className="md:col-span-5 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium">
          Apply filters
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-3 py-16 text-gray-500">
          <Loader2 className="animate-spin" size={24} /> Loading batch progress…
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 bg-red-50 border border-red-300 text-red-700 p-4 rounded-xl">
          <AlertCircle size={18} /> {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <BarChart3 className="mx-auto text-gray-300 mb-3" size={44} />
          <p className="font-medium text-gray-700">No students match these filters</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border shadow-sm overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-left">
              <tr>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Dept</th>
                <th className="px-4 py-3">Avg completion</th>
                <th className="px-4 py-3">XP</th>
                <th className="px-4 py-3">Solved</th>
                <th className="px-4 py-3">Lessons</th>
                <th className="px-4 py-3">Assess. passed</th>
                <th className="px-4 py-3">Last activity</th>
                <th className="px-4 py-3">Flags</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((r) => (
                <tr key={r.student_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{r.name}</td>
                  <td className="px-4 py-3 text-gray-500">{r.department || '—'}</td>
                  <td className="px-4 py-3">{r.avg_completion_pct}%</td>
                  <td className="px-4 py-3">{r.total_xp}</td>
                  <td className="px-4 py-3">{r.problems_solved}</td>
                  <td className="px-4 py-3">{r.lessons_completed}</td>
                  <td className="px-4 py-3">{r.assessments_passed}</td>
                  <td className="px-4 py-3 text-gray-500">{r.last_activity ? new Date(r.last_activity).toLocaleDateString() : '—'}</td>
                  <td className="px-4 py-3">
                    {r.needs_support && (
                      <span className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-700">needs support</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filtered.length > 0 && (
        <p className="text-xs text-gray-400 mt-3 flex items-center gap-1">
          <Users size={12} /> {filtered.length} students shown
        </p>
      )}
    </div>
  );
}
