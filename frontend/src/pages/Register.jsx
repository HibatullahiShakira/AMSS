import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { UserPlus, Activity } from 'lucide-react';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  });
  const [error, setError] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(formData);
      navigate('/onboarding'); // Redirect to business setup after signup
    } catch (err) {
      setError('Failed to register. Please check your details.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900 px-4 py-12">
      <div className="max-w-md w-full space-y-8 glass-card p-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-brand-500 rounded-xl flex items-center justify-center">
             <Activity className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-white">Create an Account</h2>
          <p className="mt-2 text-sm text-slate-400">
            Join AMSS Enterprise
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <div className="text-rose-500 text-sm text-center bg-rose-500/10 py-2 rounded-lg border border-rose-500/20">{error}</div>}
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">First Name</label>
              <input type="text" name="first_name" required className="input-field" onChange={handleChange} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Last Name</label>
              <input type="text" name="last_name" required className="input-field" onChange={handleChange} />
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Username</label>
              <input type="text" name="username" required className="input-field" onChange={handleChange} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
              <input type="email" name="email" required className="input-field" onChange={handleChange} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <input type="password" name="password" required className="input-field" onChange={handleChange} />
            </div>
          </div>

          <button type="submit" className="w-full btn-primary py-3">
            <UserPlus size={20} />
            Sign Up
          </button>
        </form>
        
        <div className="text-center text-sm text-slate-400">
          Already have an account? <Link to="/login" className="text-brand-500 hover:text-brand-400 font-medium">Sign in</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
