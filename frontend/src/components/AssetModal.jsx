import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { Landmark, Loader2 } from 'lucide-react';

const AssetModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    amount: '',
    date_acquired: new Date().getFullYear().toString(),
    asset_types: 'BUILDING',
    useful_life: 10,
    residual_value: 0,
    valuation_method: 'COST'
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        amount: '',
        date_acquired: new Date().getFullYear().toString(),
        asset_types: 'BUILDING',
        useful_life: 10,
        residual_value: 0,
        valuation_method: 'COST'
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
      await api.post('/finance/assets/', {
        ...formData,
        amount: parseFloat(formData.amount) || 0,
        useful_life: parseInt(formData.useful_life) || 1,
        residual_value: parseFloat(formData.residual_value) || 0,
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
        setError('Failed to record asset.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Record Fixed Asset">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Asset Name <span className="text-rose-500">*</span></label>
          <input
            type="text"
            name="name"
            required
            value={formData.name}
            onChange={handleChange}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            placeholder="e.g. Delivery Van 1"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Asset Value (₦) <span className="text-rose-500">*</span></label>
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
            <label className="block text-sm font-medium text-slate-400 mb-1">Year Acquired <span className="text-rose-500">*</span></label>
            <input
              type="number"
              name="date_acquired"
              required
              value={formData.date_acquired}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
              placeholder="2024"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Asset Type</label>
            <select
              name="asset_types"
              value={formData.asset_types}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            >
              <option value="BUILDING">Building</option>
              <option value="MACHINERY">Machinery</option>
              <option value="VEHICLE">Vehicle</option>
              <option value="EQUIPMENT">Equipment</option>
              <option value="FURNITURE">Furniture</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Valuation Method</label>
            <select
              name="valuation_method"
              value={formData.valuation_method}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            >
              <option value="COST">Cost Model</option>
              <option value="REVALUATION">Revaluation Model</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Useful Life (Years)</label>
            <input
              type="number"
              min="1"
              name="useful_life"
              value={formData.useful_life}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Residual Value (₦)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              name="residual_value"
              value={formData.residual_value}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary min-w-[140px] flex justify-center">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><Landmark size={18} className="mr-2" /> Save Asset</>}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default AssetModal;
