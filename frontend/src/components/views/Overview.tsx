import React from 'react';
import { Card } from '../ui/Card';
import { KpiCard } from '../ui/KpiCard';
import { ProgressBar } from '../ui/ProgressBar';
import { Badge } from '../ui/Badge';
import { kpis, efficiencyData, tasks, project } from '../../data/mockData';
import { CheckCircle2, Circle } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

const lineChartData = {
  labels: efficiencyData.map(d => d.month),
  datasets: [
    {
      fill: true,
      label: 'Eficiencia %',
      data: efficiencyData.map(d => d.value),
      borderColor: 'rgba(44, 154, 166, 1)',
      backgroundColor: 'rgba(44, 154, 166, 0.1)',
      tension: 0.4,
    },
  ],
};

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    y: { beginAtZero: false, grid: { color: 'rgba(0,0,0,0.05)' } },
    x: { grid: { display: false } },
  },
};

export const Overview: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-bold text-2xl">Dashboard Ejecutivo</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <KpiCard key={idx} {...kpi} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-lg">Eficiencia Operativa</h3>
            <Badge variant="active" label="+12% este mes" />
          </div>
          <div className="h-64">
            <Line data={lineChartData} options={lineChartOptions} />
          </div>
        </Card>

        <div className="space-y-6">
          <Card>
            <h3 className="font-bold text-lg mb-4">Progreso de Fase Actual</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-[var(--muted)]">Fase {project.phase} / {project.totalPhases}</span>
                <span className="font-bold text-[var(--accent-strong)]">{project.progress}%</span>
              </div>
              <ProgressBar percent={project.progress} />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg">Tareas Activas</h3>
              <span className="font-mono text-[10px] text-[var(--muted-2)] uppercase">Sprint actual</span>
            </div>
            <div className="space-y-3">
              {tasks.map((task) => (
                <div key={task.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-[var(--surface-2)] transition-colors cursor-pointer group">
                  <div className="mt-0.5" style={{ color: task.done ? 'var(--pos)' : 'var(--border-strong)' }}>
                    {task.done ? <CheckCircle2 size={16} /> : <Circle size={16} className="group-hover:text-[var(--accent)]" />}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm ${task.done ? 'line-through text-[var(--muted-2)]' : 'text-[var(--ink)]'}`}>
                      {task.title}
                    </p>
                    <p className="text-[10px] text-[var(--muted)] mt-1">{task.assignee}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
