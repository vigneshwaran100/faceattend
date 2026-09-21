import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { LoginRequest } from '../types/api';

export function useAuth() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(authService.isAuthenticated());
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
      navigate('/login');
    };

    window.addEventListener('faceattend_unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('faceattend_unauthorized', handleUnauthorized);
    };
  }, [navigate]);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      setLoading(true);
      setError(null);
      try {
        await authService.login(credentials);
        setIsAuthenticated(true);
        navigate('/dashboard');
      } catch (err: any) {
        setError(err.message || 'Login failed. Please check credentials.');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [navigate]
  );

  const logout = useCallback(() => {
    authService.logout();
    setIsAuthenticated(false);
    navigate('/login');
  }, [navigate]);

  return {
    isAuthenticated,
    loading,
    error,
    login,
    logout,
    clearError: () => setError(null),
  };
}
