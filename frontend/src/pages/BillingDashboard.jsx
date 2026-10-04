import React, { useState, useEffect } from 'react';
import { CreditCard, FileText, Download, UserPlus, FileSignature, ArrowRight, Activity, TrendingUp, AlertCircle } from 'lucide-react';
import api from '../api';
import CustomerModal from '../components/CustomerModal';
import InvoiceModal from '../components/InvoiceModal';
import PaymentModal from '../components/PaymentModal';

const BillingDashboard = () => {
  const [invoices, setInvoices] = useState([]);
  const [arAging, setArAging] = useState(null);
  const [loading, setLoading] = useState(true);

  const [isCustomerModalOpen, setIsCustomerModalOpen] = useState(false);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  const fetchBillingData = async () => {
    try {
      const invoiceRes = await api.get('/billing/invoices/');
      setInvoices(invoiceRes.data);

      const arRes = await api.get('/billing/ar-aging/report/');
      setArAging(arRes.data);
    } catch (error) {
      console.error('Error fetching billing data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBillingData();
  }, []);

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Billing Engine...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Billing & Accounts Receivable</h1>
          <p className="text-slate-400 mt-1">Autonomous invoice tracking and debt collection</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setIsCustomerModalOpen(true)} className="btn-secondary">
            <UserPlus size={18} />
            New Customer
          </button>
          <button onClick={() => setIsInvoiceModalOpen(true)} className="btn-primary">
            <FileSignature size={18} />
            Create Invoice
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-brand-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Total Outstanding</h3>
            <div className="bg-brand-500/10 p-2 rounded-lg"><Activity size={20} className="text-brand-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            ₦{arAging ? (arAging.total_outstanding || 0).toLocaleString() : '0.00'}
          </div>
        </div>
        <div className="glass-card p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">0-30 Days</h3>
            <div className="bg-amber-500/10 p-2 rounded-lg"><AlertCircle size={20} className="text-amber-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">
            ₦{arAging?.buckets?.[0] ? arAging.buckets[0].total.toLocaleString() : '0.00'}
          </div>
        </div>
        <div className="glass-card p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">31-60 Days</h3>
            <div className="bg-orange-500/10 p-2 rounded-lg"><AlertCircle size={20} className="text-orange-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">
            ₦{arAging?.buckets?.[1] ? arAging.buckets[1].total.toLocaleString() : '0.00'}
          </div>
        </div>
        <div className="glass-card p-6 border-l-4 border-l-rose-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">90+ Days Past Due</h3>
            <div className="bg-rose-500/10 p-2 rounded-lg"><TrendingUp size={20} className="text-rose-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">
            ₦{arAging?.buckets?.[3] ? arAging.buckets[3].total.toLocaleString() : '0.00'}
          </div>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-slate-700/50 flex justify-between items-center bg-dark-800/50">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText size={20} className="text-brand-500" />
            Recent Invoices
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <th className="p-4 font-semibold">Invoice ID</th>
                <th className="p-4 font-semibold">Client</th>
                <th className="p-4 font-semibold">Amount</th>
                <th className="p-4 font-semibold">Date</th>
                <th className="p-4 font-semibold">Status</th>
                <th className="p-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {invoices.length === 0 ? (
                <tr><td colSpan="6" className="p-8 text-center text-slate-500">No invoices generated yet.</td></tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/20 transition-colors group">
                    <td className="p-4 font-medium text-slate-300">{inv.invoice_number}</td>
                    <td className="p-4">{inv.customer_name}</td>
                    <td className="p-4 font-medium text-white">{inv.currency} {parseFloat(inv.total_amount).toLocaleString()}</td>
                    <td className="p-4 text-slate-400 text-sm">{inv.issue_date}</td>
                    <td className="p-4">
                      <span className={`badge ${
                        inv.status === 'PAID' ? 'badge-success' : 
                        inv.status === 'OVERDUE' ? 'badge-danger' : 
                        inv.status === 'SENT' ? 'badge-info' : 'badge-warning'
                      }`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="p-4 text-right flex justify-end gap-2">
                      {inv.status !== 'PAID' && inv.status !== 'VOID' && (
                        <button 
                          onClick={() => { setSelectedInvoice(inv); setIsPaymentModalOpen(true); }}
                          className="text-emerald-500 hover:text-emerald-400 p-2 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Record Payment"
                        >
                          <CreditCard size={18} />
                        </button>
                      )}
                      <button className="text-brand-500 hover:text-brand-400 p-2 opacity-0 group-hover:opacity-100 transition-opacity" title="Download PDF">
                        <Download size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <CustomerModal 
        isOpen={isCustomerModalOpen} 
        onClose={() => setIsCustomerModalOpen(false)} 
        onSuccess={fetchBillingData} 
      />
      <InvoiceModal 
        isOpen={isInvoiceModalOpen} 
        onClose={() => setIsInvoiceModalOpen(false)} 
        onSuccess={fetchBillingData} 
      />
      <PaymentModal
        isOpen={isPaymentModalOpen}
        onClose={() => { setIsPaymentModalOpen(false); setSelectedInvoice(null); }}
        onSuccess={fetchBillingData}
        initialInvoice={selectedInvoice}
        invoices={invoices}
      />
    </div>
  );
};

export default BillingDashboard;
