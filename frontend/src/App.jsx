import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, Wallet, TrendingUp, BookOpen, Settings, FileText, Activity, Database, Package, Users, ShoppingCart } from 'lucide-react';
import './index.css';

import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import BillingDashboard from './pages/BillingDashboard';
import ExpenseDashboard from './pages/ExpenseDashboard';
import AccountingDashboard from './pages/AccountingDashboard';
import ReportsDashboard from './pages/ReportsDashboard';
import DataManagement from './pages/DataManagement';
import InventoryDashboard from './pages/InventoryDashboard';
import PayrollDashboard from './pages/PayrollDashboard';
import POSDashboard from './pages/POSDashboard';
import AgentChat from './components/AgentChat';

const Sidebar = () => {
  const location = useLocation();
  const path = location.pathname;
  const { logout } = useAuth();

  const NavItem = ({ to, icon: Icon, label }) => {
    const isActive = path === to || (to !== '/' && path.startsWith(to));
    return (
      <Link 
        to={to} 
        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
          ${isActive 
            ? 'bg-brand-500/10 text-brand-500' 
            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
      >
        <Icon size={20} className={isActive ? 'text-brand-500' : 'text-slate-500 group-hover:text-slate-300'} />
        <span className="font-medium text-sm">{label}</span>
      </Link>
    );
  };

  return (
    <aside className="w-64 bg-dark-900 border-r border-slate-800 h-screen sticky top-0 flex flex-col pt-6">
      <div className="px-6 mb-8 flex items-center gap-3">
        <div className="bg-brand-500 p-2 rounded-lg">
          <TrendingUp size={24} className="text-white" />
        </div>
        <h2 className="text-xl font-bold tracking-tight text-white">AMSS</h2>
      </div>
      
      <nav className="flex-1 px-4 space-y-1">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 px-2 mt-4">Dashboards</div>
        <NavItem to="/" icon={LayoutDashboard} label="Overview" />
        <NavItem to="/billing" icon={Wallet} label="Billing & AR" />
        <NavItem to="/expenses" icon={Activity} label="Expenses & Alerts" />
        
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 px-2 mt-8">Accounting</div>
        <NavItem to="/accounting" icon={BookOpen} label="General Ledger" />
        <NavItem to="/reports" icon={FileText} label="Tax & Reports" />
        <NavItem to="/inventory" icon={Package} label="Inventory" />
        <NavItem to="/payroll" icon={Users} label="Payroll & Team" />
        <NavItem to="/pos" icon={ShoppingCart} label="Point of Sale" />
      </nav>

      <div className="p-4 mt-auto space-y-2">
        <NavItem to="/data-management" icon={Database} label="Data & Imports" />
        <NavItem to="/settings" icon={Settings} label="Settings" />
        <button onClick={logout} className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 w-full text-left">
          <Activity size={20} className="text-slate-500" />
          <span className="font-medium text-sm">Sign Out</span>
        </button>
      </div>
    </aside>
  );
};

const Layout = ({ children }) => (
  <div className="flex min-h-screen bg-dark-900 text-slate-200 font-sans">
    <Sidebar />
    <main className="flex-1 overflow-y-auto relative">
      <div className="p-8 max-w-7xl mx-auto animate-fade-in pb-24">
        {children}
      </div>
      <AgentChat />
    </main>
  </div>
);

const PrivateRoute = ({ children, requireBusiness = true }) => {
  const { user, business, loading } = useAuth();
  
  if (loading) return <div className="h-screen flex items-center justify-center bg-dark-900 text-brand-500">Loading...</div>;
  
  if (!user) return <Navigate to="/login" />;
  
  // If user is logged in but hasn't set up a business, force onboarding
  if (requireBusiness && !business) return <Navigate to="/onboarding" />;
  
  // If user is already onboarded and tries to visit onboarding, send to dashboard
  if (!requireBusiness && business) return <Navigate to="/" />;
  
  return requireBusiness ? <Layout>{children}</Layout> : children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/onboarding" element={
            <PrivateRoute requireBusiness={false}>
              <Onboarding />
            </PrivateRoute>
          } />
          
          <Route path="/" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
          <Route path="/billing" element={
            <PrivateRoute>
              <BillingDashboard />
            </PrivateRoute>
          } />
          <Route path="/expenses" element={
            <PrivateRoute>
              <ExpenseDashboard />
            </PrivateRoute>
          } />
          <Route path="/accounting" element={
            <PrivateRoute>
              <AccountingDashboard />
            </PrivateRoute>
          } />
          <Route path="/reports" element={
            <PrivateRoute>
              <ReportsDashboard />
            </PrivateRoute>
          } />
          <Route path="/data-management" element={
            <PrivateRoute>
              <DataManagement />
            </PrivateRoute>
          } />
          <Route path="/inventory" element={
            <PrivateRoute>
              <InventoryDashboard />
            </PrivateRoute>
          } />
          <Route path="/payroll" element={
            <PrivateRoute>
              <PayrollDashboard />
            </PrivateRoute>
          } />
          <Route path="/pos" element={
            <PrivateRoute>
              <POSDashboard />
            </PrivateRoute>
          } />
          
          <Route path="*" element={
            <PrivateRoute>
              <div className="flex flex-col items-center justify-center h-[60vh]">
                <div className="bg-dark-800 p-4 rounded-full mb-4">
                  <BookOpen size={32} className="text-brand-500" />
                </div>
                <h1 className="text-2xl font-bold mb-2">Coming Soon</h1>
                <p className="text-slate-400">This module is currently under development.</p>
              </div>
            </PrivateRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
