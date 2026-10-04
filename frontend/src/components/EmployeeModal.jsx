import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { User, Briefcase, DollarSign, Calendar, Loader2 } from 'lucide-react';

const EmployeeModal = ({ isOpen, onClose, onSuccess, initialData }) => {
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    salary: '',
    start_date: new Date().toISOString().split('T')[0],
    is_active: true
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        role: initialData.role || '',
        salary: initialData.salary || '',
        start_date: initialData.start_date || new Date().toISOString().split('T')[0],
        is_active: initialData.is_active !== undefined ? initialData.is_active : true
      });
    } else {
      setFormData({
        name: '',
        role: '',
        salary: '',
        start_date: new Date().toISOString().split('T')[0],
        is_active: true
      });
    }
    setError(null);
  }, [initialData, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (initialData && initialData.id) {
        await api.put(`/finance/employees/${initialData.id}/`, formData);
      } else {
        await api.post('/finance/employees/', formData);
      }
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error saving employee:', err);
      setError(err.response?.data?.detail || 'Failed to save employee.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={initialData ? "Edit Employee" : "Add Employee"}>
      {error && (
        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3">
          <div className="text-rose-500 font-medium text-sm">{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="text"
                required
                className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                placeholder="Jane Doe"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Role / Position</label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="text"
                required
                className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                placeholder="Sales Manager"
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Monthly Salary (₦)</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="number"
                  step="0.01"
                  required
                  className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  placeholder="0.00"
                  value={formData.salary}
                  onChange={(e) => setFormData({...formData, salary: e.target.value})}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Start Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="date"
                  required
                  className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  value={formData.start_date}
                  onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                />
              </div>
            </div>
          </div>
          
          {initialData && (
            <div className="flex items-center gap-2 mt-4">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                className="rounded border-slate-700 bg-dark-900 text-brand-500 focus:ring-brand-500/50"
              />
              <label htmlFor="is_active" className="text-sm font-medium text-slate-300">Active Employee</label>
            </div>
          )}
        </div>

        <div className="pt-4 flex gap-3">
          <button type="button" onClick={onClose} className="btn-secondary flex-1">
            Cancel
          </button>
          <button type="submit" disabled={isSubmitting} className="btn-primary flex-1">
            {isSubmitting ? <Loader2 size={18} className="animate-spin mx-auto" /> : (initialData ? 'Save Changes' : 'Add Employee')}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default EmployeeModal;
