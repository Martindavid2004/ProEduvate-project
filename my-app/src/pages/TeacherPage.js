import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { useData } from '../context/DataContext';
import { teacherAPI, chatbotAPI, BACKEND_URL } from '../services/api';
import { FileText, Users, CheckSquare, Upload, Eye, Menu } from 'lucide-react';
import Modal from '../components/Modal';

const TeacherPage = () => {
  const [activeTab, setActiveTab] = useState('assignment');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { users, fetchAllData } = useData();
  
  // Assignment form
  const [assignmentTitle, setAssignmentTitle] = useState('');
  const [assignmentDesc, setAssignmentDesc] = useState('');
  const [assignmentType, setAssignmentType] = useState('Assignment');
  const [myAssignments, setMyAssignments] = useState([]);
  
  // Admin tasks
  const [adminTasks, setAdminTasks] = useState([]);
  
  // Submissions
  const [submissions, setSubmissions] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [studentSearchTerm, setStudentSearchTerm] = useState('');
  
  // Edit modal
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [expandedSubmissions, setExpandedSubmissions] = useState({});
  
  // Student profile modal
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  useEffect(() => {
    fetchAllData();
    loadTeacherAssignments();
  }, []);

  useEffect(() => {
    if (activeTab === 'assignment') {
      loadAdminTasks();
    } else if (activeTab === 'submissions') {
      loadSubmissions();
    }
  }, [activeTab]);

  const loadTeacherAssignments = async () => {
    try {
      const response = await teacherAPI.getAssignments();
      setMyAssignments(response.data);
    } catch (error) {
      console.error('Error loading assignments:', error);
    }
  };

  const loadAdminTasks = async () => {
    try {
      const response = await teacherAPI.getAdminTasks();
      setAdminTasks(response.data);
    } catch (error) {
      console.error('Error loading admin tasks:', error);
    }
  };

  const loadSubmissions = async () => {
    try {
      const response = await teacherAPI.getSubmissions();
      setSubmissions(response.data);
    } catch (error) {
      console.error('Error loading submissions:', error);
    }
  };

  const handleCreateAssignment = async () => {
    if (!assignmentTitle.trim() || !assignmentDesc.trim()) {
      alert('Please fill all fields.');
      return;
    }

    try {
      let quizQuestions = null;
      
      // If assignment type is Quiz, generate quiz questions using AI
      if (assignmentType === 'Quiz') {
        try {
          const quizResponse = await chatbotAPI.generateQuiz(assignmentTitle, 10);
          quizQuestions = quizResponse.data.questions || quizResponse.data;
        } catch (quizError) {
          console.error('Error generating quiz:', quizError);
          alert('Failed to generate quiz questions. Please try again.');
          return;
        }
      }

      await teacherAPI.createAssignment({
        title: assignmentTitle,
        description: assignmentDesc,
        type: assignmentType,
        quizQuestions: quizQuestions,
      });
      setAssignmentTitle('');
      setAssignmentDesc('');
      setAssignmentType('Assignment');
      alert(assignmentType === 'Quiz' 
        ? 'Quiz created successfully with 10 AI-generated questions!' 
        : 'Assignment created successfully!');
      await loadTeacherAssignments();
    } catch (error) {
      console.error('Error creating assignment:', error);
      alert('Failed to create assignment.');
    }
  };

  const handleEditAssignment = (assignment) => {
    setEditingAssignment({ ...assignment });
    setEditModalOpen(true);
  };

  const handleUpdateAssignment = async () => {
    if (!editingAssignment.title.trim() || !editingAssignment.description.trim()) {
      alert('Please fill all fields.');
      return;
    }

    try {
      await teacherAPI.updateAssignment(editingAssignment.id, editingAssignment);
      setEditModalOpen(false);
      setEditingAssignment(null);
      alert('Assignment updated successfully!');
      await loadTeacherAssignments();
    } catch (error) {
      console.error('Error updating assignment:', error);
      alert('Failed to update assignment.');
    }
  };

  const handleMarkTaskComplete = async (taskId) => {
    try {
      await teacherAPI.markTaskComplete(taskId);
      alert('Task marked as complete!');
      await loadAdminTasks();
    } catch (error) {
      console.error('Error marking task complete:', error);
      alert('Failed to mark task as complete.');
    }
  };

  const toggleSubmissions = (assignmentId) => {
    setExpandedSubmissions(prev => ({
      ...prev,
      [assignmentId]: !prev[assignmentId]
    }));
  };

  const sidebarItems = [
    { id: 'assignment', label: 'Admin Tasks', icon: <CheckSquare size={20} /> },
    { id: 'create', label: 'Create Assignment', icon: <FileText size={20} /> },
    { id: 'mycreated', label: 'My Assignments', icon: <FileText size={20} /> },
    { id: 'students', label: 'Student Progress', icon: <Users size={20} /> },
    { id: 'submissions', label: 'Submissions', icon: <Upload size={20} /> },
  ];

  const students = users.filter(u => u.role === 'student');

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
        <div className="bg-gray-100 shadow-lg border-b-4 border-blue-500 rounded-lg sm:rounded-xl overflow-hidden flex h-full">
          <Sidebar
            items={sidebarItems}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
          />

          <main className="flex-1 overflow-y-auto p-8 bg-gradient-to-br from-gray-50 to-slate-100">
            {/* Admin Tasks Tab */}
            {activeTab === 'assignment' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Tasks Assigned by Admin</h2>
                
                <div className="space-y-4">
                  {adminTasks.length > 0 ? (
                    adminTasks.map(task => (
                      <div key={task.id} className="bg-white p-6 rounded-xl shadow-md">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="text-lg font-bold text-gray-800">{task.title}</h3>
                            <p className="text-sm text-gray-600 mt-2">{task.description}</p>
                            <span className={`inline-block mt-3 px-3 py-1 text-xs rounded-full ${
                              task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {task.status}
                            </span>
                          </div>
                          {task.status !== 'completed' && (
                            <button
                              onClick={() => handleMarkTaskComplete(task.id)}
                              className="ml-4 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                            >
                              Mark Complete
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl shadow-md text-center">
                      <p className="text-gray-500 italic">No tasks assigned yet.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Create Assignment Tab */}
            {activeTab === 'create' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Create New Assignment</h2>
                
                <div className="bg-white p-6 rounded-xl shadow-md">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Assignment Title</label>
                      <input
                        type="text"
                        value={assignmentTitle}
                        onChange={(e) => setAssignmentTitle(e.target.value)}
                        placeholder="Enter assignment title"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Assignment Type</label>
                      <select
                        value={assignmentType}
                        onChange={(e) => setAssignmentType(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="Assignment">Assignment</option>
                        <option value="Quiz">Quiz</option>
                        <option value="Presentation">Presentation</option>
                        <option value="Project">Project</option>
                        <option value="Lab Work">Lab Work</option>
                        <option value="Case Study">Case Study</option>
                        <option value="Research Paper">Research Paper</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                      <textarea
                        value={assignmentDesc}
                        onChange={(e) => setAssignmentDesc(e.target.value)}
                        placeholder="Enter assignment description"
                        rows="4"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <button
                      onClick={handleCreateAssignment}
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                    >
                      Create Assignment
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* My Created Assignments Tab */}
            {activeTab === 'mycreated' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">My Created Assignments</h2>

                <div className="space-y-4">
                  {myAssignments.length > 0 ? (
                    myAssignments.map(assignment => (
                      <div key={assignment.id} className="bg-white p-6 rounded-xl shadow-md">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="text-lg font-bold text-gray-800">{assignment.title}</h3>
                            <p className="text-sm text-gray-600 mt-2">{assignment.description}</p>
                          </div>
                          <button
                            onClick={() => handleEditAssignment(assignment)}
                            className="ml-4 text-blue-600 hover:text-blue-800 font-medium text-sm"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl shadow-md text-center">
                      <p className="text-gray-500 italic">You have not created any assignments yet.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Student Progress Tab */}
            {activeTab === 'students' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Student Progress</h2>
                
                {/* Search Box */}
                <div className="bg-white p-4 rounded-xl shadow-md mb-6">
                  <input
                    type="text"
                    value={studentSearchTerm}
                    onChange={(e) => setStudentSearchTerm(e.target.value)}
                    placeholder="Search by student name..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Visualization Charts */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Students</h3>
                    <p className="text-4xl font-bold text-blue-600">{students.length}</p>
                  </div>
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Avg Interview Score</h3>
                    <p className="text-4xl font-bold text-green-600">
                      {students.filter(s => s.interviewScore).length > 0
                        ? Math.round(
                            students.reduce((sum, s) => sum + (s.interviewScore || 0), 0) /
                            students.filter(s => s.interviewScore).length
                          )
                        : 0}%
                    </p>
                  </div>
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Avg Resume Score</h3>
                    <p className="text-4xl font-bold text-purple-600">
                      {students.filter(s => s.resumeScore).length > 0
                        ? Math.round(
                            students.reduce((sum, s) => sum + (s.resumeScore || 0), 0) /
                            students.filter(s => s.resumeScore).length
                          )
                        : 0}%
                    </p>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-md overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assignments</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Interview Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resume Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {students
                          .filter(student => 
                            student.name.toLowerCase().includes(studentSearchTerm.toLowerCase())
                          )
                          .sort((a, b) => a.name.localeCompare(b.name))
                          .map(student => (
                          <tr key={student.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {student.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {student.submittedAssignments || 0}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {student.interviewScore ? (
                                <span className="text-green-600 font-medium">{student.interviewScore}%</span>
                              ) : (
                                <span className="text-gray-400">Not taken</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {student.resumeScore ? (
                                <span className="text-blue-600 font-medium">{student.resumeScore}%</span>
                              ) : (
                                <span className="text-gray-400">Not uploaded</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <button
                                onClick={() => {
                                  setSelectedStudent(student);
                                  setProfileModalOpen(true);
                                }}
                                className="text-blue-600 hover:text-blue-800 font-medium"
                                title="View Profile"
                              >
                                <Users size={18} />
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

            {/* Submissions Tab */}
            {activeTab === 'submissions' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Student Submissions</h2>
                
                <div className="bg-white p-4 rounded-xl shadow-md mb-6">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search by student name..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-4">
                  {submissions.length > 0 ? (
                    submissions
                      .filter(student => 
                        student.student_name.toLowerCase().includes(searchTerm.toLowerCase())
                      )
                      .sort((a, b) => a.student_name.localeCompare(b.student_name))
                      .map(student => (
                        <div key={student.student_id} className="bg-white rounded-xl shadow-md overflow-hidden">
                          <div
                            className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => toggleSubmissions(student.student_id)}
                          >
                            <div className="flex justify-between items-center">
                              <div>
                                <h3 className="text-lg font-bold text-gray-800">{student.student_name}</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                  {student.student_email}
                                </p>
                                <p className="text-sm text-gray-500 mt-1">
                                  Submitted: {student.assignments.filter(a => a.submitted).length} / {student.assignments.length} assignments
                                </p>
                              </div>
                              <span className="text-2xl">
                                {expandedSubmissions[student.student_id] ? '▲' : '▼'}
                              </span>
                            </div>
                          </div>
                          
                          {expandedSubmissions[student.student_id] && (
                            <div className="border-t border-gray-200 p-6">
                              <div className="space-y-3">
                                {student.assignments.map((assignment) => (
                                  <div key={assignment.assignment_id} className="bg-gray-50 p-4 rounded-lg">
                                    <div className="flex justify-between items-start">
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                          <h4 className="font-medium text-gray-800">{assignment.assignment_title}</h4>
                                          <span className={`px-2 py-1 text-xs rounded-full ${
                                            assignment.submitted 
                                              ? 'bg-green-100 text-green-800' 
                                              : 'bg-red-100 text-red-800'
                                          }`}>
                                            {assignment.submitted ? 'Submitted' : 'Not Submitted'}
                                          </span>
                                          <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                                            {assignment.assignment_type}
                                          </span>
                                          {assignment.submitted && assignment.submission?.quiz_score && (
                                            <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800 font-bold">
                                              Score: {Math.round(assignment.submission.quiz_score)}%
                                            </span>
                                          )}
                                        </div>
                                        
                                        {assignment.submitted && assignment.submission && (
                                          <div className="mt-2 text-sm text-gray-600">
                                            <p>File: {assignment.submission.filename}</p>
                                            <p>Submitted: {new Date(assignment.submission.submitted_at).toLocaleString()}</p>
                                            {assignment.submission.notes && (
                                              <p className="mt-1 italic">Notes: {assignment.submission.notes}</p>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                      
                                      {assignment.submitted && assignment.submission && (
                                        <a
                                          href={`${BACKEND_URL}${assignment.submission.file_path}`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="ml-4 text-blue-600 hover:text-blue-800 transition-colors p-2"
                                          title="View Submission"
                                        >
                                          <Eye size={20} />
                                        </a>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl shadow-md text-center">
                      <p className="text-gray-500 italic">No students found.</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Edit Assignment Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setEditingAssignment(null);
        }}
        title="Edit Assignment"
      >
        {editingAssignment && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Assignment Title</label>
              <input
                type="text"
                value={editingAssignment.title}
                onChange={(e) => setEditingAssignment({...editingAssignment, title: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={editingAssignment.description}
                onChange={(e) => setEditingAssignment({...editingAssignment, description: e.target.value})}
                rows="4"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={handleUpdateAssignment}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Update Assignment
            </button>
          </div>
        )}
      </Modal>

      {/* Student Profile Modal */}
      <Modal
        isOpen={profileModalOpen}
        onClose={() => {
          setProfileModalOpen(false);
          setSelectedStudent(null);
        }}
        title="Student Profile"
      >
        {selectedStudent && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
              <h3 className="text-2xl font-bold text-gray-800 mb-2">{selectedStudent.name}</h3>
              <p className="text-gray-600">{selectedStudent.email}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Interview Score</p>
                <p className="text-2xl font-bold text-green-600">
                  {selectedStudent.interviewScore ? `${selectedStudent.interviewScore}%` : 'Not taken'}
                </p>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Resume Score</p>
                <p className="text-2xl font-bold text-blue-600">
                  {selectedStudent.resumeScore ? `${selectedStudent.resumeScore}%` : 'Not uploaded'}
                </p>
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Assignments Submitted</p>
              <p className="text-2xl font-bold text-purple-600">
                {selectedStudent.submittedAssignments || 0}
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-700 mb-2">Performance Overview</h4>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Interview</span>
                    <span>{selectedStudent.interviewScore || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${selectedStudent.interviewScore || 0}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Resume</span>
                    <span>{selectedStudent.resumeScore || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${selectedStudent.resumeScore || 0}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TeacherPage;
