import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import api from '../api';
import { Plus, Trash2, FileSignature, Loader2, ArrowRight, ArrowLeft } from 'lucide-react';

const CURRENCIES = ['NGN', 'USD', 'EUR', 'GBP', 'YEN'];

const InvoiceModal = ({ isOpen, onClose, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingCustomers, setFetchingCustomers] = useState(false);
  const [error, setError] = useState('');

  const [invoiceData, setInvoiceData] = useState({
    customer: '',
    issue_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
    currency: 'NGN',
    notes: '',
    terms: 'Payment is due within 30 days.'
  });

  const [lineItems, setLineItems] = useState([
    { description: '', product: '', quantity: 1, unit_price: 0, tax_rate: 7.5 }
  ]);

  useEffect(() => {
    if (isOpen) {
      fetchCustomers();
      fetchProducts();
      // Reset form
      setStep(1);
      setError('');
      setInvoiceData({
        customer: '',
        issue_date: new Date().toISOString().split('T')[0],
        due_date: new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
        currency: 'NGN',
        notes: '',
        terms: 'Payment is due within 30 days.'
      });
      setLineItems([{ description: '', product: '', quantity: 1, unit_price: 0, tax_rate: 7.5 }]);
    }
  }, [isOpen]);

  const fetchCustomers = async () => {
    setFetchingCustomers(true);
    try {
      const res = await api.get('/finance/customers/');
      setCustomers(res.data);
      if (res.data.length > 0) {
        setInvoiceData(prev => ({ ...prev, customer: res.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to fetch customers', err);
    } finally {
      setFetchingCustomers(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await api.get('/billing/products/');
      setProducts(res.data);
    } catch (err) {
      console.error('Failed to fetch products', err);
    }
  };

  const handleInvoiceChange = (e) => {
    setInvoiceData({ ...invoiceData, [e.target.name]: e.target.value });
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...lineItems];
    newItems[index][field] = value;
    
    // Auto-fill price and description if product is selected
    if (field === 'product' && value) {
      const product = products.find(p => p.id === parseInt(value));
      if (product) {
        newItems[index].description = product.name;
        newItems[index].unit_price = parseFloat(product.unit_price);
      }
    }
    
    setLineItems(newItems);
  };

  const addItem = () => {
    setLineItems([...lineItems, { description: '', product: '', quantity: 1, unit_price: 0, tax_rate: 7.5 }]);
  };

  const removeItem = (index) => {
    if (lineItems.length === 1) return;
    const newItems = lineItems.filter((_, i) => i !== index);
    setLineItems(newItems);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (step === 1) {
      setStep(2);
      return;
    }

    // Final Submit
    setLoading(true);
    setError('');

    try {
      // 1. Create Invoice Shell
      const invRes = await api.post('/billing/invoices/', invoiceData);
      const invoiceId = invRes.data.id;

      // 2. Add Line Items
      for (const item of lineItems) {
        if (item.description.trim() === '') continue;
        const itemPayload = {
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
          tax_rate: item.tax_rate
        };
        if (item.product) {
          itemPayload.product = item.product;
        }
        await api.post(`/billing/invoices/${invoiceId}/add-item/`, itemPayload);
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate invoice. Please check the fields.');
    } finally {
      setLoading(false);
    }
  };

  const calculateTotal = () => {
    return lineItems.reduce((acc, item) => {
      const sub = item.quantity * item.unit_price;
      const tax = sub * (item.tax_rate / 100);
      return acc + sub + tax;
    }, 0);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Invoice" maxWidth="max-w-2xl">
      {/* Progress */}
      <div className="flex mb-6 border-b border-slate-700/50 pb-4">
        <div className={`flex items-center text-sm font-medium ${step >= 1 ? 'text-brand-500' : 'text-slate-500'}`}>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 ${step >= 1 ? 'bg-brand-500 text-white' : 'bg-slate-800'}`}>1</div>
          Invoice Details
        </div>
        <div className={`flex-1 mx-4 h-0.5 mt-3 ${step >= 2 ? 'bg-brand-500' : 'bg-slate-800'}`}></div>
        <div className={`flex items-center text-sm font-medium ${step >= 2 ? 'text-brand-500' : 'text-slate-500'}`}>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 ${step >= 2 ? 'bg-brand-500 text-white' : 'bg-slate-800'}`}>2</div>
          Line Items
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4 animate-fade-in">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Customer <span className="text-rose-500">*</span></label>
                {fetchingCustomers ? (
                  <div className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-500">Loading...</div>
                ) : (
                  <select
                    name="customer"
                    required
                    value={invoiceData.customer}
                    onChange={handleInvoiceChange}
                    className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors appearance-none"
                  >
                    <option value="" disabled>Select a customer...</option>
                    {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                )}
                {customers.length === 0 && !fetchingCustomers && (
                  <p className="text-xs text-amber-500 mt-1">Please add a customer first.</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Currency</label>
                <select
                  name="currency"
                  value={invoiceData.currency}
                  onChange={handleInvoiceChange}
                  className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors appearance-none"
                >
                  {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Issue Date</label>
                <input
                  type="date"
                  name="issue_date"
                  required
                  value={invoiceData.issue_date}
                  onChange={handleInvoiceChange}
                  className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Due Date</label>
                <input
                  type="date"
                  name="due_date"
                  required
                  value={invoiceData.due_date}
                  onChange={handleInvoiceChange}
                  className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Terms</label>
              <textarea
                name="terms"
                rows={2}
                value={invoiceData.terms}
                onChange={handleInvoiceChange}
                className="w-full bg-dark-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors custom-scrollbar"
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4 animate-fade-in">
            <div className="max-h-64 overflow-y-auto custom-scrollbar pr-2 space-y-3">
              {lineItems.map((item, index) => (
                <div key={index} className="bg-dark-900/50 p-4 rounded-xl border border-slate-800 relative">
                  <button 
                    type="button" 
                    onClick={() => removeItem(index)}
                    disabled={lineItems.length === 1}
                    className="absolute -top-2 -right-2 bg-rose-500 text-white p-1.5 rounded-full hover:bg-rose-600 disabled:opacity-0 transition-opacity shadow-lg"
                  >
                    <Trash2 size={12} />
                  </button>
                  <div className="grid grid-cols-12 gap-3">
                    <div className="col-span-12 md:col-span-4">
                      <label className="block text-xs font-medium text-slate-500 mb-1">Product / Description</label>
                      <div className="flex gap-2">
                        <select
                          value={item.product}
                          onChange={(e) => handleItemChange(index, 'product', e.target.value)}
                          className="w-1/3 bg-dark-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500 appearance-none"
                        >
                          <option value="">Custom...</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                          ))}
                        </select>
                        <input
                          type="text"
                          required
                          value={item.description}
                          onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                          className="w-2/3 bg-dark-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
                          placeholder="Consulting Services"
                        />
                      </div>
                    </div>
                    <div className="col-span-4 md:col-span-2">
                      <label className="block text-xs font-medium text-slate-500 mb-1">Qty</label>
                      <input
                        type="number"
                        min="0.1"
                        step="0.1"
                        required
                        value={item.quantity}
                        onChange={(e) => handleItemChange(index, 'quantity', parseFloat(e.target.value))}
                        className="w-full bg-dark-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                    <div className="col-span-4 md:col-span-2">
                      <label className="block text-xs font-medium text-slate-500 mb-1">Price</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        required
                        value={item.unit_price}
                        onChange={(e) => handleItemChange(index, 'unit_price', parseFloat(e.target.value))}
                        className="w-full bg-dark-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                    <div className="col-span-4 md:col-span-2">
                      <label className="block text-xs font-medium text-slate-500 mb-1">Tax (%)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.1"
                        required
                        value={item.tax_rate}
                        onChange={(e) => handleItemChange(index, 'tax_rate', parseFloat(e.target.value))}
                        className="w-full bg-dark-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={addItem}
              className="w-full py-3 border border-dashed border-slate-700 rounded-xl text-slate-400 hover:text-white hover:border-brand-500 hover:bg-brand-500/10 transition-all flex items-center justify-center gap-2 text-sm"
            >
              <Plus size={16} /> Add Line Item
            </button>

            <div className="bg-dark-900 border border-slate-800 p-4 rounded-xl flex justify-between items-center">
              <span className="text-slate-400">Total (Inc. Tax)</span>
              <span className="text-xl font-bold text-white">{invoiceData.currency} {calculateTotal().toLocaleString()}</span>
            </div>
          </div>
        )}

        <div className="pt-4 flex justify-between">
          {step === 1 ? (
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          ) : (
            <button type="button" onClick={() => setStep(1)} className="btn-secondary flex items-center gap-2">
              <ArrowLeft size={16} /> Back
            </button>
          )}

          {step === 1 ? (
            <button type="submit" disabled={!invoiceData.customer} className="btn-primary flex items-center gap-2">
              Next Step <ArrowRight size={16} />
            </button>
          ) : (
            <button type="submit" disabled={loading} className="btn-primary min-w-[140px] flex justify-center items-center gap-2">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <><FileSignature size={18} /> Generate Invoice</>}
            </button>
          )}
        </div>
      </form>
    </Modal>
  );
};

export default InvoiceModal;
