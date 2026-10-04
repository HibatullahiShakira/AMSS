import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Building2, ChevronRight } from 'lucide-react';

const Onboarding = () => {
  const { completeOnboarding, user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    business_name: '',
    business_email: user?.email || '',
    business_type: 'LLC',
    industry: 'Technology',
    business_address: '',
    preferred_currency: 'NGN',
    annual_revenue: '',
    bank_account_details: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await completeOnboarding(formData);
      navigate('/data-management'); // Go to Data Import page automatically after onboarding
    } catch (err) {
      setError('Failed to setup business. Ensure business name is unique.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900 px-4 py-12">
      <div className="max-w-xl w-full space-y-8 glass-card p-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-brand-500 rounded-xl flex items-center justify-center">
             <Building2 className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-white">Setup Your Business</h2>
          <p className="mt-2 text-sm text-slate-400">
            Step {step} of 2
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={step === 1 ? (e) => { e.preventDefault(); setStep(2); } : handleSubmit}>
          {error && <div className="text-rose-500 text-sm text-center bg-rose-500/10 py-2 rounded-lg border border-rose-500/20">{error}</div>}

          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Business Name</label>
                <input type="text" name="business_name" required className="input-field" onChange={handleChange} value={formData.business_name} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Business Email</label>
                <input type="email" name="business_email" required className="input-field" onChange={handleChange} value={formData.business_email} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Entity Type</label>
                  <select name="business_type" className="input-field" onChange={handleChange} value={formData.business_type}>
                    <option value="LLC">Limited Liability Company</option>
                    <option value="SOLE">Sole Proprietorship</option>
                    <option value="CORP">Corporation</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Industry</label>
                  <select name="industry" className="input-field" onChange={handleChange} value={formData.industry}>
                    <option value="Technology">Technology</option>
                    <option value="Retail">Retail</option>
                    <option value="Manufacturing">Manufacturing</option>
                    <option value="Services">Services</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="w-full btn-primary py-3 mt-6">
                Next <ChevronRight size={20} />
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Primary Address</label>
                <input type="text" name="business_address" required className="input-field" onChange={handleChange} value={formData.business_address} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Currency</label>
                  <select name="preferred_currency" className="input-field" onChange={handleChange} value={formData.preferred_currency}>
                    <option value="NGN">Naira (NGN)</option>
                    <option value="USD">US Dollar (USD)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Est. Annual Revenue</label>
                  <input type="number" name="annual_revenue" className="input-field" onChange={handleChange} value={formData.annual_revenue} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Bank Account Details (Optional)</label>
                <input type="text" name="bank_account_details" className="input-field" onChange={handleChange} value={formData.bank_account_details} placeholder="e.g. Zenith Bank - 100XXXXXXX" />
              </div>
              <div className="flex gap-4 mt-6">
                <button type="button" onClick={() => setStep(1)} className="w-1/3 btn-secondary py-3">Back</button>
                <button type="submit" className="w-2/3 btn-primary py-3">Launch AMSS Brain</button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default Onboarding;
