import React, { useState, useEffect } from 'react';
import { Activity, Receipt, AlertTriangle, TrendingDown, PieChart, AlertCircle, Sparkles } from 'lucide-react';
import api from '../api';
import ExpenseModal from '../components/ExpenseModal';
import SmartUploadModal from '../components/SmartUploadModal';

const ExpenseDashboard = () => {
  const [expenses, setExpenses] = useState([]);
  const [anomalies, setAnomalies] = useState(null);
  const [breakdown, setBreakdown] = useState(null);
  const [reminders, setReminders] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [isSmartUploadOpen, setIsSmartUploadOpen] = useState(false);
  const [expensePrefillData, setExpensePrefillData] = useState(null);

  const fetchExpenseData = async () => {
    try {
      const expenseRes = await api.get('/finance/expenses/');
      setExpenses(expenseRes.data);

      const anomalyRes = await api.get('/finance/expense-intelligence/anomalies/');
      setAnomalies(anomalyRes.data);

      const breakdownRes = await api.get('/finance/expense-intelligence/breakdown/');
      setBreakdown(breakdownRes.data);

      const remindersRes = await api.get('/finance/reminders/summary/');
      setReminders(remindersRes.data);
    } catch (error) {
      console.error('Error fetching expense intelligence data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenseData();
  }, []);

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Expense Intelligence...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Expenses & Intelligence Alerts</h1>
          <p className="text-slate-400 mt-1">AI-driven anomaly detection and spending controls</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setIsSmartUploadOpen(true)} className="btn-secondary border-brand-500/30 text-brand-400 hover:bg-brand-500/10">
            <Sparkles size={18} />
            Smart AI Upload
          </button>
          <button onClick={() => {
            setExpensePrefillData(null);
            setIsExpenseModalOpen(true);
          }} className="btn-primary">
            <Receipt size={18} />
            Record Expense
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-rose-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Anomalies Detected</h3>
            <div className="bg-rose-500/10 p-2 rounded-lg"><AlertTriangle size={20} className="text-rose-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            {anomalies ? anomalies.anomaly_count : 0}
          </div>
          <p className="text-sm text-slate-400 mt-2">Unusual spending patterns</p>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-amber-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Critical Reminders</h3>
            <div className="bg-amber-500/10 p-2 rounded-lg"><AlertCircle size={20} className="text-amber-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            {reminders && reminders.by_urgency ? reminders.by_urgency.critical : 0}
          </div>
          <p className="text-sm text-slate-400 mt-2">Requires immediate attention</p>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-blue-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Total Upcoming Obligations</h3>
            <div className="bg-blue-500/10 p-2 rounded-lg"><TrendingDown size={20} className="text-blue-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            ₦{reminders ? (reminders.total_upcoming_obligations || 0).toLocaleString() : '0.00'}
          </div>
          <p className="text-sm text-slate-400 mt-2">Pending and Sent reminders</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card p-6 lg:col-span-2 overflow-hidden">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Receipt size={20} className="text-brand-500" />
              Recent Expenses
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <th className="p-4 font-semibold">Description</th>
                  <th className="p-4 font-semibold">Category</th>
                  <th className="p-4 font-semibold">Amount</th>
                  <th className="p-4 font-semibold">Date</th>
                  <th className="p-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {expenses.length === 0 ? (
                  <tr><td colSpan="5" className="p-8 text-center text-slate-500">No expenses recorded yet.</td></tr>
                ) : (
                  expenses.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="p-4 font-medium text-slate-300">{exp.description}</td>
                      <td className="p-4 text-slate-400">{exp.category_name || exp.expense_category}</td>
                      <td className="p-4 font-medium text-white">{exp.currency} {parseFloat(exp.amount).toLocaleString()}</td>
                      <td className="p-4 text-slate-400 text-sm">{new Date(exp.date).toLocaleDateString()}</td>
                      <td className="p-4">
                        <span className={`badge ${
                          exp.status === 'CLEARED' ? 'badge-success' : 'badge-warning'
                        }`}>
                          {exp.status || 'PENDING'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <PieChart size={20} className="text-brand-500" />
              Spending Breakdown
            </h2>
          </div>
          <div className="space-y-4">
            {breakdown && breakdown.breakdown && breakdown.breakdown.length > 0 ? (
              breakdown.breakdown.map((item) => (
                <div key={item.category}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-400">{item.category}</span>
                    <span className="text-white font-medium">₦{parseFloat(item.total).toLocaleString()}</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className="bg-brand-500 h-2 rounded-full" style={{ width: `${item.percentage}%` }}></div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-500 text-sm text-center">No breakdown data available.</p>
            )}
          </div>
        </div>
      </div>

      <ExpenseModal 
        isOpen={isExpenseModalOpen} 
        onClose={() => {
          setIsExpenseModalOpen(false);
          setExpensePrefillData(null);
        }} 
        onSuccess={fetchExpenseData} 
        initialData={expensePrefillData}
      />

      <SmartUploadModal
        isOpen={isSmartUploadOpen}
        onClose={() => setIsSmartUploadOpen(false)}
        onParsed={(data) => {
          setExpensePrefillData(data);
          setIsExpenseModalOpen(true);
        }}
      />
    </div>
  );
};

export default ExpenseDashboard;
