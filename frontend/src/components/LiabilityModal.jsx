import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { Briefcase, Loader2 } from 'lucide-react';

const LiabilityModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    amount: '',
    date_incurred: new Date().toISOString().split('T')[0],
    liability_type: 'SHORT_TERM_LOAN',
    due_date: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        amount: '',
        date_incurred: new Date().toISOString().split('T')[0],
        liability_type: 'SHORT_TERM_LOAN',
        due_date: ''
      });
      setError('');
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/finance/liabilities/', {
        ...formData,
        amount: parseFloat(formData.amount) || 0,
        due_date: formData.due_date || null
      });
      onSuccess();
      onClose();
    } catch (err) {
      const errData = err.response?.data;
      if (errData && typeof errData === 'object') {
        const messages = Object.entries(errData)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('; ');
        setError(messages);
      } else {
        setError('Failed to record liability.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Record Liability">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Liability Name / Description <span className="text-rose-500">*</span></label>
          <input
            type="text"
            name="name"
            required
            value={formData.name}
            onChange={handleChange}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            placeholder="e.g. Bank of Industry Loan"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Amount (₦) <span className="text-rose-500">*</span></label>
            <input
              type="number"
              step="0.01"
              min="0"
              name="amount"
              required
              value={formData.amount}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Liability Type <span className="text-rose-500">*</span></label>
            <select
              name="liability_type"
              required
              value={formData.liability_type}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            >
              <option value="SHORT_TERM_LOAN">Short Term Loan</option>
              <option value="LONG_TERM_LOAN">Long Term Loan</option>
              <option value="ACCOUNTS_PAYABLE">Accounts Payable</option>
              <option value="ACCRUED_EXPENSES">Accrued Expenses</option>
              <option value="UNEARNED_REVENUE">Unearned Revenue</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Date Incurred <span className="text-rose-500">*</span></label>
            <input
              type="date"
              name="date_incurred"
              required
              value={formData.date_incurred}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Due Date</label>
            <input
              type="date"
              name="due_date"
              value={formData.due_date}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary min-w-[140px] flex justify-center">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><Briefcase size={18} className="mr-2" /> Save Liability</>}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default LiabilityModal;
