import React, { useState, useEffect } from 'react';
import { Activity, DollarSign, TrendingUp, TrendingDown, Clock, ShieldAlert } from 'lucide-react';
import api from '../api';

const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [pnl, setPnl] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const kpiRes = await api.get('/finance/analytics/kpis/');
        setKpis(kpiRes.data);

        const pnlRes = await api.post('/finance/analytics/pnl/', { period: 'YTD' });
        setPnl(pnlRes.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Financial Intelligence...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">Financial Intelligence Overview</h1>
        <p className="text-slate-400 mt-1">Real-time autonomous tracking of your business health.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Current Cash</h3>
            <div className="bg-emerald-500/10 p-2 rounded-lg"><DollarSign size={20} className="text-emerald-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">₦{kpis ? (kpis.liquidity?.current_cash || 0).toLocaleString() : '0.00'}</div>
          <div className="mt-4 flex items-center text-sm text-emerald-400">
            <TrendingUp size={16} className="mr-1" />
            <span>Healthy runway</span>
          </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-blue-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Net Margin</h3>
            <div className="bg-blue-500/10 p-2 rounded-lg"><Activity size={20} className="text-blue-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">{kpis ? (kpis.profitability?.net_margin_pct || 0).toFixed(1) : '0'}%</div>
          <div className="mt-4 flex items-center text-sm text-slate-400">
            <span>Profitability health</span>
          </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-amber-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Cash Runway</h3>
            <div className="bg-amber-500/10 p-2 rounded-lg"><Clock size={20} className="text-amber-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">{kpis ? kpis.liquidity?.cash_runway_months : '0'} mo</div>
          <div className="mt-4 flex items-center text-sm text-slate-400">
            <span>Estimated survival</span>
          </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-rose-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Debt to Equity</h3>
            <div className="bg-rose-500/10 p-2 rounded-lg"><ShieldAlert size={20} className="text-rose-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">{kpis ? kpis.leverage?.debt_to_equity : '0.00'}</div>
          <div className="mt-4 flex items-center text-sm text-slate-400">
            <span>Leverage ratio</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-6 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-white">Revenue Breakdown (YTD)</h2>
            <span className="badge badge-info">YTD {new Date().getFullYear()}</span>
          </div>
          <div className="h-64 flex items-center justify-center border border-dashed border-slate-700 rounded-xl bg-dark-900/50">
            {pnl?.revenue?.breakdown?.length > 0 ? (
              <div className="w-full h-full p-4 flex flex-col justify-center">
                 {pnl.revenue.breakdown.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center mb-2">
                       <span className="text-slate-300">{item.category}</span>
                       <span className="text-white font-medium">₦{item.amount.toLocaleString()}</span>
                    </div>
                 ))}
              </div>
            ) : (
              <p className="text-slate-500">No revenue data for this period.</p>
            )}
          </div>
        </div>

        <div className="glass-card p-6">
          <h2 className="text-lg font-bold text-white mb-6">Profit & Loss Summary</h2>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Total Revenue</span>
                <span className="text-white font-medium">₦{pnl ? (pnl.revenue?.total || 0).toLocaleString() : '0'}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2"><div className="bg-emerald-500 h-2 rounded-full" style={{ width: '100%' }}></div></div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Total COGS</span>
                <span className="text-white font-medium">₦{pnl ? (pnl.cogs?.total || 0).toLocaleString() : '0'}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2"><div className="bg-rose-500 h-2 rounded-full" style={{ width: pnl && pnl.revenue?.total > 0 ? `${(pnl.cogs.total/pnl.revenue.total)*100}%` : '0%' }}></div></div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Operating Expenses</span>
                <span className="text-white font-medium">₦{pnl ? (pnl.opex?.total || 0).toLocaleString() : '0'}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2"><div className="bg-amber-500 h-2 rounded-full" style={{ width: pnl && pnl.revenue?.total > 0 ? `${(pnl.opex.total/pnl.revenue.total)*100}%` : '0%' }}></div></div>
            </div>
            <div className="pt-4 border-t border-slate-700">
              <div className="flex justify-between items-center">
                <span className="text-slate-300 font-medium">Net Profit</span>
                <span className="text-2xl font-bold text-emerald-400">₦{pnl ? (pnl.net_profit || 0).toLocaleString() : '0'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
