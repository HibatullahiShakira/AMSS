import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { BookOpen, Plus, Trash2, Loader2 } from 'lucide-react';

const JournalEntryModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    lines: [
      { account: '', debit_amount: '', credit_amount: '', description: '' },
      { account: '', debit_amount: '', credit_amount: '', description: '' }
    ]
  });
  
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setFormData({
        date: new Date().toISOString().split('T')[0],
        description: '',
        lines: [
          { account: '', debit_amount: '', credit_amount: '', description: '' },
          { account: '', debit_amount: '', credit_amount: '', description: '' }
        ]
      });
      setError('');
      fetchAccounts();
    }
  }, [isOpen]);

  const fetchAccounts = async () => {
    try {
      const res = await api.get('/finance/accounts/');
      setAccounts(res.data);
    } catch (err) {
      console.error('Failed to load accounts', err);
    }
  };

  const handleLineChange = (index, field, value) => {
    const newLines = [...formData.lines];
    newLines[index][field] = value;

    // Mutually exclusive debit/credit
    if (field === 'debit_amount' && value > 0) {
      newLines[index]['credit_amount'] = '';
    } else if (field === 'credit_amount' && value > 0) {
      newLines[index]['debit_amount'] = '';
    }

    setFormData(prev => ({ ...prev, lines: newLines }));
  };

  const addLine = () => {
    setFormData(prev => ({
      ...prev,
      lines: [...prev.lines, { account: '', debit_amount: '', credit_amount: '', description: '' }]
    }));
  };

  const removeLine = (index) => {
    if (formData.lines.length <= 2) return;
    const newLines = formData.lines.filter((_, i) => i !== index);
    setFormData(prev => ({ ...prev, lines: newLines }));
  };

  const totalDebits = formData.lines.reduce((sum, line) => sum + (parseFloat(line.debit_amount) || 0), 0);
  const totalCredits = formData.lines.reduce((sum, line) => sum + (parseFloat(line.credit_amount) || 0), 0);
  const isBalanced = totalDebits > 0 && totalDebits === totalCredits;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isBalanced) {
      setError(`Entry must balance. Debits: ₦${totalDebits.toLocaleString()}, Credits: ₦${totalCredits.toLocaleString()}`);
      return;
    }

    setLoading(true);
    setError('');

    // Format lines for API
    const formattedLines = formData.lines.map(line => ({
      ...line,
      debit_amount: parseFloat(line.debit_amount) || 0.00,
      credit_amount: parseFloat(line.credit_amount) || 0.00
    })).filter(line => line.debit_amount > 0 || line.credit_amount > 0);

    try {
      await api.post('/finance/journal-entries/', {
        ...formData,
        lines: formattedLines
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
        setError('Failed to create journal entry.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="New Journal Entry">
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Date <span className="text-rose-500">*</span></label>
            <input
              type="date"
              required
              value={formData.date}
              onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Description <span className="text-rose-500">*</span></label>
            <input
              type="text"
              required
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="e.g. Monthly Rent Allocation"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-slate-400">Entry Lines</label>
            <button type="button" onClick={addLine} className="text-brand-500 text-sm flex items-center hover:text-brand-400 transition-colors">
              <Plus size={16} className="mr-1" /> Add Line
            </button>
          </div>
          
          <div className="space-y-3">
            {formData.lines.map((line, idx) => (
              <div key={idx} className="flex gap-3 items-start bg-dark-900/50 p-3 rounded-lg border border-slate-800">
                <div className="flex-1">
                  <select
                    required
                    value={line.account}
                    onChange={(e) => handleLineChange(idx, 'account', e.target.value)}
                    className="w-full bg-dark-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-brand-500"
                  >
                    <option value="">Select Account...</option>
                    {accounts.map(acc => (
                      <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                    ))}
                  </select>
                </div>
                <div className="w-28 relative">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={line.debit_amount}
                    onChange={(e) => handleLineChange(idx, 'debit_amount', e.target.value)}
                    placeholder="Debit"
                    className="w-full bg-dark-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div className="w-28 relative">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={line.credit_amount}
                    onChange={(e) => handleLineChange(idx, 'credit_amount', e.target.value)}
                    placeholder="Credit"
                    className="w-full bg-dark-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-brand-500"
                  />
                </div>
                <button 
                  type="button" 
                  onClick={() => removeLine(idx)}
                  disabled={formData.lines.length <= 2}
                  className="p-2 text-slate-500 hover:text-rose-500 disabled:opacity-30 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-6 mt-4 p-4 bg-dark-900/50 rounded-lg border border-slate-800">
            <div className="text-right">
              <p className="text-xs text-slate-500 mb-1">Total Debits</p>
              <p className={`text-lg font-medium ${isBalanced ? 'text-white' : 'text-rose-500'}`}>₦{totalDebits.toLocaleString()}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500 mb-1">Total Credits</p>
              <p className={`text-lg font-medium ${isBalanced ? 'text-white' : 'text-rose-500'}`}>₦{totalCredits.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading || !isBalanced} className="btn-primary min-w-[160px] flex justify-center">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><BookOpen size={18} className="mr-2" /> Post Entry</>}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default JournalEntryModal;
