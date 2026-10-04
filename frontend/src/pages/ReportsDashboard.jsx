import React, { useState, useEffect } from 'react';
import { FileText, Calendar, Calculator, Download, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '../api';
import TaxReturnModal from '../components/TaxReturnModal';

const ReportsDashboard = () => {
  const [returns, setReturns] = useState([]);
  const [deadlines, setDeadlines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isTaxModalOpen, setIsTaxModalOpen] = useState(false);

  const fetchTaxData = async () => {
    try {
      setLoading(true);
      const [returnsRes, deadlinesRes] = await Promise.all([
        api.get('/finance/tax-returns/'),
        api.get('/finance/tax-deadlines/upcoming/')
      ]);
      setReturns(returnsRes.data);
      // The endpoint returns { deadlines: [...] }
      setDeadlines(deadlinesRes.data.deadlines || []);
    } catch (error) {
      console.error('Error fetching tax data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaxData();
  }, []);

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Tax Engine...</div>;
  }

  // Calculate totals
  const totalLiability = returns.reduce((sum, r) => sum + parseFloat(r.total_liability || 0), 0);
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Tax & Reports</h1>
          <p className="text-slate-400 mt-1">Automated tax calculations and FIRS compliance</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setIsTaxModalOpen(true)} className="btn-primary">
            <Calculator size={18} /> Generate VAT Return
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-rose-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Historical Net Tax Liability</h3>
            <div className="bg-rose-500/10 p-2 rounded-lg"><Calculator size={20} className="text-rose-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">₦{totalLiability.toLocaleString()}</div>
        </div>
        <div className="glass-card p-6 border-l-4 border-l-brand-500 md:col-span-2">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Upcoming FIRS Deadlines</h3>
            <div className="bg-brand-500/10 p-2 rounded-lg"><Calendar size={20} className="text-brand-500" /></div>
          </div>
          <div className="space-y-3">
            {deadlines.length === 0 ? (
              <p className="text-slate-500 text-sm">No upcoming deadlines detected.</p>
            ) : (
              deadlines.slice(0, 3).map((d, i) => {
                const daysLeft = Math.ceil((new Date(d.due_date) - new Date()) / (1000 * 60 * 60 * 24));
                const isUrgent = daysLeft <= 7;
                return (
                  <div key={i} className="flex justify-between items-center bg-dark-900/50 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-3">
                      {isUrgent ? (
                        <AlertCircle size={18} className="text-rose-500" />
                      ) : (
                        <CheckCircle2 size={18} className="text-emerald-500" />
                      )}
                      <div>
                        <p className="font-medium text-white">{d.tax_type} Filing - {d.period}</p>
                        <p className="text-xs text-slate-400">Due: {new Date(d.due_date).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div>
                      {daysLeft < 0 ? (
                        <span className="badge badge-danger">Overdue</span>
                      ) : (
                        <span className={`badge ${isUrgent ? 'badge-warning' : 'badge-info'}`}>
                          {daysLeft} days left
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-slate-700/50 flex justify-between items-center bg-dark-800/50">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText size={20} className="text-brand-500" />
            Tax Returns (Drafts & Filed)
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <th className="p-4 font-semibold">Tax Type</th>
                <th className="p-4 font-semibold">Period Start</th>
                <th className="p-4 font-semibold">Period End</th>
                <th className="p-4 font-semibold">Net Liability</th>
                <th className="p-4 font-semibold">Status</th>
                <th className="p-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {returns.length === 0 ? (
                <tr><td colSpan="6" className="p-8 text-center text-slate-500">No tax returns generated yet.</td></tr>
              ) : (
                returns.map((ret) => (
                  <tr key={ret.id} className="hover:bg-slate-800/20 transition-colors group">
                    <td className="p-4 font-medium text-slate-300">{ret.tax_type}</td>
                    <td className="p-4 text-slate-400 text-sm">{ret.period_start}</td>
                    <td className="p-4 text-slate-400 text-sm">{ret.period_end}</td>
                    <td className={`p-4 font-medium ${parseFloat(ret.total_liability) > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      ₦{parseFloat(ret.total_liability).toLocaleString()}
                    </td>
                    <td className="p-4">
                      <span className={`badge ${
                        ret.status === 'FILED' ? 'badge-success' : 
                        ret.status === 'DRAFT' ? 'badge-warning' : 'badge-info'
                      }`}>
                        {ret.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <button className="text-brand-500 hover:text-brand-400 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
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

      <TaxReturnModal isOpen={isTaxModalOpen} onClose={() => setIsTaxModalOpen(false)} onSuccess={fetchTaxData} />
    </div>
  );
};

export default ReportsDashboard;
