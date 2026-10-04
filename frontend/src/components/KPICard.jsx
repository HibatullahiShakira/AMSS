import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import clsx from 'clsx';

const KPICard = ({ title, value, prefix = '', suffix = '', trend = null, trendValue = '', icon: Icon, colorClass = 'text-brand-500', bgClass = 'bg-brand-500/10' }) => {
  return (
    <div className="glass-card p-6 flex flex-col gap-4 relative overflow-hidden group hover:border-slate-600/50 transition-colors">
      {/* Background glow effect */}
      <div className={clsx("absolute -right-8 -top-8 w-32 h-32 rounded-full blur-3xl opacity-20 group-hover:opacity-30 transition-opacity", bgClass.replace('/10', ''))} />
      
      <div className="flex justify-between items-start z-10">
        <div>
          <h3 className="text-sm font-medium text-slate-400 mb-1">{title}</h3>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white tracking-tight">
              {prefix}{value}{suffix}
            </span>
          </div>
        </div>
        
        {Icon && (
          <div className={clsx("p-3 rounded-xl", bgClass)}>
            <Icon size={24} className={colorClass} />
          </div>
        )}
      </div>

      {trend && (
        <div className="flex items-center gap-2 mt-2 z-10">
          <div className={clsx(
            "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-md",
            trend === 'up' ? "bg-emerald-500/10 text-emerald-400" :
            trend === 'down' ? "bg-rose-500/10 text-rose-400" :
            "bg-slate-500/10 text-slate-400"
          )}>
            {trend === 'up' && <TrendingUp size={14} />}
            {trend === 'down' && <TrendingDown size={14} />}
            {trend === 'neutral' && <Minus size={14} />}
            <span>{trendValue}</span>
          </div>
          <span className="text-xs text-slate-500">vs last month</span>
        </div>
      )}
    </div>
  );
};

export default KPICard;
