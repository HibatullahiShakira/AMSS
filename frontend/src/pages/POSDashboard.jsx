import React, { useState, useEffect } from 'react';
import { ShoppingCart, Plus, Minus, Search, CreditCard, Banknote, Landmark, Trash2, CheckCircle2 } from 'lucide-react';
import api from '../api';

const POSDashboard = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  
  // Checkout Modal State
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('CASH');
  const [amountPaid, setAmountPaid] = useState('');
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, []);

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

  const addToCart = (product) => {
    const existing = cart.find(item => item.product_id === product.id);
    if (existing) {
      setCart(cart.map(item => 
        item.product_id === product.id 
          ? { ...item, quantity: item.quantity + 1 } 
          : item
      ));
    } else {
      setCart([...cart, { 
        product_id: product.id, 
        name: product.name, 
        unit_price: parseFloat(product.unit_price), 
        quantity: 1, 
        tax_rate: 7.5 
      }]);
    }
  };

  const updateQuantity = (productId, delta) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newQ = item.quantity + delta;
        return newQ > 0 ? { ...item, quantity: newQ } : item;
      }
      return item;
    }));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const subtotal = cart.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0);
  const tax = cart.reduce((sum, item) => sum + ((item.unit_price * item.quantity) * (item.tax_rate / 100)), 0);
  const total = subtotal + tax;

  const handleCheckout = async () => {
    setProcessing(true);
    try {
      const payload = {
        items: cart.map(item => ({
          product_id: item.product_id,
          description: item.name,
          quantity: item.quantity,
          unit_price: item.unit_price,
          tax_rate: item.tax_rate
        })),
        amount_paid: amountPaid || total,
        payment_method: paymentMethod
      };
      
      await api.post('/billing/invoices/pos-checkout/', payload);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setIsCheckoutOpen(false);
        setCart([]);
        setAmountPaid('');
      }, 2000);
    } catch (error) {
      console.error('Checkout failed', error);
      alert('Checkout failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const filteredProducts = products.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

  if (loading) {
    return <div className="animate-pulse h-64 bg-dark-800 rounded-2xl flex items-center justify-center text-slate-400">Loading POS...</div>;
  }

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-6 -mt-4">
      
      {/* Main Product Area */}
      <div className="flex-1 flex flex-col h-full bg-dark-900 rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-dark-950 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Point of Sale</h2>
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input 
              type="text" 
              placeholder="Search products..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-dark-800 border border-slate-700 rounded-xl pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>
        
        <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredProducts.map(product => (
              <div 
                key={product.id}
                onClick={() => addToCart(product)}
                className="bg-dark-800 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-brand-500 hover:bg-dark-700 transition-all group flex flex-col h-32"
              >
                <div className="flex-1">
                  <h3 className="text-white font-medium line-clamp-2">{product.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">{product.sku}</p>
                </div>
                <div className="flex justify-between items-end mt-2">
                  <span className="text-brand-400 font-bold">₦{parseFloat(product.unit_price).toLocaleString()}</span>
                  <span className="text-xs text-slate-400">Stock: {product.quantity_on_hand}</span>
                </div>
              </div>
            ))}
            {filteredProducts.length === 0 && (
              <div className="col-span-full py-12 text-center text-slate-500">No products found.</div>
            )}
          </div>
        </div>
      </div>

      {/* Cart Sidebar */}
      <div className="w-96 flex flex-col h-full bg-dark-900 rounded-2xl border border-slate-800 overflow-hidden shrink-0 shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-dark-950 flex items-center gap-3">
          <ShoppingCart className="text-brand-500" size={20} />
          <h2 className="text-lg font-bold text-white">Current Order</h2>
          <span className="ml-auto bg-brand-500/10 text-brand-500 text-xs font-bold px-2.5 py-1 rounded-full">{cart.length} items</span>
        </div>
        
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
          {cart.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-50">
              <ShoppingCart size={48} className="mb-4" />
              <p>Your cart is empty</p>
            </div>
          ) : (
            cart.map((item, index) => (
              <div key={index} className="bg-dark-800 rounded-xl p-3 border border-slate-700">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-sm font-medium text-white line-clamp-1">{item.name}</h4>
                  <button onClick={() => removeFromCart(item.product_id)} className="text-slate-500 hover:text-rose-500 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-brand-400 font-bold text-sm">₦{(item.unit_price * item.quantity).toLocaleString()}</span>
                  <div className="flex items-center gap-3 bg-dark-950 rounded-lg p-1 border border-slate-700">
                    <button onClick={() => updateQuantity(item.product_id, -1)} className="text-slate-400 hover:text-white p-1"><Minus size={14} /></button>
                    <span className="text-white text-sm font-medium w-4 text-center">{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.product_id, 1)} className="text-slate-400 hover:text-white p-1"><Plus size={14} /></button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-5 border-t border-slate-800 bg-dark-950">
          <div className="space-y-2 mb-4">
            <div className="flex justify-between text-slate-400 text-sm">
              <span>Subtotal</span>
              <span>₦{subtotal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-slate-400 text-sm">
              <span>Tax (7.5%)</span>
              <span>₦{tax.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-white font-bold text-lg pt-2 border-t border-slate-800 border-dashed">
              <span>Total</span>
              <span>₦{total.toLocaleString()}</span>
            </div>
          </div>
          <button 
            onClick={() => setIsCheckoutOpen(true)}
            disabled={cart.length === 0}
            className="w-full py-3.5 bg-brand-500 hover:bg-brand-400 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(99,102,241,0.4)] disabled:opacity-50 disabled:shadow-none"
          >
            Charge ₦{total.toLocaleString()}
          </button>
        </div>
      </div>

      {/* Checkout Modal Overlay */}
      {isCheckoutOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-dark-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-slide-up">
            
            {success ? (
              <div className="p-8 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-emerald-500/20 text-emerald-500 rounded-full flex items-center justify-center mb-4">
                  <CheckCircle2 size={32} />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Payment Successful!</h2>
                <p className="text-slate-400">The invoice has been generated and inventory updated.</p>
              </div>
            ) : (
              <>
                <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-dark-950">
                  <h2 className="text-lg font-bold text-white">Complete Checkout</h2>
                  <button onClick={() => setIsCheckoutOpen(false)} className="text-slate-400 hover:text-white">✕</button>
                </div>
                
                <div className="p-6 space-y-6">
                  <div className="text-center mb-2">
                    <p className="text-slate-400 text-sm mb-1">Total Amount Due</p>
                    <h3 className="text-4xl font-bold text-brand-400">₦{total.toLocaleString()}</h3>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">Payment Method</label>
                    <div className="grid grid-cols-3 gap-3">
                      <button 
                        onClick={() => setPaymentMethod('CASH')}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all ${paymentMethod === 'CASH' ? 'bg-brand-500/20 border-brand-500 text-brand-400' : 'bg-dark-800 border-slate-700 text-slate-400 hover:border-slate-500'}`}
                      >
                        <Banknote size={20} className="mb-1" />
                        <span className="text-xs font-medium">Cash</span>
                      </button>
                      <button 
                        onClick={() => setPaymentMethod('POS')}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all ${paymentMethod === 'POS' ? 'bg-brand-500/20 border-brand-500 text-brand-400' : 'bg-dark-800 border-slate-700 text-slate-400 hover:border-slate-500'}`}
                      >
                        <CreditCard size={20} className="mb-1" />
                        <span className="text-xs font-medium">POS Card</span>
                      </button>
                      <button 
                        onClick={() => setPaymentMethod('BANK_TRANSFER')}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all ${paymentMethod === 'BANK_TRANSFER' ? 'bg-brand-500/20 border-brand-500 text-brand-400' : 'bg-dark-800 border-slate-700 text-slate-400 hover:border-slate-500'}`}
                      >
                        <Landmark size={20} className="mb-1" />
                        <span className="text-xs font-medium">Transfer</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-1">Amount Tendered</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">₦</span>
                      <input 
                        type="number"
                        placeholder={total.toString()}
                        value={amountPaid}
                        onChange={(e) => setAmountPaid(e.target.value)}
                        className="w-full bg-dark-950 border border-slate-700 rounded-xl pl-8 pr-4 py-3 text-lg font-medium text-white focus:outline-none focus:border-brand-500"
                      />
                    </div>
                  </div>

                  <button 
                    onClick={handleCheckout}
                    disabled={processing}
                    className="w-full py-4 bg-brand-500 hover:bg-brand-400 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(99,102,241,0.4)] disabled:opacity-50 flex justify-center items-center gap-2 text-lg"
                  >
                    {processing ? <span className="animate-pulse">Processing...</span> : `Confirm ₦${(amountPaid || total).toLocaleString()}`}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default POSDashboard;
