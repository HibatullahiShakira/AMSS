import React, { useState } from 'react';
import { Download, Upload, FileSpreadsheet, HardDrive, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import api from '../api';

const DataManagement = () => {
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importTarget, setImportTarget] = useState('customers');
  const [importFile, setImportFile] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [importError, setImportError] = useState('');

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await api.get('/finance/data/export/', { responseType: 'blob' });
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      // Read filename from content-disposition header if available
      const disposition = response.headers['content-disposition'];
      let filename = 'AMSS_Export.xlsx';
      if (disposition && disposition.indexOf('filename=') !== -1) {
        filename = disposition.split('filename=')[1].replace(/['"]/g, '');
      }
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export failed', error);
      alert('Failed to export data. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e) => {
    e.preventDefault();
    if (!importFile) {
      setImportError('Please select a file to upload.');
      return;
    }

    setImporting(true);
    setImportError('');
    setImportResult(null);

    const formData = new FormData();
    formData.append('file', importFile);
    // Removed target_table since backend auto-detects now

    try {
      const res = await api.post('/finance/data/import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImportResult(res.data);
      setImportFile(null); // clear file
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to import data.';
      setImportError(msg);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">Data Management</h1>
        <p className="text-slate-400 mt-1">Export your data or bulk import from CSV/Excel files</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Export Card */}
        <div className="glass-card p-6 border-t-4 border-brand-500 flex flex-col">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-brand-500/10 p-3 rounded-lg"><Download className="text-brand-500" size={24} /></div>
            <div>
              <h2 className="text-xl font-bold text-white">Export Data</h2>
              <p className="text-sm text-slate-400">Download a full backup of your business data</p>
            </div>
          </div>
          <div className="flex-1 text-slate-300 space-y-4 text-sm mt-4">
            <p>The export will generate an Excel workbook (.xlsx) containing separate sheets for:</p>
            <ul className="list-disc pl-5 space-y-1 text-slate-400 marker:text-brand-500">
              <li>Customers, Suppliers, Employees</li>
              <li>Products & Inventory</li>
              <li>Invoices & Billing</li>
              <li>Expenses</li>
              <li>General Ledger Transactions</li>
            </ul>
          </div>
          <button 
            onClick={handleExport} 
            disabled={exporting}
            className="btn-primary w-full justify-center mt-6 py-3"
          >
            {exporting ? <><Loader2 size={18} className="animate-spin mr-2"/> Preparing Export...</> : <><FileSpreadsheet size={18} className="mr-2"/> Download Excel Export</>}
          </button>
        </div>

        {/* Import Card */}
        <div className="glass-card p-6 border-t-4 border-emerald-500 flex flex-col">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-emerald-500/10 p-3 rounded-lg"><Upload className="text-emerald-500" size={24} /></div>
            <div>
              <h2 className="text-xl font-bold text-white">Bulk Import</h2>
              <p className="text-sm text-slate-400">Upload CSV or Excel files to populate tables</p>
            </div>
          </div>

          <form onSubmit={handleImport} className="flex-1 flex flex-col space-y-4 mt-4">
            {importError && (
              <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm flex gap-2 items-start">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <p>{importError}</p>
              </div>
            )}
            
            {importResult && (
              <div className="bg-emerald-500/10 border border-emerald-500/50 text-emerald-400 p-3 rounded-lg text-sm flex gap-2 items-center">
                <CheckCircle2 size={16} />
                <p>{importResult.message}</p>
              </div>
            )}

            <div>
              <p className="text-sm text-slate-400 mb-2">The system will automatically detect the table (Customers, Employees, Products, Expenses) based on the columns in your file.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Upload File (.csv, .xlsx)</label>
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-6 text-center hover:bg-dark-900 transition-colors">
                <input 
                  type="file" 
                  accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="hidden" 
                  id="file-upload" 
                />
                <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                  <HardDrive size={32} className="text-slate-500 mb-2" />
                  <span className="text-brand-400 font-medium hover:text-brand-300">Choose a file</span>
                  <span className="text-xs text-slate-500 mt-1">{importFile ? importFile.name : 'No file selected'}</span>
                </label>
              </div>
            </div>

            <div className="mt-auto pt-4">
              <button 
                type="submit" 
                disabled={importing || !importFile}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 disabled:shadow-none flex items-center justify-center"
              >
                {importing ? <><Loader2 size={18} className="animate-spin mr-2"/> Importing Data...</> : 'Start Import'}
              </button>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
};

export default DataManagement;
