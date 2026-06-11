import React from 'react';
import { Card } from '../ui/Card';
import { ProgressBar } from '../ui/ProgressBar';
import { BookOpen, CheckCircle, Clock } from 'lucide-react';

const mockCourses = [
  { id: 1, title: 'Introducción a SOPs Básicos', progress: 100, status: 'COMPLETED', modules: 5 },
  { id: 2, title: 'Manejo de Residuos Peligrosos (EHS)', progress: 50, status: 'IN_PROGRESS', modules: 4 },
  { id: 3, title: 'Cultura BJX Pit Crew', progress: 0, status: 'PENDING', modules: 3 },
];

export const AcademyView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="font-bold text-2xl">Academia Syner</h2>
        <p className="text-sm text-[var(--muted)]">Capacitación y certificación del equipo</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {mockCourses.map((course) => (
          <Card key={course.id} className="flex flex-col p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div className="bg-[var(--surface-2)] p-3 rounded-lg">
                <BookOpen size={24} className="text-[var(--ink)]" />
              </div>
              {course.status === 'COMPLETED' ? (
                <CheckCircle size={20} className="text-green-500" />
              ) : course.status === 'IN_PROGRESS' ? (
                <Clock size={20} className="text-yellow-500" />
              ) : null}
            </div>

            <div>
              <h3 className="font-semibold text-[var(--ink)]">{course.title}</h3>
              <p className="text-xs text-[var(--muted)] mt-1">{course.modules} módulos de aprendizaje</p>
            </div>

            <div className="mt-auto pt-4 space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-[var(--muted)]">Progreso</span>
                <span className="font-bold">{course.progress}%</span>
              </div>
              <ProgressBar percent={course.progress} />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};