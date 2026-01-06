import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { useData } from '../context/DataContext';
import { adminAPI } from '../services/api';
import { Users, FileText, Activity, CheckSquare, Eye, Trash2, Menu, TrendingUp, BarChart3, PieChart, Loader } from 'lucide-react';
import Modal from '../components/Modal';
import {
  BarChart, Bar, PieChart as RechartsPie, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

const AdminPage = () => {
  const [activeTab, setActiveTab] = useState('users');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { users, assignments, fetchAllData, refreshUsers, refreshAssignments } = useData();
  const [roleFilter, setRoleFilter] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Form states
  const [newUserName, setNewUserName] = useState('');
  const [userRole, setUserRole] = useState('student');
  const [userDepartment, setUserDepartment] = useState('');
  const [userIdNumber, setUserIdNumber] = useState('');
  const [userSubject, setUserSubject] = useState('');
  const [userRollNo, setUserRollNo] = useState('');
  const [userCompanyName, setUserCompanyName] = useState('');
  const [userJobRoles, setUserJobRoles] = useState('');
  const [assignmentTitle, setAssignmentTitle] = useState('');
  const [assignmentDesc, setAssignmentDesc] = useState('');
  const [selectedTeacher, setSelectedTeacher] = useState('');
  const [isAddingUser, setIsAddingUser] = useState(false);
  
  // Status and tasks
  const [adminTasks, setAdminTasks] = useState([]);
  const [editingTask, setEditingTask] = useState(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [viewingUser, setViewingUser] = useState(null);
  const [viewUserModalOpen, setViewUserModalOpen] = useState(false);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  useEffect(() => {
    if (activeTab === 'tasks') {
      loadAdminTasks();
    }
  }, [activeTab]);

  // Suppress exhaustive-deps warning as loadAdminTasks is a stable function

  const loadAdminTasks = async () => {
    try {
      const response = await adminAPI.getTasks();
      setAdminTasks(response.data);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const handleAddUser = async () => {
    if (!newUserName.trim() || !userDepartment.trim() || !userIdNumber.trim()) {
      alert('Please enter name, department, and ID number.');
      return;
    }

    // Role-specific validation
    if (userRole === 'teacher' && !userSubject.trim()) {
      alert('Please enter subject for teacher.');
      return;
    }
    if (userRole === 'student' && !userRollNo.trim()) {
      alert('Please enter roll number for student.');
      return;
    }
    if (userRole === 'hr' && (!userCompanyName.trim() || !userJobRoles.trim())) {
      alert('Please enter company name and job roles for HR.');
      return;
    }

    setIsAddingUser(true);
    try {
      const userData = {
        name: newUserName,
        role: userRole,
        department: userDepartment,
        idNumber: userIdNumber,
      };

      if (userRole === 'teacher') {
        userData.subject = userSubject;
      } else if (userRole === 'student') {
        userData.rollNo = userRollNo;
      } else if (userRole === 'hr') {
        userData.companyName = userCompanyName;
        userData.jobRoles = userJobRoles;
      }

      await adminAPI.addUser(userData);
      
      // Clear all fields
      setNewUserName('');
      setUserRole('student');
      setUserDepartment('');
      setUserIdNumber('');
      setUserSubject('');
      setUserRollNo('');
      setUserCompanyName('');
      setUserJobRoles('');
      
      await refreshUsers();
      alert(`✅ Success! User "${userData.name}" has been added successfully.`);
    } catch (error) {
      console.error('Error adding user:', error);
      alert('❌ Failed to add user. Please try again.');
    } finally {
      setIsAddingUser(false);
    }
  };

  const handleRemoveUser = async (userId) => {
    if (!window.confirm('Are you sure you want to remove this user?')) return;

    try {
      await adminAPI.removeUser(userId);
      await refreshUsers();
    } catch (error) {
      console.error('Error removing user:', error);
      alert('Failed to remove user.');
    }
  };

  const handleViewUser = (user) => {
    setViewingUser(user);
    setViewUserModalOpen(true);
  };

  const handleAssignWork = async () => {
    if (!assignmentTitle.trim() || !selectedTeacher || !assignmentDesc.trim()) {
      alert('Please fill all assignment fields.');
      return;
    }

    try {
      await adminAPI.createAssignment({
        title: assignmentTitle,
        teacherId: selectedTeacher,
        description: assignmentDesc,
        status: 'pending',
        createdBy: 'admin'
      });
      
      setAssignmentTitle('');
      setSelectedTeacher('');
      setAssignmentDesc('');
      alert('Work assigned successfully!');
      
      // Refresh both assignments and admin tasks
      await refreshAssignments();
      await loadAdminTasks();
    } catch (error) {
      console.error('Error assigning work:', error);
      alert('Failed to assign work.');
    }
  };

  const handleEditTask = (task) => {
    setEditingTask(task);
    setEditModalOpen(true);
  };

  const handleUpdateTask = async () => {
    if (!editingTask.title.trim() || !editingTask.description.trim()) {
      alert('Please fill all fields.');
      return;
    }

    try {
      await adminAPI.updateTask(editingTask.id, editingTask);
      setEditModalOpen(false);
      setEditingTask(null);
      await loadAdminTasks();
      alert('Task updated successfully!');
    } catch (error) {
      console.error('Error updating task:', error);
      alert('Failed to update task.');
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;

    try {
      await adminAPI.deleteTask(taskId);
      await loadAdminTasks();
      alert('Task deleted successfully!');
    } catch (error) {
      console.error('Error deleting task:', error);
      alert('Failed to delete task.');
    }
  };

  const sidebarItems = [
    { id: 'users', label: 'Manage Users', icon: <Users size={20} /> },
    { id: 'adduser', label: 'Add User', icon: <Users size={20} /> },
    { id: 'assign', label: 'Assign Work', icon: <FileText size={20} /> },
    { id: 'status', label: 'Status', icon: <Activity size={20} /> },
    { id: 'tasks', label: 'My Tasks', icon: <CheckSquare size={20} /> },
  ];

  const students = users.filter(u => u.role === 'student');
  const teachers = users.filter(u => u.role === 'teacher');
  const interviews = students.filter(s => s.interviewScore);

  // Get unique departments
  const uniqueDepartments = [...new Set(users.map(u => u.department).filter(Boolean))];

  // Filter and sort users
  const filteredUsers = users
    .filter(user => {
      const matchesRole = !roleFilter || user.role === roleFilter;
      const matchesDepartment = !departmentFilter || user.department === departmentFilter;
      const matchesSearch = !searchQuery || 
        user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (user.idNumber && user.idNumber.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (user.rollNo && user.rollNo.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesRole && matchesDepartment && matchesSearch;
    })
    .sort((a, b) => a.name.localeCompare(b.name));

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
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          <main className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 bg-gradient-to-br from-gray-50 to-slate-100">
            {/* Manage Users Tab */}
            {activeTab === 'users' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Manage Users</h2>
                
                <div className="bg-white p-6 rounded-xl shadow-md mb-6">
                  <div className="space-y-4">
                    <div className="relative">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search by name, ID number, or roll number..."
                        className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <svg
                        className="absolute left-3 top-3 h-5 w-5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Role</label>
                      <select
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">All Roles</option>
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                        <option value="admin">Admin</option>
                        <option value="hr">HR</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Department</label>
                      <select
                        value={departmentFilter}
                        onChange={(e) => setDepartmentFilter(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">All Departments</option>
                        {uniqueDepartments.map(dept => (
                          <option key={dept} value={dept}>{dept}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-md overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredUsers.map(user => (
                          <tr key={user.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.name}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.role === 'student' ? 'bg-blue-100 text-blue-800' :
                                user.role === 'teacher' ? 'bg-green-100 text-green-800' :
                                user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {user.role}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{user.department || 'N/A'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <div className="flex items-center gap-3">
                                <button
                                  onClick={() => handleViewUser(user)}
                                  className="text-blue-600 hover:text-blue-900 hover:bg-blue-50 p-2 rounded-lg transition-colors"
                                  title="View Profile"
                                >
                                  <Eye size={18} />
                                </button>
                                <button
                                  onClick={() => handleRemoveUser(user.id)}
                                  className="text-red-600 hover:text-red-900 hover:bg-red-50 p-2 rounded-lg transition-colors"
                                  title="Remove User"
                                >
                                  <Trash2 size={18} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Add User Tab */}
            {activeTab === 'adduser' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Add New User</h2>
                
                <div className="bg-white p-6 rounded-xl shadow-md">
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Name *</label>
                        <input
                          type="text"
                          value={newUserName}
                          onChange={(e) => setNewUserName(e.target.value)}
                          placeholder="Enter user name"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Role *</label>
                        <select
                          value={userRole}
                          onChange={(e) => setUserRole(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="student">Student</option>
                          <option value="teacher">Teacher</option>
                          <option value="admin">Admin</option>
                          <option value="hr">HR</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Department *</label>
                        <input
                          type="text"
                          value={userDepartment}
                          onChange={(e) => setUserDepartment(e.target.value)}
                          placeholder="Enter department"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">ID Number *</label>
                        <input
                          type="text"
                          value={userIdNumber}
                          onChange={(e) => setUserIdNumber(e.target.value)}
                          placeholder="Enter ID number"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      {/* Conditional fields based on role */}
                      {userRole === 'teacher' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Subject *</label>
                          <input
                            type="text"
                            value={userSubject}
                            onChange={(e) => setUserSubject(e.target.value)}
                            placeholder="Enter subject"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      )}
                      
                      {userRole === 'student' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Roll Number *</label>
                          <input
                            type="text"
                            value={userRollNo}
                            onChange={(e) => setUserRollNo(e.target.value)}
                            placeholder="Enter roll number"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      )}
                      
                      {userRole === 'hr' && (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Company Name *</label>
                            <input
                              type="text"
                              value={userCompanyName}
                              onChange={(e) => setUserCompanyName(e.target.value)}
                              placeholder="Enter company name"
                              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Job Roles *</label>
                            <input
                              type="text"
                              value={userJobRoles}
                              onChange={(e) => setUserJobRoles(e.target.value)}
                              placeholder="Enter job roles"
                              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                        </>
                      )}
                    </div>
                    
                    <button
                      onClick={handleAddUser}
                      disabled={isAddingUser}
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isAddingUser ? (
                        <>
                          <Loader className="animate-spin" size={20} />
                          Adding User...
                        </>
                      ) : (
                        'Add User'
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Assign Work Tab */}
            {activeTab === 'assign' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Assign Work to Teacher</h2>
                
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
                      <label className="block text-sm font-medium text-gray-700 mb-2">Assign to Teacher</label>
                      <select
                        value={selectedTeacher}
                        onChange={(e) => setSelectedTeacher(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select Teacher</option>
                        {teachers.map(teacher => (
                          <option key={teacher.id} value={teacher.id}>{teacher.name}</option>
                        ))}
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
                      onClick={handleAssignWork}
                      className="w-full bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                    >
                      Assign Work
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Status Tab */}
            {activeTab === 'status' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800 flex items-center gap-3">
                  <TrendingUp className="text-blue-600" size={36} />
                  Analytics & Progress Dashboard
                </h2>
                
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl shadow-lg text-white">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-blue-100 text-sm font-medium">Total Students</p>
                        <p className="text-4xl font-bold mt-2">{students.length}</p>
                      </div>
                      <div className="bg-blue-400 bg-opacity-50 p-3 rounded-lg">
                        <Users size={24} />
                      </div>
                    </div>
                    <p className="text-blue-100 text-xs mt-4">Active learners in system</p>
                  </div>

                  <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl shadow-lg text-white">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-green-100 text-sm font-medium">Total Teachers</p>
                        <p className="text-4xl font-bold mt-2">{teachers.length}</p>
                      </div>
                      <div className="bg-green-400 bg-opacity-50 p-3 rounded-lg">
                        <Users size={24} />
                      </div>
                    </div>
                    <p className="text-green-100 text-xs mt-4">Educators managing courses</p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl shadow-lg text-white">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-purple-100 text-sm font-medium">Assignments</p>
                        <p className="text-4xl font-bold mt-2">{assignments.length}</p>
                      </div>
                      <div className="bg-purple-400 bg-opacity-50 p-3 rounded-lg">
                        <FileText size={24} />
                      </div>
                    </div>
                    <p className="text-purple-100 text-xs mt-4">Total tasks created</p>
                  </div>

                  <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl shadow-lg text-white">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-orange-100 text-sm font-medium">Interviews</p>
                        <p className="text-4xl font-bold mt-2">{interviews.length}</p>
                      </div>
                      <div className="bg-orange-400 bg-opacity-50 p-3 rounded-lg">
                        <CheckSquare size={24} />
                      </div>
                    </div>
                    <p className="text-orange-100 text-xs mt-4">Completed assessments</p>
                  </div>
                </div>

                {/* Charts Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  {/* Student Progress Distribution Pie Chart */}
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">
                      <PieChart size={24} className="text-blue-600" />
                      Student Performance Distribution
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <RechartsPie>
                        <Pie
                          data={[
                            { name: 'Excellent (75-100%)', value: students.filter(s => {
                              const score = s.interviewScore || s.average_score || Math.floor(Math.random() * 100);
                              return score >= 75;
                            }).length, color: '#10B981' },
                            { name: 'Good (50-74%)', value: students.filter(s => {
                              const score = s.interviewScore || s.average_score || Math.floor(Math.random() * 100);
                              return score >= 50 && score < 75;
                            }).length, color: '#3B82F6' },
                            { name: 'Fair (25-49%)', value: students.filter(s => {
                              const score = s.interviewScore || s.average_score || Math.floor(Math.random() * 100);
                              return score >= 25 && score < 50;
                            }).length, color: '#F59E0B' },
                            { name: 'Needs Improvement', value: students.filter(s => {
                              const score = s.interviewScore || s.average_score || Math.floor(Math.random() * 100);
                              return score < 25;
                            }).length, color: '#EF4444' }
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, value }) => value > 0 ? `${name.split(' ')[0]}: ${value}` : ''}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[
                            { name: 'Excellent', value: students.filter(s => (s.interviewScore || s.average_score || 50) >= 75).length, color: '#10B981' },
                            { name: 'Good', value: students.filter(s => { const sc = s.interviewScore || s.average_score || 50; return sc >= 50 && sc < 75; }).length, color: '#3B82F6' },
                            { name: 'Fair', value: students.filter(s => { const sc = s.interviewScore || s.average_score || 50; return sc >= 25 && sc < 50; }).length, color: '#F59E0B' },
                            { name: 'Needs Improvement', value: students.filter(s => (s.interviewScore || s.average_score || 50) < 25).length, color: '#EF4444' }
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </RechartsPie>
                    </ResponsiveContainer>
                  </div>

                  {/* Department-wise Distribution */}
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">
                      <BarChart3 size={24} className="text-green-600" />
                      Department Distribution
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={uniqueDepartments.map(dept => ({
                        name: dept,
                        students: users.filter(u => u.department === dept && u.role === 'student').length,
                        teachers: users.filter(u => u.department === dept && u.role === 'teacher').length
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="students" fill="#3B82F6" name="Students" />
                        <Bar dataKey="teachers" fill="#10B981" name="Teachers" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Teacher Workload Chart */}
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">
                      <FileText size={24} className="text-purple-600" />
                      Teacher Workload Analysis
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={teachers.map(teacher => ({
                        name: teacher.name.split(' ')[0],
                        assignments: assignments.filter(a => a.teacherId === teacher.id).length,
                        capacity: 10
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="assignments" fill="#8B5CF6" name="Assigned Tasks" />
                        <Bar dataKey="capacity" fill="#E5E7EB" name="Capacity" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Student Progress Trend */}
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">
                      <Activity size={24} className="text-indigo-600" />
                      Overall Performance Metrics
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={[
                        {
                          metric: 'Attendance',
                          value: 85
                        },
                        {
                          metric: 'Assignment Completion',
                          value: students.length > 0 ? Math.round((students.filter(s => s.submittedAssignments > 0).length / students.length) * 100) : 0
                        },
                        {
                          metric: 'Interview Success',
                          value: interviews.length > 0 ? Math.round(interviews.reduce((sum, s) => sum + s.interviewScore, 0) / interviews.length) : 0
                        },
                        {
                          metric: 'Teacher Efficiency',
                          value: teachers.length > 0 ? Math.min(Math.round((assignments.length / teachers.length) * 10), 100) : 0
                        },
                        {
                          metric: 'Overall Progress',
                          value: students.length > 0 ? Math.round(students.reduce((sum, s) => sum + (s.average_score || 0), 0) / students.length) : 0
                        }
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                        <Radar name="Metrics" dataKey="value" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Top Performers Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  {/* Student Progress Table */}
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-bold mb-4 text-gray-800">Top Performing Students</h3>
                    <div className="space-y-3">
                      {students.length > 0 ? (
                        students
                          .sort((a, b) => (b.interviewScore || b.average_score || 0) - (a.interviewScore || a.average_score || 0))
                          .slice(0, 5)
                          .map((student, index) => {
                            const score = student.interviewScore || student.average_score || Math.floor(Math.random() * 100);
                            return (
                              <div key={student.id} className="flex items-center gap-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                                <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">
                                  {index + 1}
                                </div>
                                <div className="flex-1">
                                  <p className="font-semibold text-gray-800">{student.name}</p>
                                  <p className="text-xs text-gray-500">{student.department || 'N/A'}</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-lg font-bold text-blue-600">{score}%</p>
                                </div>
                              </div>
                            );
                          })
                      ) : (
                        <p className="text-gray-500 italic text-center py-8">No students enrolled yet</p>
                      )}
                    </div>
                  </div>

                  {/* Department Performance */}
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-bold mb-4 text-gray-800">Department Performance Overview</h3>
                    <div className="space-y-3">
                      {uniqueDepartments.length > 0 ? (
                        uniqueDepartments.map(dept => {
                          const deptStudents = users.filter(u => u.department === dept && u.role === 'student');
                          const deptTeachers = users.filter(u => u.department === dept && u.role === 'teacher');
                          const avgScore = deptStudents.length > 0
                            ? Math.round(deptStudents.reduce((sum, s) => sum + (s.average_score || 50), 0) / deptStudents.length)
                            : 0;
                          
                          return (
                            <div key={dept} className="p-4 bg-gradient-to-r from-gray-50 to-slate-100 rounded-lg border-l-4 border-purple-500">
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="font-bold text-gray-800">{dept}</h4>
                                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                                  {avgScore}% avg
                                </span>
                              </div>
                              <div className="grid grid-cols-2 gap-4 mt-3">
                                <div>
                                  <p className="text-xs text-gray-500">Students</p>
                                  <p className="text-lg font-bold text-blue-600">{deptStudents.length}</p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500">Teachers</p>
                                  <p className="text-lg font-bold text-green-600">{deptTeachers.length}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <p className="text-gray-500 italic text-center py-8">No departments assigned yet</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Teacher Activity Details */}
                <div className="bg-white p-6 rounded-xl shadow-lg">
                  <h3 className="text-xl font-bold mb-4 text-gray-800">Teacher Activity & Assignments</h3>
                  <div className="space-y-3">
                    {teachers.length > 0 ? (
                      teachers.map(teacher => {
                        const teacherAssignments = assignments.filter(a => a.teacherId === teacher.id);
                        const workload = teacherAssignments.length;
                        const workloadPercent = Math.min((workload / 10) * 100, 100);
                        const workloadStatus = workload >= 8 ? 'High Load' : workload >= 4 ? 'Moderate' : 'Available';
                        const statusColor = workload >= 8 ? 'bg-red-100 text-red-700' : workload >= 4 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700';
                        
                        return (
                          <div key={teacher.id} className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-center mb-3">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center text-white font-bold">
                                  {teacher.name.charAt(0)}
                                </div>
                                <div>
                                  <h4 className="font-semibold text-gray-800">{teacher.name}</h4>
                                  <p className="text-xs text-gray-500">{teacher.subject || teacher.department || 'General'}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor}`}>
                                  {workloadStatus}
                                </span>
                                <p className="text-xs text-gray-500 mt-1">{workload} tasks</p>
                              </div>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2.5">
                              <div className="bg-gradient-to-r from-green-400 to-green-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${workloadPercent}%` }}></div>
                            </div>
                            <div className="flex justify-between mt-2">
                              <span className="text-xs text-gray-500">Workload</span>
                              <span className="text-xs font-semibold text-gray-700">{workloadPercent.toFixed(0)}% of capacity</span>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-gray-500 italic text-center py-8">No teachers assigned yet</p>
                    )}
                  </div>
                </div>

                {/* Key Insights */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-100 p-6 rounded-xl border-l-4 border-blue-500">
                    <h4 className="font-bold text-gray-800 mb-2">Average Student Score</h4>
                    <p className="text-3xl font-bold text-blue-600">
                      {students.length > 0
                        ? Math.round(students.reduce((sum, s) => sum + (s.average_score || 50), 0) / students.length)
                        : 0}%
                    </p>
                    <p className="text-sm text-gray-600 mt-2">Overall performance</p>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-emerald-100 p-6 rounded-xl border-l-4 border-green-500">
                    <h4 className="font-bold text-gray-800 mb-2">Assignment Completion</h4>
                    <p className="text-3xl font-bold text-green-600">
                      {students.length > 0
                        ? Math.round((students.filter(s => s.submittedAssignments > 0).length / students.length) * 100)
                        : 0}%
                    </p>
                    <p className="text-sm text-gray-600 mt-2">Students with submissions</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-violet-100 p-6 rounded-xl border-l-4 border-purple-500">
                    <h4 className="font-bold text-gray-800 mb-2">Teacher-Student Ratio</h4>
                    <p className="text-3xl font-bold text-purple-600">
                      1:{teachers.length > 0 ? Math.round(students.length / teachers.length) : 0}
                    </p>
                    <p className="text-sm text-gray-600 mt-2">Optimal distribution</p>
                  </div>
                </div>
              </div>
            )}

            {/* Tasks Tab */}
            {activeTab === 'tasks' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">My Created Tasks</h2>
                <p className="text-gray-600 mb-6">View, edit, and manage all tasks created by you as admin</p>
                
                <div className="space-y-4">
                  {adminTasks.length > 0 ? (
                    adminTasks.map(task => (
                      <div key={task.id} className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-lg font-bold text-gray-800">{task.title}</h3>
                              <span className={`px-3 py-1 text-xs rounded-full font-semibold ${
                                task.status === 'completed' ? 'bg-green-100 text-green-800' : 
                                task.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {task.status || 'pending'}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-2 mb-3">{task.description}</p>
                            <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                              <div className="flex items-center gap-1">
                                <Users size={14} />
                                <span>Assigned to: <span className="font-semibold text-gray-700">{task.teacherName || 'Unknown'}</span></span>
                              </div>
                              <div className="flex items-center gap-1">
                                <Activity size={14} />
                                <span>Created by: <span className="font-semibold text-gray-700">Admin</span></span>
                              </div>
                            </div>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <button
                              onClick={() => handleEditTask(task)}
                              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              Edit
                            </button>
                            <button
                              onClick={() => handleDeleteTask(task.id)}
                              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl shadow-md text-center">
                      <FileText size={48} className="mx-auto text-gray-300 mb-4" />
                      <p className="text-gray-500 text-lg font-medium">No tasks created yet</p>
                      <p className="text-gray-400 text-sm mt-2">Create a new task in the "Assign Work" section</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Edit Task Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setEditingTask(null);
        }}
        title="Edit Task"
      >
        {editingTask && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Task Title</label>
              <input
                type="text"
                value={editingTask.title}
                onChange={(e) => setEditingTask({...editingTask, title: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Assign to Teacher</label>
              <select
                value={editingTask.teacherId}
                onChange={(e) => setEditingTask({...editingTask, teacherId: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {teachers.map(teacher => (
                  <option key={teacher.id} value={teacher.id}>{teacher.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={editingTask.description}
                onChange={(e) => setEditingTask({...editingTask, description: e.target.value})}
                rows="4"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={handleUpdateTask}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Update Task
            </button>
          </div>
        )}
      </Modal>

      {/* View User Profile Modal */}
      <Modal
        isOpen={viewUserModalOpen}
        onClose={() => {
          setViewUserModalOpen(false);
          setViewingUser(null);
        }}
        title="User Profile"
      >
        {viewingUser && (
          <div className="space-y-4">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="bg-blue-500 text-white rounded-full w-16 h-16 flex items-center justify-center text-2xl font-bold">
                  {viewingUser.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-800">{viewingUser.name}</h3>
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    viewingUser.role === 'student' ? 'bg-blue-100 text-blue-800' :
                    viewingUser.role === 'teacher' ? 'bg-green-100 text-green-800' :
                    viewingUser.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {viewingUser.role.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <label className="text-xs font-semibold text-gray-500 uppercase">Department</label>
                <p className="text-gray-800 font-medium mt-1">{viewingUser.department || 'Not specified'}</p>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <label className="text-xs font-semibold text-gray-500 uppercase">ID Number</label>
                <p className="text-gray-800 font-medium mt-1">{viewingUser.idNumber || 'Not specified'}</p>
              </div>

              {viewingUser.role === 'student' && viewingUser.rollNo && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-xs font-semibold text-gray-500 uppercase">Roll Number</label>
                  <p className="text-gray-800 font-medium mt-1">{viewingUser.rollNo}</p>
                </div>
              )}

              {viewingUser.role === 'teacher' && viewingUser.subject && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="text-xs font-semibold text-gray-500 uppercase">Subject</label>
                  <p className="text-gray-800 font-medium mt-1">{viewingUser.subject}</p>
                </div>
              )}

              {viewingUser.role === 'hr' && (
                <>
                  {viewingUser.companyName && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-xs font-semibold text-gray-500 uppercase">Company Name</label>
                      <p className="text-gray-800 font-medium mt-1">{viewingUser.companyName}</p>
                    </div>
                  )}
                  {viewingUser.jobRoles && (
                    <div className="bg-gray-50 p-4 rounded-lg md:col-span-2">
                      <label className="text-xs font-semibold text-gray-500 uppercase">Job Roles</label>
                      <p className="text-gray-800 font-medium mt-1">{viewingUser.jobRoles}</p>
                    </div>
                  )}
                </>
              )}

              {viewingUser.role === 'student' && (
                <>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-xs font-semibold text-gray-500 uppercase">Submitted Assignments</label>
                    <p className="text-gray-800 font-medium mt-1">{viewingUser.submittedAssignments || 0}</p>
                  </div>
                  {viewingUser.interviewScore && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-xs font-semibold text-gray-500 uppercase">Interview Score</label>
                      <p className="text-gray-800 font-medium mt-1">{viewingUser.interviewScore}%</p>
                    </div>
                  )}
                  {viewingUser.resumeScore && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-xs font-semibold text-gray-500 uppercase">Resume Score</label>
                      <p className="text-gray-800 font-medium mt-1">{viewingUser.resumeScore}%</p>
                    </div>
                  )}
                  {viewingUser.quizScore && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <label className="text-xs font-semibold text-gray-500 uppercase">Quiz Score</label>
                      <p className="text-gray-800 font-medium mt-1">{viewingUser.quizScore}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AdminPage;
