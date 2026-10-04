import React, { useState } from 'react';
import Modal from './Modal';
import api from '../api';
import { UserPlus, Loader2 } from 'lucide-react';

const CustomerModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    contact_info: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/finance/customers/', formData);
      onSuccess();
      onClose();
      setFormData({ name: '', contact_info: '' });
    } catch (err) {
      const errData = err.response?.data;
      if (errData && typeof errData === 'object') {
        const messages = Object.entries(errData).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join('; ');
        setError(messages);
      } else {
        setError('Failed to create customer. Please check the fields.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="New Customer">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}
        
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Company / Name <span className="text-rose-500">*</span></label>
          <input
            type="text"
            name="name"
            required
            value={formData.name}
            onChange={handleChange}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
            placeholder="Acme Corp"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Contact Info <span className="text-rose-500">*</span></label>
          <textarea
            name="contact_info"
            required
            rows={3}
            value={formData.contact_info}
            onChange={handleChange}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors custom-scrollbar"
            placeholder={"Email: billing@acme.com\nPhone: +234 801 234 5678\nAddress: 15 Broad Street, Lagos"}
          />
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary min-w-[120px] flex justify-center">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><UserPlus size={18} className="mr-2" /> Save Customer</>}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default CustomerModal;
