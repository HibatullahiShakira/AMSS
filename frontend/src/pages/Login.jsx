import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { LogIn, Activity } from 'lucide-react';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900 px-4">
      <div className="max-w-md w-full space-y-8 glass-card p-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-brand-500 rounded-xl flex items-center justify-center">
             <Activity className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-white">Welcome back</h2>
          <p className="mt-2 text-sm text-slate-400">
            Sign in to your autonomous financial brain
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <div className="text-rose-500 text-sm text-center bg-rose-500/10 py-2 rounded-lg border border-rose-500/20">{error}</div>}
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Username</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                className="input-field"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button type="submit" className="w-full btn-primary py-3">
            <LogIn size={20} />
            Sign in
          </button>
        </form>
        
        <div className="text-center text-sm text-slate-400">
          Don't have an account? <Link to="/register" className="text-brand-500 hover:text-brand-400 font-medium">Create one</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
