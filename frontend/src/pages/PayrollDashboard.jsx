import React, { useState, useEffect } from 'react';
import { Users, Plus, DollarSign, Calendar, Settings, PlayCircle } from 'lucide-react';
import api from '../api';
import EmployeeModal from '../components/EmployeeModal';

const PayrollDashboard = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [runningPayroll, setRunningPayroll] = useState(false);

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/finance/employees/');
      setEmployees(res.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleRunPayroll = async () => {
    if (!window.confirm("Run payroll for all active employees? This will generate expense records.")) return;
    
    setRunningPayroll(true);
    try {
      const res = await api.post('/finance/employees/run-payroll/');
      alert(res.data.message);
    } catch (error) {
      console.error('Error running payroll:', error);
      alert('Failed to run payroll.');
    } finally {
      setRunningPayroll(false);
    }
  };

  const activeEmployees = employees.filter(e => e.is_active);
  const totalMonthlyPayroll = activeEmployees.reduce((sum, e) => sum + parseFloat(e.salary), 0);

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Payroll...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Payroll & Team</h1>
          <p className="text-slate-400 mt-1">Manage your employees and run automated payroll.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleRunPayroll} disabled={runningPayroll} className="btn-secondary text-brand-500 border-brand-500/50 hover:bg-brand-500/10">
            <PlayCircle size={18} className="mr-2" />
            {runningPayroll ? 'Processing...' : 'Run Payroll'}
          </button>
          <button onClick={() => { setSelectedEmployee(null); setIsModalOpen(true); }} className="btn-primary">
            <Plus size={18} />
            Add Employee
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-brand-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Active Employees</h3>
            <div className="bg-brand-500/10 p-2 rounded-lg"><Users size={20} className="text-brand-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">
            {activeEmployees.length}
          </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Est. Monthly Payroll</h3>
            <div className="bg-emerald-500/10 p-2 rounded-lg"><DollarSign size={20} className="text-emerald-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white">
            ₦{totalMonthlyPayroll.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-6">Employee Directory</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.map(employee => (
            <div key={employee.id} className="bg-dark-900 border border-slate-800 p-5 rounded-xl flex flex-col justify-between hover:border-slate-700 transition-colors">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-white text-lg">{employee.name}</h4>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${employee.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                    {employee.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <p className="text-slate-400 text-sm mb-4">{employee.role}</p>
                <div className="space-y-2">
                  <div className="flex items-center text-sm text-slate-300">
                    <DollarSign size={14} className="text-slate-500 mr-2" />
                    ₦{parseFloat(employee.salary).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / month
                  </div>
                  <div className="flex items-center text-sm text-slate-300">
                    <Calendar size={14} className="text-slate-500 mr-2" />
                    Started {employee.start_date}
                  </div>
                </div>
              </div>
              <button 
                onClick={() => { setSelectedEmployee(employee); setIsModalOpen(true); }}
                className="mt-6 w-full py-2 bg-dark-800 hover:bg-slate-800 text-slate-300 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
              >
                <Settings size={14} /> Manage
              </button>
            </div>
          ))}
          {employees.length === 0 && (
             <div className="col-span-full py-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
               <Users size={48} className="mx-auto mb-4 opacity-20" />
               <p>No employees found. Add your first team member.</p>
             </div>
          )}
        </div>
      </div>

      <EmployeeModal 
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setSelectedEmployee(null); }}
        onSuccess={fetchEmployees}
        initialData={selectedEmployee}
      />
    </div>
  );
};

export default PayrollDashboard;
