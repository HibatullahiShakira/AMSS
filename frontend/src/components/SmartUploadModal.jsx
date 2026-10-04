import React, { useState } from 'react';
import { Upload, Loader2, FileText, AlertCircle, Sparkles } from 'lucide-react';
import Modal from './Modal';
import api from '../api';

const SmartUploadModal = ({ isOpen, onClose, onParsed }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer?.files[0] || e.target.files[0];
    if (droppedFile) {
      if (droppedFile.type === 'application/pdf' || droppedFile.type.includes('image/')) {
        setFile(droppedFile);
        setError('');
      } else {
        setError('Please upload a PDF or Image file.');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/finance/document/parse/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const data = res.data.extracted_data;
      // Pre-fill object for the Expense Modal
      const prefillData = {
        description: data.vendor ? `${data.vendor} - ${data.description || 'Invoice'}` : data.description || '',
        amount: data.amount || '',
        date: data.date || new Date().toISOString().split('T')[0],
        expense_type: data.expense_type || 'OPEX',
      };
      
      onParsed(prefillData);
      setFile(null);
      onClose();
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to parse document. Ensure the AI engine is running.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Smart Upload (AI Powered)">
      <div className="space-y-4 text-slate-300">
        <p className="text-sm">
          Upload an invoice or receipt. Our AI engine will automatically extract the vendor, date, and amount to pre-fill your expense record.
        </p>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-lg text-sm flex gap-2 items-start">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div 
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors
            ${file ? 'border-brand-500 bg-brand-500/5' : 'border-slate-700 hover:border-slate-600 bg-dark-900'}
          `}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
        >
          <input 
            type="file" 
            accept=".pdf,image/*"
            onChange={handleFileDrop}
            className="hidden" 
            id="smart-file-upload" 
          />
          <label htmlFor="smart-file-upload" className="cursor-pointer flex flex-col items-center">
            {file ? (
              <>
                <FileText size={48} className="text-brand-500 mb-3" />
                <span className="text-brand-400 font-bold">{file.name}</span>
                <span className="text-xs text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </>
            ) : (
              <>
                <Upload size={48} className="text-slate-500 mb-3" />
                <span className="text-brand-400 font-medium hover:text-brand-300">Click to upload or drag & drop</span>
                <span className="text-xs text-slate-500 mt-1">Supports PDF, PNG, JPG</span>
              </>
            )}
          </label>
        </div>

        <div className="pt-4 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button 
            type="button" 
            onClick={handleUpload}
            disabled={!file || loading}
            className="btn-primary min-w-[160px] flex justify-center"
          >
            {loading ? (
              <><Loader2 size={18} className="animate-spin mr-2" /> Extracting AI Data...</>
            ) : (
              <><Sparkles size={18} className="mr-2" /> Read Document</>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default SmartUploadModal;
