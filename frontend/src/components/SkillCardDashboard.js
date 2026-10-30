import React, { useState, useEffect, useCallback } from 'react';
import { skillAPI } from '../services/api';
import {
  Code, Database, FileCode, Terminal, Network, Target, Brain,
  MessageSquare, Globe, Book, Award, Zap, CheckCircle, ArrowLeft,
  RefreshCw, AlertCircle, Play, Check, Lock, Trophy, Star, History,
  ChevronRight, Loader2,
} from 'lucide-react';

const ICONS = {
  code: Code, database: Database, 'file-code': FileCode, terminal: Terminal,
  network: Network, target: Target, brain: Brain,
  'message-square': MessageSquare, globe: Globe, book: Book,
};

const BADGE_COLORS = {
  beginner: 'bg-gray-100 text-gray-700',
  practitioner: 'bg-blue-100 text-blue-700',
  advanced: 'bg-indigo-100 text-indigo-700',
  expert: 'bg-green-100 text-green-700',
};

const pctBar = (pct) => (
  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
    <div
      className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all"
      style={{ width: `${Math.max(0, Math.min(100, pct))}%` }}
    />
  </div>
);

const fmtWhen = (at) => (at ? new Date(at).toLocaleString() : 'No activity yet');

// ------------------------------------------------------------------ card --
function TopicCard({ card, onOpen }) {
  const Icon = ICONS[card.topic.icon] || Book;
  const counts = card.counts;
  return (
    <div
      onClick={() => onOpen(card.topic.id)}
      className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer border-2 border-transparent hover:border-blue-500 transform hover:-translate-y-1 p-5"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="bg-blue-100 p-3 rounded-full">
          <Icon className="text-blue-600" size={26} />
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${BADGE_COLORS[card.badge_key] || BADGE_COLORS.beginner}`}>
          {card.badge_label}
        </span>
      </div>
      <h3 className="text-lg font-bold text-gray-800 mb-1">{card.topic.name}</h3>
      <p className="text-xs text-gray-500 mb-3">Last activity: {fmtWhen(card.last_activity)}</p>

      <div className="mb-2">{pctBar(card.completion_pct)}</div>
      <div className="flex justify-between text-xs text-gray-600 mb-3">
        <span>{card.completion_pct}% complete</span>
        <span className="flex items-center gap-1"><Zap size={12} className="text-yellow-500" /> {card.xp} XP</span>
      </div>

      <dl className="text-xs space-y-1 text-gray-600 border-t pt-3">
        <div className="flex justify-between"><dt>💻 Coding practice</dt><dd>{counts.problems_solved}/{counts.problems_required} solved</dd></div>
        <div className="flex justify-between"><dt>📖 Learning</dt><dd>{counts.lessons_completed}/{counts.lessons_required} lessons</dd></div>
        <div className="flex justify-between"><dt>📝 Assessments</dt><dd>{counts.assessments_completed}/{counts.assessments_required} done</dd></div>
        <div className="flex justify-between"><dt>🎯 Assessment score</dt><dd>{card.assessment_pct ? `${card.assessment_pct}%` : '—'}</dd></div>
      </dl>

      {card.proficiency.earned && (
        <div className="mt-3 flex items-center gap-1 text-xs text-yellow-700 bg-yellow-50 px-2 py-1 rounded">
          <Star size={12} /> Skill Master
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <span className="text-blue-600 text-sm font-medium flex items-center gap-1">
          Continue Learning <ChevronRight size={14} />
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- detail --
const DETAIL_TABS = [
  ['overview', 'Overview'], ['learn', 'Learn'], ['coding', 'Coding Practice'],
  ['assessments', 'Assessments'], ['achievements', 'Achievements'], ['history', 'Activity History'],
];

function LessonList({ lessons, onComplete, busyId, doneMsg }) {
  if (!lessons.length) {
    return <EmptyState icon={Book} title="No lessons yet" text="Lessons will appear here once your teacher adds them." />;
  }
  return (
    <ul className="space-y-3">
      {lessons.map((lesson) => (
        <li key={lesson.id} className="bg-white border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              {lesson.completed
                ? <CheckCircle className="text-green-500 shrink-0" size={20} />
                : <Book className="text-gray-400 shrink-0" size={20} />}
              <div>
                <p className="font-medium text-gray-800">{lesson.title}</p>
                {lesson.completed && <p className="text-xs text-green-600">Completed (+XP awarded once)</p>}
              </div>
            </div>
            {!lesson.completed && (
              <button
                onClick={() => onComplete(lesson.id)}
                disabled={busyId === lesson.id}
                className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded flex items-center gap-1"
              >
                {busyId === lesson.id ? <Loader2 size={12} className="animate-spin" /> : 'Mark complete'}
              </button>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{lesson.content}</p>
          {doneMsg && lesson.id === doneMsg.lessonId && doneMsg.message && (
            <p className="text-xs text-green-600 mt-2">{doneMsg.message}</p>
          )}
        </li>
      ))}
    </ul>
  );
}

function CodingPanel({ problems, onRefresh, detail, setDetail }) {
  const [openProblemId, setOpenProblemId] = useState(null);
  const [code, setCode] = useState('');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const openProblem = problems.find((p) => p.id === openProblemId);

  if (!problems.length) {
    return <EmptyState icon={Code} title="No coding problems yet" text="Practice problems will appear here once assigned." />;
  }

  const startProblem = (problem) => {
    setOpenProblemId(problem.id);
    setCode(problem.starter_code || '');
    setResults(null);
    setError(null);
  };

  const submit = async () => {
    if (!openProblem) return;
    setRunning(true);
    setError(null);
    setResults(null);
    try {
      const res = await skillAPI.submitProblem(openProblem.id, code);
      const data = res.data;
      setResults(data);
      if (data.solved) {
        // refresh topic detail so progress reflects immediately
        const refreshed = await skillAPI.topicDetail(detail.topic.id);
        setTimeout(() => { if (refreshed.data.success) setDetail(refreshed.data); }, 0);
      }
    } catch (e) {
      setError(e.response?.data?.message || e.message || 'Submission failed');
    } finally {
      setRunning(false);
    }
  };

  if (openProblem) {
    return (
      <div>
        <button
          onClick={() => { setOpenProblemId(null); setResults(null); }}
          className="mb-4 text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
        >
          <ArrowLeft size={16} /> Back to problem list
        </button>
        <h3 className="text-lg font-bold text-gray-800">{openProblem.title}
          <span className="ml-2 text-xs align-middle px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">{openProblem.difficulty}</span>
        </h3>
        <p className="text-sm text-gray-600 mt-1 mb-3">{openProblem.description}</p>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={12}
          spellCheck={false}
          className="w-full border border-gray-300 rounded-lg p-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={submit}
          disabled={running}
          className="mt-3 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white px-5 py-2 rounded-lg flex items-center gap-2"
        >
          {running ? <><Loader2 size={16} className="animate-spin" /> Evaluating…</> : <><Play size={16} /> Submit for evaluation</>}
        </button>
        {error && <ErrorState message={error} />}
        {results && (
          <div className="mt-4 bg-gray-900 text-gray-100 rounded-lg p-4 text-sm font-mono overflow-x-auto">
            <p className={results.solved ? 'text-green-400' : 'text-red-400'}>
              {results.solved ? '✅ SOLVED — all test cases passed. XP awarded on the server.' : '❌ Not solved yet — failed attempts do not count or award XP.'}
            </p>
            <ul className="mt-2 space-y-2">
              {results.case_results.map((c, i) => (
                <li key={i}>
                  <span className={c.passed ? 'text-green-400' : 'text-red-400'}>{c.passed ? 'PASS' : 'FAIL'}</span>{' '}
                  input="{c.input}" → got "{c.actual}" (expected "{c.expected}")
                  {!c.passed && c.error && <div className="text-yellow-300 text-xs whitespace-pre-wrap mt-1 ml-4">{c.error}</div>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {problems.map((problem) => (
        <li key={problem.id} className="bg-white border rounded-lg p-4 shadow-sm flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {problem.solved
              ? <CheckCircle className="text-green-500 shrink-0" size={20} />
              : <Circle className="text-gray-400 shrink-0" size={20} />}
            <div>
              <p className="font-medium text-gray-800">{problem.title}</p>
              <p className="text-xs text-gray-500">
                {problem.difficulty} · {problem.test_case_count} test cases {problem.solved && '· solved ✅'}
              </p>
            </div>
          </div>
          <button
            onClick={() => startProblem(problem)}
            className="bg-blue-500 hover:bg-blue-600 text-white text-xs px-3 py-1.5 rounded"
          >
            {problem.solved ? 'Practice again' : 'Start problem'}
          </button>
        </li>
      ))}
    </ul>
  );
}

function AssessmentsPanel({ assessments, onRefresh, setDetail, detail }) {
  const [openId, setOpenId] = useState(null);
  const [paper, setPaper] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const open = async (assessment) => {
    setOpenId(assessment.id);
    setError(null);
    setResult(null);
    setAnswers({});
    if (assessment.attempts.length) {
      setPaper(null);
      return;
    }
    try {
      const res = await skillAPI.getAssessment(assessment.id);
      setPaper(res.data.assessment);
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to load assessment');
    }
  };

  const submit = async (assessmentId) => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await skillAPI.submitAssessment(assessmentId, answers);
      setResult(res.data);
      const refreshed = await skillAPI.topicDetail(detail.topic.id);
      setTimeout(() => { if (refreshed.data.success) setDetail(refreshed.data); }, 0);
      setPaper(null);
    } catch (e) {
      setError(e.response?.data?.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (!assessments.length) {
    return <EmptyState icon={Award} title="No assessments yet" text="Assessments will appear here once configured." />;
  }

  if (openId) {
    const assessment = assessments.find((a) => a.id === openId);
    return (
      <div>
        <button
          onClick={() => { setOpenId(null); setPaper(null); setResult(null); }}
          className="mb-4 text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
        >
          <ArrowLeft size={16} /> Back to assessments
        </button>
        <h3 className="text-lg font-bold text-gray-800">{assessment.title}</h3>
        <p className="text-sm text-gray-500 mb-4">
          Max marks: {assessment.max_marks} · Pass: {assessment.pass_pct}% ·
          Retakes allowed: {assessment.retakes_allowed} · Attempts used: {assessment.attempts.length}
        </p>

        {result && (
          <div className={`p-4 rounded-lg mb-4 ${result.pass ? 'bg-green-50 border border-green-300' : 'bg-red-50 border border-red-300'}`}>
            <p className="font-bold text-gray-800">
              {result.pass ? '🎉 Passed' : '❌ Not passed'} — {result.marks}/{result.max_marks} ({result.pct}%)
            </p>
            <p className="text-sm text-gray-600">
              {result.xp_awarded > 0 ? `+${result.xp_awarded} XP awarded on the server.` : 'No XP for this result (already awarded or attempt not passing).'}
              Total XP: {result.total_xp}
            </p>
            <p className="text-xs text-gray-500 mt-1">Completion and proficiency are tracked separately.</p>
          </div>
        )}

        {paper && (
          <div className="space-y-4">
            {paper.questions.map((q, qi) => (
              <div key={qi} className="bg-white border rounded-lg p-4 shadow-sm">
                <p className="font-medium text-gray-800 mb-2">{qi + 1}. {q.question} <span className="text-xs text-gray-400">({q.marks} marks)</span></p>
                {q.options.map((opt, oi) => (
                  <label key={oi} className="flex items-center gap-2 text-sm text-gray-700 py-1 cursor-pointer">
                    <input
                      type="radio"
                      name={`q${qi}`}
                      checked={answers[String(qi)] === oi}
                      onChange={() => setAnswers({ ...answers, [String(qi)]: oi })}
                    />
                    {opt}
                  </label>
                ))}
              </div>
            ))}
            <button
              onClick={() => submit(openId)}
              disabled={submitting || Object.keys(answers).length < paper.questions.length}
              className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-6 py-2 rounded-lg flex items-center gap-2"
            >
              {submitting ? <><Loader2 size={16} className="animate-spin" /> Submitting…</> : 'Submit assessment'}
            </button>
            <p className="text-xs text-gray-500">{Object.keys(answers).length}/{paper.questions.length} answered</p>
          </div>
        )}

        {!paper && !result && assessment.attempts.length > 0 && (
          <div className="space-y-2">
            <ul className="space-y-2">
              {assessment.attempts.map((a) => (
                <li key={a.attempt_no} className="bg-white border rounded-lg p-3 text-sm flex justify-between">
                  <span>Attempt {a.attempt_no}</span>
                  <span className={a.pass ? 'text-green-600' : 'text-red-600'}>
                    {a.marks}/{a.max_marks} ({a.pct}%) {a.pass ? 'PASS' : 'FAIL'} — {fmtWhen(a.at)}
                  </span>
                </li>
              ))}
            </ul>
            {assessment.attempts.length <= assessment.retakes_allowed && (
              <button
                onClick={() => open(assessment)}
                className="bg-blue-500 hover:bg-blue-600 text-white text-sm px-4 py-2 rounded"
              >
                Retake assessment
              </button>
            )}
          </div>
        )}
        {error && <ErrorState message={error} />}
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {assessments.map((a) => (
        <li key={a.id} className="bg-white border rounded-lg p-4 shadow-sm flex items-center justify-between gap-3">
          <div>
            <p className="font-medium text-gray-800">{a.title}</p>
            <p className="text-xs text-gray-500">
              Max {a.max_marks} · pass {a.pass_pct}% ·{a.attempts.length
                ? ` attempts: ${a.attempts.map((at) => `${at.pct}%${at.pass ? ' ✓' : ' ✗'}`).join(', ')}`
                : ' not attempted yet'}
            </p>
          </div>
          <button onClick={() => open(a)} className="bg-blue-500 hover:bg-blue-600 text-white text-xs px-3 py-1.5 rounded">
            {a.attempts.length ? 'Retake' : 'Take assessment'}
          </button>
        </li>
      ))}
    </ul>
  );
}

// ------------------------------------------------------------ small bits --
function Circle(props) { return <span className="inline-block w-5 h-5 rounded-full border-2 border-gray-300" aria-hidden="true" />; }

function LoadingState({ text = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-gray-500">
      <Loader2 className="animate-spin" size={24} /> {text}
    </div>
  );
}

function EmptyState({ icon: Icon = Book, title, text }) {
  return (
    <div className="text-center py-12 bg-white rounded-xl border">
      <Icon className="mx-auto text-gray-300 mb-3" size={44} />
      <p className="font-medium text-gray-700">{title}</p>
      <p className="text-sm text-gray-500 mt-1">{text}</p>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="flex items-center justify-between gap-3 bg-red-50 border border-red-300 text-red-700 p-4 rounded-xl">
      <div className="flex items-center gap-2">
        <AlertCircle size={18} />
        <span className="text-sm">{message}</span>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="text-sm underline flex items-center gap-1">
          <RefreshCw size={14} /> Retry
        </button>
      )}
    </div>
  );
}

// ----------------------------------------------------------------- main --
export default function SkillCardDashboard({ currentStudent }) {
  const [dashboard, setDashboard] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailTab, setDetailTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);
  const [busyLessonId, setBusyLessonId] = useState(null);
  const [doneMsg, setDoneMsg] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await skillAPI.dashboard();
      setDashboard(res.data);
    } catch (e) {
      setError(e.response?.data?.message || 'Could not load your skill dashboard.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  const openTopic = async (topicId, tab = 'overview') => {
    setDetailLoading(true);
    setDetail(null);
    setDetailTab(tab);
    try {
      const res = await skillAPI.topicDetail(topicId);
      setDetail(res.data.success ? res.data : null);
    } catch (e) {
      setError(e.response?.data?.message || 'Could not load the topic.');
    } finally {
      setDetailLoading(false);
    }
  };

  const completeLesson = async (lessonId) => {
    setBusyLessonId(lessonId);
    setDoneMsg(null);
    try {
      const res = await skillAPI.completeLesson(lessonId);
      setDoneMsg({
        lessonId,
        message: res.data.duplicate
          ? 'Lesson was already completed (no duplicate XP).'
          : `+${res.data.xp_awarded} XP${res.data.topic_bonus_awarded ? ' + topic bonus!' : ''}`,
      });
      const refreshed = await skillAPI.topicDetail(detail.topic.id);
      if (refreshed.data.success) setDetail(refreshed.data);
    } catch (e) {
      setDoneMsg({ lessonId, message: e.response?.data?.message || 'Failed to complete lesson' });
    } finally {
      setBusyLessonId(null);
    }
  };

  if (loading) return <LoadingState text="Loading your Placement Training skill cards…" />;
  if (error && !dashboard) return <ErrorState message={error} onRetry={loadDashboard} />;

  // ------------------------------------------------ topic detail page --
  if (detail) {
    const t = detail.topic;
    const Icon = ICONS[t.icon] || Book;
    return (
      <div>
        <button
          onClick={() => { setDetail(null); loadDashboard(); }}
          className="mb-4 text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
        >
          <ArrowLeft size={20} /> Back to Skill Cards
        </button>

        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl shadow-md mb-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-blue-100 p-3 rounded-full"><Icon className="text-blue-600" size={26} /></div>
            <h3 className="text-2xl font-bold text-gray-800">{t.name}</h3>
            <span className={`ml-auto text-xs px-2 py-1 rounded-full font-medium ${BADGE_COLORS[detail.card.badge_key]}`}>
              {detail.card.badge_label}
            </span>
          </div>
          <p className="text-gray-600 text-sm mb-3">{t.description}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-white rounded-lg p-3"><p className="text-gray-500 text-xs">Completion</p><p className="font-bold text-gray-800">{detail.card.completion_pct}%</p></div>
            <div className="bg-white rounded-lg p-3"><p className="text-gray-500 text-xs">Topic XP</p><p className="font-bold text-gray-800 flex items-center gap-1"><Zap size={13} className="text-yellow-500" />{detail.xp}</p></div>
            <div className="bg-white rounded-lg p-3"><p className="text-gray-500 text-xs">Assessment</p><p className="font-bold text-gray-800">{detail.card.proficiency.earned ? 'Skill Master 🏆' : (detail.card.assessment_pct ? `${detail.card.assessment_pct}% best` : 'No attempts')}</p></div>
            <div className="bg-white rounded-lg p-3"><p className="text-gray-500 text-xs">Last activity</p><p className="font-bold text-gray-800 text-xs mt-1">{fmtWhen(detail.card.last_activity)}</p></div>
          </div>
        </div>

        <div className="flex gap-2 mb-5 overflow-x-auto pb-1">
          {DETAIL_TABS.map(([id, label]) => (
            <button
              key={id}
              onClick={() => setDetailTab(id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${detailTab === id ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-100 border'}`}
            >
              {label}
            </button>
          ))}
        </div>

        {detailTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border p-5 shadow-sm">
              <h4 className="font-bold text-gray-800 mb-3">Progress breakdown</h4>
              <div className="space-y-3 text-sm">
                <div><div className="flex justify-between mb-1"><span>Coding practice (40%)</span><span>{detail.card.counts.problems_solved}/{detail.card.counts.problems_required}</span></div>{pctBar(detail.card.counts.problems_required ? detail.card.counts.problems_solved / detail.card.counts.problems_required * 100 : 0)}</div>
                <div><div className="flex justify-between mb-1"><span>Learning (20%)</span><span>{detail.card.counts.lessons_completed}/{detail.card.counts.lessons_required}</span></div>{pctBar(detail.card.counts.lessons_required ? detail.card.counts.lessons_completed / detail.card.counts.lessons_required * 100 : 0)}</div>
                <div><div className="flex justify-between mb-1"><span>Assessments (40%)</span><span>{detail.card.counts.assessments_completed}/{detail.card.counts.assessments_required}</span></div>{pctBar(detail.card.counts.assessments_required ? detail.card.counts.assessments_completed / detail.card.counts.assessments_required * 100 : 0)}</div>
              </div>
              <p className="text-xs text-gray-500 mt-3">Overall = Coding×40% + Learning×20% + Assessment×40% (empty categories are normalized out). Completion and proficiency are separate metrics.</p>
            </div>
            <div className="bg-white rounded-xl border p-5 shadow-sm">
              <h4 className="font-bold text-gray-800 mb-3">Recommended next steps</h4>
              <p className="text-sm text-gray-600">
                {detail.lessons.some((l) => !l.completed)
                  ? <>Continue learning: <strong>{detail.lessons.find((l) => !l.completed).title}</strong></>
                  : detail.problems.some((p) => !p.solved)
                    ? <>Try solving: <strong>{detail.problems.find((p) => !p.solved).title}</strong></>
                    : detail.assessments.some((a) => !a.attempts.length)
                      ? <>Take assessment: <strong>{detail.assessments.find((a) => !a.attempts.length).title}</strong></>
                      : 'All required activities done - great job! 🎉'}
              </p>
              <button
                onClick={() => setDetailTab(
                  detail.lessons.some((l) => !l.completed) ? 'learn'
                    : detail.problems.some((p) => !p.solved) ? 'coding' : 'assessments')}
                className="mt-4 bg-blue-500 hover:bg-blue-600 text-white text-sm px-4 py-2 rounded-lg"
              >
                Continue Learning
              </button>
            </div>
          </div>
        )}

        {detailTab === 'learn' && (
          <LessonList lessons={detail.lessons} onComplete={completeLesson} busyId={busyLessonId} doneMsg={doneMsg} />
        )}
        {detailTab === 'coding' && (
          <CodingPanel problems={detail.problems} detail={detail} setDetail={setDetail} />
        )}
        {detailTab === 'assessments' && (
          <AssessmentsPanel assessments={detail.assessments} detail={detail} setDetail={setDetail} />
        )}
        {detailTab === 'achievements' && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border p-5 shadow-sm">
              <h4 className="font-bold text-gray-800 mb-3">Earned badges</h4>
              {detail.badges.length === 0
                ? <p className="text-sm text-gray-500">No badges yet - complete activities to progress from Beginner to Expert.</p>
                : <div className="flex flex-wrap gap-2">{detail.badges.map((b) => (
                  <span key={b.id} className={`text-xs px-3 py-1.5 rounded-full font-medium ${BADGE_COLORS[b.badge_key] || BADGE_COLORS.beginner}`}>
                    {b.badge_label}
                  </span>))}</div>}
            </div>
            <div className="bg-white rounded-xl border p-5 shadow-sm">
              <h4 className="font-bold text-gray-800 mb-3">Upcoming criteria</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                {progressLevels().map((lv) => (
                  <li key={lv.key}>• <strong>{lv.label}</strong> — {lv.meaning}</li>
                ))}
                <li className="pt-2">🏆 <strong>Skill Master</strong> — separate proficiency badge: best assessment ≥ 80%, learning ≥ 60%, and all required coding problems solved.</li>
              </ul>
            </div>
          </div>
        )}
        {detailTab === 'history' && (
          <div className="bg-white rounded-xl border p-5 shadow-sm">
            {detail.activity_history.length === 0
              ? <p className="text-sm text-gray-500">No activity recorded yet.</p>
              : <ol className="space-y-3">{detail.activity_history.map((h) => (
                <li key={h.id} className="flex gap-3 text-sm">
                  <History className="text-gray-400 shrink-0 mt-0.5" size={16} />
                  <div>
                    <p className="text-gray-800">{h.description}</p>
                    <p className="text-xs text-gray-400">{fmtWhen(h.at)}</p>
                  </div>
                </li>))}</ol>}
          </div>
        )}
      </div>
    );
  }

  // ------------------------------------------------------ dashboard page --
  const totals = dashboard.totals;
  return (
    <div>
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl shadow-md mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Trophy className="text-blue-600" size={28} />
          <h3 className="text-xl font-bold text-gray-800">Skill Card Dashboard</h3>
          <button onClick={loadDashboard} className="ml-auto text-gray-500 hover:text-blue-600 flex items-center gap-1 text-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className="bg-white rounded-xl p-4 shadow-sm"><p className="text-xs text-gray-500">Total XP</p><p className="text-2xl font-bold text-gray-800 flex items-center gap-1"><Zap size={18} className="text-yellow-500" />{totals.xp}</p></div>
          <div className="bg-white rounded-xl p-4 shadow-sm"><p className="text-xs text-gray-500">Badges</p><p className="text-2xl font-bold text-gray-800 flex items-center gap-1"><Award size={18} className="text-indigo-500" />{totals.badges}</p></div>
          <div className="bg-white rounded-xl p-4 shadow-sm"><p className="text-xs text-gray-500">Problems solved</p><p className="text-2xl font-bold text-gray-800">{totals.problems_solved}<span className="text-sm text-gray-400">/{totals.problems_total}</span></p></div>
          <div className="bg-white rounded-xl p-4 shadow-sm"><p className="text-xs text-gray-500">Lessons completed</p><p className="text-2xl font-bold text-gray-800">{totals.lessons_completed}<span className="text-sm text-gray-400">/{totals.lessons_total}</span></p></div>
          <div className="bg-white rounded-xl p-4 shadow-sm col-span-2 md:col-span-2"><p className="text-xs text-gray-500">Assessments</p><p className="text-lg font-bold text-gray-800">{totals.assessments_completed}/{totals.assessments_total} · avg {totals.average_assessment_score}% · pass rate {totals.pass_rate}%</p></div>
          {dashboard.recommended.topic && (
            <div
              onClick={() => openTopic(dashboard.recommended.topic.id, 'learn')}
              className="bg-white rounded-xl p-4 shadow-sm cursor-pointer hover:shadow-md col-span-2"
            >
              <p className="text-xs text-gray-500">Recommended next</p>
              <p className="font-bold text-blue-600">{dashboard.recommended.topic.name} — {dashboard.recommended.next_lesson?.title || 'keep practicing'}</p>
            </div>
          )}
        </div>
      </div>

      {error && <div className="mb-6"><ErrorState message={error} onRetry={loadDashboard} /></div>}

      {dashboard.cards.length === 0 ? (
        <EmptyState icon={Trophy} title="No skill cards yet" text="Topics will appear here once your administrator assigns training topics." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dashboard.cards.map((card) => (
            <TopicCard key={card.topic.id} card={card} onOpen={openTopic} />
          ))}
        </div>
      )}

      {dashboard.recent_activity.length > 0 && (
        <div className="mt-8 bg-white rounded-xl border p-5 shadow-sm">
          <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2"><History size={16} /> Recently completed</h4>
          <ul className="space-y-2 text-sm">
            {dashboard.recent_activity.map((h) => (
              <li key={h.id} className="flex justify-between gap-3">
                <span className="text-gray-700">{h.description}</span>
                <span className="text-gray-400 text-xs whitespace-nowrap">{fmtWhen(h.at)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function progressLevels() {
  return [
    { key: 'beginner', label: 'Beginner', meaning: '0–24% — started the topic and is learning fundamentals.' },
    { key: 'practitioner', label: 'Practitioner', meaning: '25–49% — building familiarity through lessons and practice.' },
    { key: 'advanced', label: 'Advanced', meaning: '50–79% — substantial progress through required activities.' },
    { key: 'expert', label: 'Expert', meaning: '80–100% — has completed most or all required activities.' },
  ];
}
