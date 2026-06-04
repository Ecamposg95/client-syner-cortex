import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface KpiCardProps {
  label: string;
  value: string;
  delta: string;
  up: boolean;
}

export const KpiCard: React.FC<KpiCardProps> = ({ label, value, delta, up }) => {
  return (
    <div className="kpi-card group">
      <p className="kpi-card__label mb-2">{label}</p>
      <p className="kpi-card__value">{value}</p>
      <div className={`kpi-card__delta mt-1.5 flex items-center gap-1 ${up ? 'kpi-card__delta--up' : 'kpi-card__delta--down'}`}>
        {up ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
        <span>{delta}</span>
      </div>
    </div>
  );
};
