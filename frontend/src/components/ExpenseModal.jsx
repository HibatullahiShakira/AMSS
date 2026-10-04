import React, { useState } from 'react';
import Modal from './Modal';
import api from '../api';
import { Receipt, Loader2 } from 'lucide-react';

const EXPENSE_CATEGORIES = [
  'Rent', 'Utilities', 'Salaries', 'Office Supplies', 
  'Travel', 'Marketing', 'Maintenance', 'Miscellaneous'
];

const CURRENCIES = ['NGN', 'USD', 'EUR', 'GBP', 'YEN'];

const ExpenseModal = ({ isOpen, onClose, onSuccess, initialData }) => {
  const [formData, setFormData] = useState({
    amount: '',
    expense_category: 'Miscellaneous',
    expense_type: 'OPEX',
    product: '',
    description: '',
    currency: 'NGN'
  });
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  React.useEffect(() => {
    if (isOpen) {
      setFormData({
        amount: initialData?.amount || '',
        expense_category: initialData?.expense_category || 'Miscellaneous',
        expense_type: initialData?.expense_type || 'OPEX',
        product: initialData?.product || '',
        description: initialData?.description || '',
        currency: 'NGN'
      });
      setError('');
      
      // Fetch products if opened
      const fetchProducts = async () => {
        try {
          const res = await api.get('/billing/products/');
          setProducts(res.data);
        } catch (err) {
          console.error("Failed to fetch products", err);
        }
      };
      fetchProducts();
    }
  }, [isOpen, initialData]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        amount: parseFloat(formData.amount),
        expense_category: formData.expense_category,
        expense_type: formData.expense_type,
        description: formData.description,
        currency: formData.currency
      };
      
      if (formData.expense_type === 'STOCK' && formData.product) {
        payload.product = formData.product;
      }

      await api.post('/finance/expenses/', payload);
      onSuccess();
      onClose();
      // Reset
      setFormData({ amount: '', expense_category: 'Miscellaneous', expense_type: 'OPEX', product: '', description: '', currency: 'NGN' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record expense. Please check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Record Expense">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Amount <span className="text-rose-500">*</span></label>
            <input
              type="number"
              step="0.01"
              name="amount"
              required
              value={formData.amount}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Currency</label>
            <select
              name="currency"
              value={formData.currency}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors appearance-none"
            >
              {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Expense Type</label>
            <select
              name="expense_type"
              value={formData.expense_type}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors appearance-none"
            >
              <option value="OPEX">Operating Expense</option>
              <option value="STOCK">Stock / Inventory Purchase</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Category</label>
            <select
              name="expense_category"
              value={formData.expense_category}
              onChange={handleChange}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors appearance-none"
            >
              {EXPENSE_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        {formData.expense_type === 'STOCK' && (
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Select Product</label>
            <select
              name="product"
              value={formData.product}
              onChange={handleChange}
              required={formData.expense_type === 'STOCK'}
              className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors appearance-none"
            >
              <option value="">-- Choose a Product --</option>
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.name} (In stock: {p.quantity_on_hand})</option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Description <span className="text-rose-500">*</span></label>
          <textarea
            name="description"
            required
            rows={2}
            value={formData.description}
            onChange={handleChange}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors custom-scrollbar"
            placeholder="Office supplies for Q3..."
          />
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary min-w-[140px] flex justify-center">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <><Receipt size={18} className="mr-2" /> Record Expense</>}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default ExpenseModal;
