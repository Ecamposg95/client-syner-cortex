import React from 'react';
import { Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Sample data – replace with real KPI API data later
const sampleData = {
  labels: ['Revenue', 'Profit', 'Customer Satisfaction', 'Growth'],
  datasets: [
    {
      label: 'Q1 2026',
      data: [120000, 30000, 85, 12],
      backgroundColor: 'rgba(139, 92, 246, 0.6)',
      borderColor: 'rgba(139, 92, 246, 1)',
      borderWidth: 1,
    },
  ],
};

const options = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: true,
      text: 'Key Performance Indicators',
    },
  },
};

export const Boardroom: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center p-8 glass-panel">
      <h1 className="text-4xl font-bold gradient-text mb-8">Boardroom Dashboard</h1>
      <div className="w-full max-w-4xl glass-panel-hover p-4 rounded-lg shadow-lg">
        <Chart type="bar" data={sampleData} options={options} />
      </div>
      <p className="mt-6 text-slate-300 text-center">
        This boardroom view will surface real‑time KPI charts and AI‑generated insights.
      </p>
    </div>
  );
};
