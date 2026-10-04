import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { Package, Hash, DollarSign, Loader2 } from 'lucide-react';

const ProductModal = ({ isOpen, onClose, onSuccess, initialData }) => {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    description: '',
    unit_price: '',
    cost_price: '',
    quantity_on_hand: '',
    reorder_level: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        sku: initialData.sku || '',
        description: initialData.description || '',
        unit_price: initialData.unit_price || '',
        cost_price: initialData.cost_price || '',
        quantity_on_hand: initialData.quantity_on_hand || '',
        reorder_level: initialData.reorder_level || ''
      });
    } else {
      setFormData({
        name: '',
        sku: '',
        description: '',
        unit_price: '',
        cost_price: '',
        quantity_on_hand: '',
        reorder_level: ''
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
        await api.put(`/billing/products/${initialData.id}/`, formData);
      } else {
        await api.post('/billing/products/', formData);
      }
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error saving product:', err);
      setError(err.response?.data?.detail || err.response?.data?.name?.[0] || 'Failed to save product. Please check the form.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={initialData ? "Edit Product" : "Add New Product"}>
      {error && (
        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3">
          <div className="text-rose-500 font-medium text-sm">{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Product Name</label>
            <div className="relative">
              <Package className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="text"
                required
                className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                placeholder="e.g., iPhone 15 Pro"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">SKU (Optional)</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="text"
                className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                placeholder="e.g., IP15P-256-BLK"
                value={formData.sku}
                onChange={(e) => setFormData({...formData, sku: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Selling Price (₦)</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="number"
                  step="0.01"
                  required
                  className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  placeholder="0.00"
                  value={formData.unit_price}
                  onChange={(e) => setFormData({...formData, unit_price: e.target.value})}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Cost Price (₦)</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="number"
                  step="0.01"
                  required
                  className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  placeholder="0.00"
                  value={formData.cost_price}
                  onChange={(e) => setFormData({...formData, cost_price: e.target.value})}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Initial Quantity</label>
              <input
                type="number"
                required
                className="w-full bg-dark-900 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                placeholder="0"
                value={formData.quantity_on_hand}
                onChange={(e) => setFormData({...formData, quantity_on_hand: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Reorder Level</label>
              <input
                type="number"
                required
                className="w-full bg-dark-900 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                placeholder="e.g., 5"
                value={formData.reorder_level}
                onChange={(e) => setFormData({...formData, reorder_level: e.target.value})}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Description (Optional)</label>
            <textarea
              className="w-full bg-dark-900 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50 min-h-[100px]"
              placeholder="Product details..."
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>
        </div>

        <div className="pt-4 flex gap-3">
          <button type="button" onClick={onClose} className="btn-secondary flex-1">
            Cancel
          </button>
          <button type="submit" disabled={isSubmitting} className="btn-primary flex-1">
            {isSubmitting ? <Loader2 size={18} className="animate-spin mx-auto" /> : (initialData ? 'Save Changes' : 'Add Product')}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default ProductModal;
