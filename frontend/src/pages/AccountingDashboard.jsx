import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Landmark, Briefcase, TrendingUp } from 'lucide-react';
import api from '../api';
import JournalEntryModal from '../components/JournalEntryModal';
import AssetModal from '../components/AssetModal';
import LiabilityModal from '../components/LiabilityModal';

const AccountingDashboard = () => {
  const [activeTab, setActiveTab] = useState('journals');
  
  const [accounts, setAccounts] = useState([]);
  const [journals, setJournals] = useState([]);
  const [assets, setAssets] = useState([]);
  const [liabilities, setLiabilities] = useState([]);
  const [loading, setLoading] = useState(true);

  const [isJournalModalOpen, setIsJournalModalOpen] = useState(false);
  const [isAssetModalOpen, setIsAssetModalOpen] = useState(false);
  const [isLiabilityModalOpen, setIsLiabilityModalOpen] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [accRes, jeRes, astRes, liabRes] = await Promise.all([
        api.get('/finance/accounts/'),
        api.get('/finance/journal-entries/'),
        api.get('/finance/assets/'),
        api.get('/finance/liabilities/')
      ]);
      setAccounts(accRes.data);
      setJournals(jeRes.data);
      setAssets(astRes.data);
      setLiabilities(liabRes.data);
    } catch (error) {
      console.error('Error fetching accounting data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Ledger...</div>;
  }

  // Calculate totals for KPI cards
  const totalAssets = assets.reduce((sum, ast) => sum + parseFloat(ast.amount || 0), 0);
  const totalLiabilities = liabilities.reduce((sum, liab) => sum + parseFloat(liab.amount || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">General Ledger</h1>
          <p className="text-slate-400 mt-1">Chart of Accounts, Journal Entries, and Balance Sheet Items</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setIsAssetModalOpen(true)} className="btn-secondary hidden md:flex">
            <Landmark size={18} /> Add Asset
          </button>
          <button onClick={() => setIsLiabilityModalOpen(true)} className="btn-secondary hidden md:flex">
            <Briefcase size={18} /> Add Liability
          </button>
          <button onClick={() => setIsJournalModalOpen(true)} className="btn-primary">
            <BookOpen size={18} /> New Journal Entry
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Total Fixed Assets</h3>
            <div className="bg-emerald-500/10 p-2 rounded-lg"><Landmark size={20} className="text-emerald-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">₦{totalAssets.toLocaleString()}</div>
        </div>
        <div className="glass-card p-6 border-l-4 border-l-rose-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Total Liabilities</h3>
            <div className="bg-rose-500/10 p-2 rounded-lg"><Briefcase size={20} className="text-rose-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">₦{totalLiabilities.toLocaleString()}</div>
        </div>
        <div className="glass-card p-6 border-l-4 border-l-brand-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Accounts Tracked</h3>
            <div className="bg-brand-500/10 p-2 rounded-lg"><TrendingUp size={20} className="text-brand-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">{accounts.length}</div>
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="border-b border-slate-700/50 flex bg-dark-800/50">
          <button 
            className={`px-6 py-4 font-medium text-sm transition-colors ${activeTab === 'journals' ? 'text-brand-400 border-b-2 border-brand-500' : 'text-slate-400 hover:text-white'}`}
            onClick={() => setActiveTab('journals')}
          >
            Journal Entries
          </button>
          <button 
            className={`px-6 py-4 font-medium text-sm transition-colors ${activeTab === 'accounts' ? 'text-brand-400 border-b-2 border-brand-500' : 'text-slate-400 hover:text-white'}`}
            onClick={() => setActiveTab('accounts')}
          >
            Chart of Accounts
          </button>
          <button 
            className={`px-6 py-4 font-medium text-sm transition-colors ${activeTab === 'assets' ? 'text-brand-400 border-b-2 border-brand-500' : 'text-slate-400 hover:text-white'}`}
            onClick={() => setActiveTab('assets')}
          >
            Assets
          </button>
          <button 
            className={`px-6 py-4 font-medium text-sm transition-colors ${activeTab === 'liabilities' ? 'text-brand-400 border-b-2 border-brand-500' : 'text-slate-400 hover:text-white'}`}
            onClick={() => setActiveTab('liabilities')}
          >
            Liabilities
          </button>
        </div>
        
        <div className="p-0">
          {activeTab === 'journals' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <th className="p-4 font-semibold">Date</th>
                    <th className="p-4 font-semibold">Ref</th>
                    <th className="p-4 font-semibold">Description</th>
                    <th className="p-4 font-semibold">Lines</th>
                    <th className="p-4 font-semibold">Amount</th>
                    <th className="p-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {journals.length === 0 ? (
                    <tr><td colSpan="6" className="p-8 text-center text-slate-500">No journal entries found.</td></tr>
                  ) : (
                    journals.map((je) => (
                      <tr key={je.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="p-4 text-slate-300">{je.date}</td>
                        <td className="p-4 font-medium">{je.reference_number || 'N/A'}</td>
                        <td className="p-4 text-white">{je.description}</td>
                        <td className="p-4 text-slate-400">{je.line_count || 0}</td>
                        <td className="p-4 font-medium text-white">₦{parseFloat(je.total_amount || 0).toLocaleString()}</td>
                        <td className="p-4">
                          <span className={`badge ${je.status === 'POSTED' ? 'badge-success' : 'badge-warning'}`}>
                            {je.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'accounts' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <th className="p-4 font-semibold">Code</th>
                    <th className="p-4 font-semibold">Name</th>
                    <th className="p-4 font-semibold">Type</th>
                    <th className="p-4 font-semibold">Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {accounts.map((acc) => (
                    <tr key={acc.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="p-4 font-medium text-brand-400">{acc.code}</td>
                      <td className="p-4 text-white">{acc.name}</td>
                      <td className="p-4 text-slate-300">{acc.account_type.replace('_', ' ')}</td>
                      <td className="p-4 font-medium text-white">₦{parseFloat(acc.balance || 0).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'assets' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <th className="p-4 font-semibold">Name</th>
                    <th className="p-4 font-semibold">Type</th>
                    <th className="p-4 font-semibold">Acquired</th>
                    <th className="p-4 font-semibold">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {assets.length === 0 ? (
                    <tr><td colSpan="4" className="p-8 text-center text-slate-500">No assets recorded.</td></tr>
                  ) : (
                    assets.map((ast) => (
                      <tr key={ast.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="p-4 font-medium text-white">{ast.name}</td>
                        <td className="p-4 text-slate-300">{ast.asset_types}</td>
                        <td className="p-4 text-slate-400">{ast.date_acquired}</td>
                        <td className="p-4 font-medium text-emerald-400">₦{parseFloat(ast.amount || 0).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'liabilities' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <th className="p-4 font-semibold">Name</th>
                    <th className="p-4 font-semibold">Type</th>
                    <th className="p-4 font-semibold">Due Date</th>
                    <th className="p-4 font-semibold">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {liabilities.length === 0 ? (
                    <tr><td colSpan="4" className="p-8 text-center text-slate-500">No liabilities recorded.</td></tr>
                  ) : (
                    liabilities.map((liab) => (
                      <tr key={liab.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="p-4 font-medium text-white">{liab.name}</td>
                        <td className="p-4 text-slate-300">{liab.liability_type}</td>
                        <td className="p-4 text-slate-400">{liab.due_date}</td>
                        <td className="p-4 font-medium text-rose-400">₦{parseFloat(liab.amount || 0).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <JournalEntryModal isOpen={isJournalModalOpen} onClose={() => setIsJournalModalOpen(false)} onSuccess={fetchData} />
      <AssetModal isOpen={isAssetModalOpen} onClose={() => setIsAssetModalOpen(false)} onSuccess={fetchData} />
      <LiabilityModal isOpen={isLiabilityModalOpen} onClose={() => setIsLiabilityModalOpen(false)} onSuccess={fetchData} />
    </div>
  );
};

export default AccountingDashboard;
