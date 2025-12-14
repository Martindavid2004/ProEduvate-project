import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Modal from '../components/Modal';
import { useData } from '../context/DataContext';
import { hrAPI } from '../services/api';
import { Users, Award, FileText, Eye, Download, Search, Filter, Trophy, BarChart3, CheckCircle, Menu } from 'lucide-react';

const HRPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { users, fetchAllData } = useData();
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [sortBy, setSortBy] = useState('atsScore');
  const [studentActions, setStudentActions] = useState({});

  useEffect(() => {
    fetchAllData();
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    try {
      const response = await hrAPI.getCandidates();
      setCandidates(response.data);
    } catch (error) {
      console.error('Error loading candidates:', error);
      // Fallback to students from users
      const students = users.filter(u => u.role === 'student');
      setCandidates(students);
    }
  };

  const viewCandidateDetails = (candidate) => {
    setSelectedCandidate(candidate);
    setModalOpen(true);
  };

  const viewResume = (candidate) => {
    // Check if candidate has a resume
    if (!candidate.resume_filename) {
      alert('No resume uploaded for this candidate.');
      return;
    }
    // Open resume in new tab
    const resumeUrl = `http://localhost:5000/resumes/${candidate.resume_filename}`;
    window.open(resumeUrl, '_blank');
  };

  const updateStudentAction = (studentId, action) => {
    setStudentActions(prev => ({
      ...prev,
      [studentId]: action
    }));
  };

  const sidebarItems = [
    { id: 'overview', label: 'Overview', icon: <BarChart3 size={20} /> },
    { id: 'candidates', label: 'Candidates', icon: <Users size={20} /> },
  ];

  const students = users.filter(u => u.role === 'student');
  
  // Get unique departments
  const departments = ['all', ...new Set(students.map(s => s.department).filter(Boolean))];
  
  // Filter students based on search term and department
  const filteredStudents = students.filter(student => {
    const matchesSearch = student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          student.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          student.rollNo?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDepartment = selectedDepartment === 'all' || student.department === selectedDepartment;
    return matchesSearch && matchesDepartment;
  }).sort((a, b) => {
    switch(sortBy) {
      case 'atsScore':
        return (b.resumeScore || b.atsScore || 0) - (a.resumeScore || a.atsScore || 0);
      case 'name':
        return a.name.localeCompare(b.name);
      case 'interviewScore':
        return (b.interviewScore || 0) - (a.interviewScore || 0);
      case 'trainingScore':
        return (b.trainingScore || b.average_score || 0) - (a.trainingScore || a.average_score || 0);
      default:
        return 0;
    }
  });
  
  const interviewedCandidates = filteredStudents.filter(s => s.interviewScore);
  
  const shortlistedStudents = filteredStudents.filter(s => studentActions[s.id] === 'shortlisted');
  const hiredStudents = filteredStudents.filter(s => studentActions[s.id] === 'hired');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Floating Menu Button for Mobile */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="floating-menu-btn md:hidden"
      >
        <Menu size={24} className="text-gray-700" />
      </button>

      <div className="max-w-7xl mx-auto p-2 sm:p-4 h-screen">
        <div className="bg-gray-100 shadow-lg border-b-4 border-blue-500 rounded-lg sm:rounded-xl overflow-hidden flex flex-col h-full">
          {/* Logo Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-blue-500 p-4 flex items-center justify-center">
            <img src="/logo.png" alt="ProEduvate Logo" className="h-16 w-auto" />
          </div>
          
          <div className="flex flex-1 overflow-hidden">
            <Sidebar
              items={sidebarItems}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
            />

            <main className="flex-1 overflow-y-auto p-8 bg-gradient-to-br from-gray-50 to-slate-100">
            {/* Search and Filter Bar */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search by name, email, or roll number..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <select
                  value={selectedDepartment}
                  onChange={(e) => setSelectedDepartment(e.target.value)}
                  className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white cursor-pointer"
                >
                  <option value="all">All Departments</option>
                  {departments.filter(d => d !== 'all').map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="pl-4 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white cursor-pointer font-medium"
                >
                  <option value="atsScore">Sort by ATS Score</option>
                  <option value="name">Sort by Name</option>
                  <option value="interviewScore">Sort by Interview Score</option>
                  <option value="trainingScore">Sort by Training Score</option>
                </select>
              </div>
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Recruitment Overview</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-xl shadow-lg text-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold opacity-90">Total Students</h3>
                        <p className="text-5xl font-bold mt-2">{filteredStudents.length}</p>
                      </div>
                      <Users size={60} className="opacity-80" />
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-green-500 to-green-600 p-6 rounded-xl shadow-lg text-white">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold opacity-90">Shortlisted</h3>
                        <p className="text-5xl font-bold mt-2">{shortlistedStudents.length}</p>
                      </div>
                      <CheckCircle size={60} className="opacity-80" />
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-md overflow-hidden">
                  <div className="px-6 py-4 bg-gray-50 border-b">
                    <h3 className="text-xl font-bold text-gray-800">Student Status</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Skills</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ATS Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredStudents.map(student => (
                          <tr key={student.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{student.name}</div>
                              <div className="text-xs text-gray-500">{student.email}</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-wrap gap-1">
                                {student.matchingSkills && student.matchingSkills.length > 0 ? (
                                  student.matchingSkills.slice(0, 3).map((skill, index) => (
                                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                      {skill}
                                    </span>
                                  ))
                                ) : (
                                  <span className="text-xs text-gray-400">No skills listed</span>
                                )}
                                {student.matchingSkills && student.matchingSkills.length > 3 && (
                                  <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                    +{student.matchingSkills.length - 3}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {student.resumeScore || student.atsScore ? (
                                <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full font-medium text-sm">
                                  {student.resumeScore || student.atsScore}%
                                </span>
                              ) : (
                                <span className="text-gray-400 text-sm">N/A</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <select
                                value={studentActions[student.id] || 'open'}
                                onChange={(e) => updateStudentAction(student.id, e.target.value)}
                                className={`px-3 py-1 rounded-full text-sm font-medium border-0 focus:ring-2 focus:ring-blue-500 cursor-pointer ${
                                  studentActions[student.id] === 'shortlisted' ? 'bg-yellow-100 text-yellow-800' :
                                  studentActions[student.id] === 'hired' ? 'bg-green-100 text-green-800' :
                                  studentActions[student.id] === 'interviewed' ? 'bg-blue-100 text-blue-800' :
                                  'bg-gray-100 text-gray-700'
                                }`}
                              >
                                <option value="open">Open</option>
                                <option value="shortlisted">Shortlisted</option>
                                <option value="interviewed">Interviewed</option>
                                <option value="hired">Hired</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Candidates Tab */}
            {activeTab === 'candidates' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">All Candidates</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
                    <h3 className="text-lg font-semibold text-gray-600">Total Candidates</h3>
                    <p className="text-4xl font-bold text-blue-600 mt-2">{filteredStudents.length}</p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
                    <h3 className="text-lg font-semibold text-gray-600">Interviewed</h3>
                    <p className="text-4xl font-bold text-green-600 mt-2">{interviewedCandidates.length}</p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
                    <h3 className="text-lg font-semibold text-gray-600">Hired</h3>
                    <p className="text-4xl font-bold text-purple-600 mt-2">{hiredStudents.length}</p>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-md overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assignments</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Interview Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resume Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredStudents.map(student => (
                          <tr key={student.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{student.name}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {student.submittedAssignments || 0}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {student.interviewScore ? (
                                <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full font-medium">
                                  {student.interviewScore}%
                                </span>
                              ) : (
                                <span className="text-gray-400">Not taken</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {student.resumeScore ? (
                                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">
                                  {student.resumeScore}%
                                </span>
                              ) : (
                                <span className="text-gray-400">Not uploaded</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <button
                                onClick={() => viewCandidateDetails(student)}
                                className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded-lg transition-colors"
                                title="View Details"
                              >
                                <Eye size={20} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
            </main>
          </div>
        </div>
      </div>

      {/* Candidate Details Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedCandidate(null);
        }}
        title=""
        maxWidth="900px"
      >
        {selectedCandidate && (
          <div className="space-y-6">
            {/* Header Section */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-8 rounded-xl shadow-lg -mt-6 -mx-6 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center text-blue-600 font-bold text-3xl shadow-lg">
                  {selectedCandidate.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1">
                  <h3 className="text-3xl font-bold">{selectedCandidate.name}</h3>
                  <p className="text-blue-100 mt-2 text-lg">
                    {selectedCandidate.rollNo || selectedCandidate.idNumber || 'N/A'} • 
                    {selectedCandidate.department && ` ${selectedCandidate.department} • `}
                    Avg Score: {selectedCandidate.average_score || 0}%
                  </p>
                </div>
                <div className="text-right">
                  <div className="px-4 py-2 bg-white bg-opacity-20 rounded-lg backdrop-blur-sm">
                    <p className="text-xs uppercase tracking-wider text-blue-100">Status</p>
                    <p className="text-lg font-bold">
                      {studentActions[selectedCandidate.id] 
                        ? studentActions[selectedCandidate.id].charAt(0).toUpperCase() + studentActions[selectedCandidate.id].slice(1)
                        : 'Open'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Core Skills Section */}
            <div className="bg-gradient-to-br from-gray-50 to-slate-100 p-6 rounded-xl border border-gray-200 shadow-md">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                  <Award size={20} className="text-white" />
                </div>
                <h4 className="font-bold text-gray-800 text-xl">Core Skills</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedCandidate.matchingSkills && selectedCandidate.matchingSkills.length > 0 ? (
                  selectedCandidate.matchingSkills.map((skill, index) => (
                    <span key={index} className="px-4 py-2 bg-white text-blue-700 rounded-lg font-semibold shadow-sm border border-blue-200 hover:shadow-md transition-shadow">
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500 italic">No skills listed</span>
                )}
              </div>
            </div>

            {/* Stats Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-emerald-100 p-6 rounded-xl border border-green-200 shadow-lg hover:shadow-xl transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-700 font-semibold mb-2 uppercase tracking-wide">Interview Score</p>
                    <p className="text-5xl font-bold text-green-700">
                      {selectedCandidate.interviewScore || 'N/A'}
                      {selectedCandidate.interviewScore && <span className="text-2xl">%</span>}
                    </p>
                  </div>
                  <div className="p-3 bg-green-200 rounded-full">
                    <Award size={32} className="text-green-700" />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-green-200">
                  <p className="text-xs text-green-700 font-medium">
                    {selectedCandidate.interviewScore ? '✓ Interview Completed' : 'Pending'}
                  </p>
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-orange-50 to-amber-100 p-6 rounded-xl border border-orange-200 shadow-lg hover:shadow-xl transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-700 font-semibold mb-2 uppercase tracking-wide">Training Score</p>
                    <p className="text-5xl font-bold text-orange-700">
                      {selectedCandidate.trainingScore || selectedCandidate.average_score || 'N/A'}
                      {(selectedCandidate.trainingScore || selectedCandidate.average_score) && <span className="text-2xl">%</span>}
                    </p>
                  </div>
                  <div className="p-3 bg-orange-200 rounded-full">
                    <Trophy size={32} className="text-orange-700" />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-orange-200">
                  <p className="text-xs text-orange-700 font-medium">
                    Average Performance
                  </p>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-violet-100 p-6 rounded-xl border border-purple-200 shadow-lg hover:shadow-xl transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-700 font-semibold mb-2 uppercase tracking-wide">Resume Score</p>
                    <p className="text-5xl font-bold text-purple-700">
                      {selectedCandidate.resumeScore || selectedCandidate.atsScore || 'N/A'}
                      {(selectedCandidate.resumeScore || selectedCandidate.atsScore) && <span className="text-2xl">%</span>}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-200 rounded-full">
                    <FileText size={32} className="text-purple-700" />
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-purple-200">
                  <p className="text-xs text-purple-700 font-medium">
                    ATS Compatibility
                  </p>
                </div>
              </div>
            </div>

            {/* Resume Section */}
            {selectedCandidate.resume_filename && (
              <div className="bg-gradient-to-br from-indigo-50 to-blue-100 p-6 rounded-xl border border-indigo-200 shadow-md">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
                    <FileText size={20} className="text-white" />
                  </div>
                  <h4 className="font-bold text-gray-800 text-xl">Resume Document</h4>
                </div>
                <div className="flex items-center justify-between bg-white p-5 rounded-xl shadow-sm">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                      <FileText size={24} className="text-red-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">{selectedCandidate.resume_filename.split('_').slice(1).join('_') || selectedCandidate.resume_filename}</p>
                      <p className="text-sm text-gray-500 mt-1">PDF Document</p>
                    </div>
                  </div>
                  <button
                    onClick={() => viewResume(selectedCandidate)}
                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2"
                  >
                    <Eye size={20} />
                    Preview
                  </button>
                </div>
              </div>
            )}

            {/* Recruitment Actions */}
            <div className="bg-gradient-to-br from-slate-50 to-gray-100 p-6 rounded-xl border border-gray-200 shadow-md">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg flex items-center justify-center">
                  <CheckCircle size={20} className="text-white" />
                </div>
                <h4 className="font-bold text-gray-800 text-xl">Recruitment Actions</h4>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  onClick={() => {
                    updateStudentAction(selectedCandidate.id, 'shortlisted');
                    alert('Candidate shortlisted successfully!');
                  }}
                  className="px-6 py-4 bg-gradient-to-r from-yellow-500 to-amber-500 hover:from-yellow-600 hover:to-amber-600 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                >
                  <CheckCircle size={20} />
                  Shortlist
                </button>
                <button
                  onClick={() => {
                    updateStudentAction(selectedCandidate.id, 'open');
                    alert('Candidate rejected');
                  }}
                  className="px-6 py-4 bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                >
                  ✕ Reject
                </button>
                <button
                  onClick={() => {
                    updateStudentAction(selectedCandidate.id, 'interviewed');
                    alert('Interview scheduled');
                  }}
                  className="px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
                >
                  <Award size={20} />
                  Schedule Interview
                </button>
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setModalOpen(false)}
              className="w-full bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default HRPage;
