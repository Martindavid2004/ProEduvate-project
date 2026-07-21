import React, { createContext, useState, useContext } from 'react';
import { adminAPI } from '../services/api';

const DataContext = createContext(null);

export const DataProvider = ({ children }) => {
  const [users, setUsers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [usersResponse, assignmentsResponse] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getAssignments(),
      ]);
      setUsers(usersResponse.data);
      setAssignments(assignmentsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshUsers = async () => {
    try {
      const response = await adminAPI.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const refreshAssignments = async () => {
    try {
      const response = await adminAPI.getAssignments();
      setAssignments(response.data);
    } catch (error) {
      console.error('Error fetching assignments:', error);
    }
  };

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
