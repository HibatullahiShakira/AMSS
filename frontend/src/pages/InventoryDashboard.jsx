import React, { useState, useEffect } from 'react';
import { Package, Plus, AlertTriangle, Search, TrendingUp, Archive, Edit2 } from 'lucide-react';
import api from '../api';
import ProductModal from '../components/ProductModal';

const InventoryDashboard = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchProducts = async () => {
    try {
      const res = await api.get('/billing/products/');
      setProducts(res.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const totalValue = products.reduce((sum, p) => sum + (parseFloat(p.cost_price) * parseFloat(p.quantity_on_hand)), 0);
  const lowStockCount = products.filter(p => parseFloat(p.quantity_on_hand) <= parseFloat(p.reorder_level)).length;
  
  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (p.sku && p.sku.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center">Loading Inventory...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Inventory & Stock</h1>
          <p className="text-slate-400 mt-1">Manage your products, stock levels, and valuations.</p>
        </div>
        <button onClick={() => { setSelectedProduct(null); setIsModalOpen(true); }} className="btn-primary">
          <Plus size={18} />
          Add Product
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 border-l-4 border-l-brand-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Total Products</h3>
            <div className="bg-brand-500/10 p-2 rounded-lg"><Package size={20} className="text-brand-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            {products.length}
          </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Total Inventory Value</h3>
            <div className="bg-emerald-500/10 p-2 rounded-lg"><TrendingUp size={20} className="text-emerald-500" /></div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            ₦{totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-sm text-slate-400 mt-2">Based on cost price</p>
        </div>

        <div className={`glass-card p-6 border-l-4 ${lowStockCount > 0 ? 'border-l-rose-500' : 'border-l-slate-700'}`}>
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium">Low Stock Alerts</h3>
            <div className={`${lowStockCount > 0 ? 'bg-rose-500/10' : 'bg-slate-800'} p-2 rounded-lg`}>
              <AlertTriangle size={20} className={lowStockCount > 0 ? 'text-rose-500' : 'text-slate-500'} />
            </div>
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            {lowStockCount}
          </div>
          <p className="text-sm text-slate-400 mt-2">Items at or below reorder level</p>
        </div>
      </div>

      <div className="glass-card p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="text" 
              placeholder="Search products..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-dark-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/50 text-white"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-dark-900/50 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <th className="p-4 font-semibold">Product</th>
                <th className="p-4 font-semibold">SKU</th>
                <th className="p-4 font-semibold">Cost Price</th>
                <th className="p-4 font-semibold">Selling Price</th>
                <th className="p-4 font-semibold text-right">In Stock</th>
                <th className="p-4 font-semibold text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-slate-500">
                    <Archive size={48} className="mx-auto mb-4 opacity-20" />
                    <p>No products found.</p>
                  </td>
                </tr>
              ) : (
                filteredProducts.map((product) => {
                  const qty = parseFloat(product.quantity_on_hand);
                  const reorder = parseFloat(product.reorder_level);
                  const isLow = qty <= reorder;

                  return (
                    <tr key={product.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="p-4">
                        <div className="font-medium text-white">{product.name}</div>
                      </td>
                      <td className="p-4 text-slate-400 text-sm">{product.sku || '-'}</td>
                      <td className="p-4 text-slate-300">₦{parseFloat(product.cost_price).toLocaleString()}</td>
                      <td className="p-4 font-medium text-emerald-400">₦{parseFloat(product.unit_price).toLocaleString()}</td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isLow && <AlertTriangle size={14} className="text-rose-500" />}
                          <span className={`font-bold ${isLow ? 'text-rose-500' : 'text-white'}`}>
                            {qty}
                          </span>
                        </div>
                      </td>
                      <td className="p-4 text-center">
                        <button 
                          onClick={() => { setSelectedProduct(product); setIsModalOpen(true); }}
                          className="p-2 text-slate-400 hover:text-brand-400 hover:bg-brand-500/10 rounded-lg transition-colors"
                        >
                          <Edit2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <ProductModal 
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setSelectedProduct(null); }}
        onSuccess={fetchProducts}
        initialData={selectedProduct}
      />
    </div>
  );
};

export default InventoryDashboard;
