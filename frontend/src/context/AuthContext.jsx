import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [business, setBusiness] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const res = await api.get('/auth/users/me/');
          setUser(res.data);
          // If the user has a business attached, the API might not return it directly from Djoser's /me/.
          // We can try to fetch the business if they have an ID, or assume the backend handles it.
          // For now, if the user object has a business ID, we set it.
          if (res.data.business) {
             setBusiness(res.data.business);
          }
        } catch (error) {
          console.error("Token invalid or expired");
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (username, password) => {
    const res = await api.post('/auth/jwt/create/', { username, password });
    localStorage.setItem('access_token', res.data.access);
    localStorage.setItem('refresh_token', res.data.refresh);
    
    // Fetch user details after login
    const userRes = await api.get('/auth/users/me/');
    setUser(userRes.data);
    if (userRes.data.business) {
      setBusiness(userRes.data.business);
    }
  };

  const register = async (userData) => {
    await api.post('/auth/users/', userData);
    // Automatically login after successful registration
    await login(userData.username, userData.password);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setBusiness(null);
  };

  const completeOnboarding = async (businessData) => {
    const res = await api.post('/user-business/business/', businessData);
    setBusiness(res.data.id);
    
    // Refetch user to get the updated business association
    const userRes = await api.get('/auth/users/me/');
    setUser(userRes.data);
  };

  return (
    <AuthContext.Provider value={{ user, business, loading, login, register, logout, completeOnboarding }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
