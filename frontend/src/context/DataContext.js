import React, { createContext, useState, useContext, useEffect } from 'react';
import { adminAPI } from '../services/api';
import { useAuth } from './AuthContext';

const DataContext = createContext(null);

export const DataProvider = ({ children }) => {
  const [users, setUsers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  // Fetch admin data only when user is admin or teacher
  const fetchAllData = async () => {
    // Only admins and teachers can access admin endpoints
    if (user?.role !== 'admin' && user?.role !== 'teacher') {
      console.log('Skipping admin data fetch - user is not admin/teacher');
      return;
    }

    setLoading(true);
    try {
      const [usersResponse, assignmentsResponse] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getAssignments(),
      ]);
      setUsers(usersResponse.data);
      setAssignments(assignmentsResponse.data);
    } catch (error) {
      console.error('Error fetching admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshUsers = async () => {
    if (user?.role !== 'admin' && user?.role !== 'teacher') {
      console.log('Skipping user refresh - user is not admin/teacher');
      return;
    }
    try {
      const response = await adminAPI.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const refreshAssignments = async () => {
    if (user?.role !== 'admin' && user?.role !== 'teacher') {
      console.log('Skipping assignment refresh - user is not admin/teacher');
      return;
    }
    try {
      const response = await adminAPI.getAssignments();
      setAssignments(response.data);
    } catch (error) {
      console.error('Error fetching assignments:', error);
    }
  };

  // Auto-fetch data when user logs in (for admins/teachers)
  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'teacher') {
      fetchAllData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  return (
    <DataContext.Provider value={{ 
      users, 
      assignments, 
      loading, 
      fetchAllData, 
      refreshUsers, 
      refreshAssignments 
    }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};
