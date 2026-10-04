import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { FileText, Loader2, Calculator } from 'lucide-react';

const TaxReturnModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setFormData({
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear()
      });
      setError('');
      setResult(null);
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: parseInt(value) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await api.post('/finance/tax-returns/generate-vat/', formData);
      setResult(res.data);
      onSuccess();
    } catch (err) {
      const errData = err.response?.data;
      if (errData && typeof errData === 'object') {
        const messages = Object.entries(errData)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('; ');
        setError(messages);
      } else {
        setError('Failed to generate VAT return.');
      }
    } finally {
      setLoading(false);
    }
  };

  const months = [
    { value: 1, label: 'January' }, { value: 2, label: 'February' },
    { value: 3, label: 'March' }, { value: 4, label: 'April' },
    { value: 5, label: 'May' }, { value: 6, label: 'June' },
    { value: 7, label: 'July' }, { value: 8, label: 'August' },
    { value: 9, label: 'September' }, { value: 10, label: 'October' },
    { value: 11, label: 'November' }, { value: 12, label: 'December' }
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Generate VAT Return">
      {!result ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-slate-400 mb-4">
            Our engine will automatically calculate VAT collected from your invoices and VAT paid on your expenses for the selected period.
          </p>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Month <span className="text-rose-500">*</span></label>
              <select
                name="month"
                required
                value={formData.month}
                onChange={handleChange}
                className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
              >
                {months.map(m => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Year <span className="text-rose-500">*</span></label>
              <input
                type="number"
                name="year"
                required
                min="2020"
                max={new Date().getFullYear()}
                value={formData.year}
                onChange={handleChange}
                className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary min-w-[160px] flex justify-center">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <><Calculator size={18} className="mr-2" /> Generate Return</>}
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          <div className="bg-emerald-500/10 border border-emerald-500/50 p-4 rounded-lg text-center">
            <h3 className="text-emerald-400 font-bold mb-1">VAT Return Generated Successfully</h3>
            <p className="text-sm text-slate-400">Your draft return for {months.find(m => m.value === formData.month)?.label} {formData.year} has been saved.</p>
          </div>

          <div className="space-y-3 bg-dark-900 p-4 rounded-lg border border-slate-800">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <span className="text-slate-400">Total VAT Collected (Sales)</span>
              <span className="text-white font-medium">₦{parseFloat(result.report_data_json?.total_vat_collected || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <span className="text-slate-400">Total VAT Paid (Purchases)</span>
              <span className="text-white font-medium">₦{parseFloat(result.report_data_json?.total_vat_paid || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center pt-2">
              <span className="text-slate-300 font-bold">Net VAT Liability</span>
              <span className={`font-bold text-lg ${parseFloat(result.total_liability) > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                ₦{parseFloat(result.total_liability || 0).toLocaleString()}
              </span>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button type="button" onClick={onClose} className="btn-primary">Done</button>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default TaxReturnModal;
