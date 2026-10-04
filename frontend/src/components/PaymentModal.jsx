import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { CreditCard, Loader2, DollarSign } from 'lucide-react';

const PaymentModal = ({ isOpen, onClose, onSuccess, initialInvoice = null, invoices = [] }) => {
  const [formData, setFormData] = useState({
    invoice: '',
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_method: 'BANK_TRANSFER',
    reference: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Whenever the modal opens or initialInvoice changes, pre-fill data
  useEffect(() => {
    if (isOpen) {
      if (initialInvoice) {
        setFormData({
          invoice: initialInvoice.id,
          amount: initialInvoice.balance_due || initialInvoice.total_amount || '',
          payment_date: new Date().toISOString().split('T')[0],
          payment_method: 'BANK_TRANSFER',
          reference: '',
          notes: ''
        });
      } else {
        setFormData({
          invoice: '',
          amount: '',
          payment_date: new Date().toISOString().split('T')[0],
          payment_method: 'BANK_TRANSFER',
          reference: '',
          notes: ''
        });
      }
      setError('');
    }
  }, [isOpen, initialInvoice]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Auto-fill amount if invoice changes
    if (name === 'invoice' && value) {
      const selected = invoices.find(inv => inv.id.toString() === value.toString());
      if (selected) {
        setFormData(prev => ({ ...prev, amount: selected.balance_due || selected.total_amount }));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/billing/payments/', {
        ...formData,
        amount: parseFloat(formData.amount)
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
        setError('Failed to record payment. Please check the fields.');
      }
    } finally {
      setLoading(false);
    }
  };

  const paymentMethods = [
    { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
    { value: 'CASH', label: 'Cash' },
    { value: 'POS', label: 'POS Terminal' },
    { value: 'CARD', label: 'Credit/Debit Card' },
    { value: 'MOBILE_MONEY', label: 'Mobile Money' },
    { value: 'USSD', label: 'USSD Code' },
    { value: 'CHEQUE', label: 'Cheque' }
  ];

  const pendingInvoices = invoices.filter(inv => inv.status !== 'PAID' && inv.status !== 'VOID');

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Record Payment">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Invoice <span className="text-rose-500">*</span></label>
          <select
            name="invoice"
            required
            value={formData.invoice}
            onChange={handleChange}
            disabled={!!initialInvoice}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors disabled:opacity-50"
          >
            <option value="">Select an Invoice</option>
            {initialInvoice && !pendingInvoices.find(i => i.id === initialInvoice.id) && (
               <option value={initialInvoice.id}>{initialInvoice.invoice_number} (Selected)</option>
            )}
            {pendingInvoices.map(inv => (
              <option key={inv.id} value={inv.id}>
                {inv.invoice_number} - {inv.customer_name} (Balance: ₦{parseFloat(inv.balance_due || inv.total_amount).toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Amount Paid <span className="text-rose-500">*</span></label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-slate-400 font-medium">₦</span>
              </div>
              <input
                type="number"
                step="0.01"
                min="0.01"
                name="amount"
                required
                value={formData.amount}
                onChange={handleChange}
                className="w-full bg-dark-900 border border-slate-700 rounded-lg pl-8 pr-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors"
                placeholder="0.00"
              />
            </div>
            {formData.invoice && (
              <p className="text-xs text-slate-500 mt-1">Partial payments are allowed.</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Payment Date <span className="text-rose-500">*</span></label>
            <input
              type="date"
              name="payment_date"
              required
              value={formData.payment_date}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Payment Method <span className="text-rose-500">*</span></label>
            <select
              name="payment_method"
              required
              value={formData.payment_method}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors"
            >
              {paymentMethods.map(method => (
                <option key={method.value} value={method.value}>{method.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Reference</label>
            <input
              type="text"
              name="reference"
              value={formData.reference}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="e.g. TXN-987654321"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Notes</label>
          <textarea
            name="notes"
            rows={2}
            value={formData.notes}
            onChange={handleChange}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 transition-colors custom-scrollbar"
            placeholder="Optional payment notes..."
          />
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary min-w-[140px] flex justify-center">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><CreditCard size={18} className="mr-2" /> Record Payment</>}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default PaymentModal;
