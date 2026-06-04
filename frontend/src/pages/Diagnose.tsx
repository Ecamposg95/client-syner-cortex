import React, { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useDiagnosisStore } from '../store/diagnosisStore';
import {
  Activity,
  Star,
  Loader2,
  ChevronRight,
  ChevronLeft,
  CheckCircle,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  RefreshCw
} from 'lucide-react';

export const Diagnose: React.FC = () => {
  const { activeWorkspace } = useWorkspaceStore();
  const { currentDiagnosis, submitDiagnosis, fetchLatestDiagnosis, isLoading, isSubmitting } = useDiagnosisStore();

  const dimensionsList = [
    { name: 'Ventas', label: 'Ventas y Comercial', desc: 'Captación de clientes, pipeline, pricing y prospección.' },
    { name: 'Operaciones', label: 'Operaciones y Procesos', desc: 'Entrega de servicio, manuales, eficiencia y cuellos de botella.' },
    { name: 'Administracion', label: 'Administración y Finanzas', desc: 'Flujo de caja, control de gastos, rentabilidad y contabilidad.' },
    { name: 'Recursos Humanos', label: 'Recursos Humanos y Personal', desc: 'Cultura, perfiles de puesto, compensación y retención de talento.' },
    { name: 'Tecnologia', label: 'Tecnología y Madurez Digital', desc: 'Herramientas de software, automatización, seguridad y uso de IA.' }
  ];

  const [currentStep, setCurrentStep] = useState(0);
  const [isFormMode, setIsFormMode] = useState(false);
  const [answers, setAnswers] = useState<any[]>(
    dimensionsList.map((d) => ({
      name: d.name,
      rating: 3,
      findings: '',
      challenges: ''
    }))
  );

  useEffect(() => {
    if (activeWorkspace) {
      fetchLatestDiagnosis(activeWorkspace.id);
    }
  }, [activeWorkspace, fetchLatestDiagnosis]);

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <Activity size={48} className="text-violet-500 mb-4 animate-pulse" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-sm text-slate-400 max-w-sm">
          Please select or create a project workspace from the sidebar menu to view company diagnosis.
        </p>
      </div>
    );
  }

  const handleRatingChange = (rating: number) => {
    setAnswers((prev) =>
      prev.map((ans, idx) => (idx === currentStep ? { ...ans, rating } : ans))
    );
  };

  const handleTextChange = (field: 'findings' | 'challenges', value: string) => {
    setAnswers((prev) =>
      prev.map((ans, idx) => (idx === currentStep ? { ...ans, [field]: value } : ans))
    );
  };

  const handleNext = () => {
    if (currentStep < dimensionsList.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    const success = await submitDiagnosis(activeWorkspace.id, answers);
    if (success) {
      setIsFormMode(false);
    }
  };

  // Group SWOT factors for presentation
  const getOverallSWOT = () => {
    if (!currentDiagnosis) return null;
    const strengths: string[] = [];
    const weaknesses: string[] = [];
    const opportunities: string[] = [];
    const threats: string[] = [];

    currentDiagnosis.dimensions.forEach((dim) => {
      if (dim.swot_analysis) {
        strengths.push(...(dim.swot_analysis.strengths || []).slice(0, 1));
        weaknesses.push(...(dim.swot_analysis.weaknesses || []).slice(0, 1));
        opportunities.push(...(dim.swot_analysis.opportunities || []).slice(0, 1));
        threats.push(...(dim.swot_analysis.threats || []).slice(0, 1));
      }
    });

    return { strengths, weaknesses, opportunities, threats };
  };

  const swot = getOverallSWOT();

  return (
    <div className="space-y-8">
      
      {/* PAGE HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h2 className="font-display font-extrabold text-3xl tracking-tight text-white">
            Cortex 360 Corporate Diagnosis
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Evaluate core operations, compile SWOT frameworks, and trigger execution strategies.
          </p>
        </div>
        {currentDiagnosis && !isFormMode && (
          <button
            onClick={() => setIsFormMode(true)}
            className="px-4 py-2 text-xs font-semibold text-white rounded-xl bg-white/5 border border-white/10 hover:border-violet-500/20 flex items-center space-x-1.5 transition-all duration-300"
          >
            <RefreshCw size={12} />
            <span>Re-run Diagnosis</span>
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 size={32} className="text-violet-500 animate-spin" />
        </div>
      ) : isFormMode || !currentDiagnosis ? (
        
        /* QUESTIONNAIRE WIZARD VIEW */
        <div className="w-full max-w-3xl mx-auto glass-panel rounded-3xl p-6 md:p-8 space-y-6">
          
          {/* PROGRESS STEPS BAR */}
          <div className="flex items-center justify-between pb-4 border-b border-white/5">
            <span className="text-[10px] font-bold text-violet-400 tracking-widest uppercase">
              Dimension {currentStep + 1} of {dimensionsList.length}
            </span>
            <span className="text-sm font-semibold text-white">
              {dimensionsList[currentStep].label}
            </span>
          </div>

          {/* STEP EXPLANATION */}
          <div className="space-y-1">
            <h3 className="font-display font-bold text-lg text-white">
              {dimensionsList[currentStep].label} Assessment
            </h3>
            <p className="text-xs text-slate-400">
              {dimensionsList[currentStep].desc}
            </p>
          </div>

          <div className="space-y-5">
            {/* RATING SLIDER */}
            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-400">
                Performance Rating (1 = Critical, 5 = Excellent)
              </label>
              <div className="flex space-x-2.5">
                {[1, 2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => handleRatingChange(num)}
                    className={`w-10 h-10 rounded-xl font-bold flex items-center justify-center border text-sm transition-all duration-200 ${
                      answers[currentStep].rating === num
                        ? 'bg-violet-600 border-violet-500 text-white shadow-glow'
                        : 'bg-white/5 border-white/5 hover:border-white/10 text-slate-400'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </div>

            {/* FINDINGS INPUT */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Current Strengths & Status (Findings)
              </label>
              <textarea
                required
                rows={3}
                placeholder="What is currently working? (e.g. Sales reps convert 15% of inbound leads, CRM is partially mapped...)"
                value={answers[currentStep].findings}
                onChange={(e) => handleTextChange('findings', e.target.value)}
                className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm resize-none transition-all"
              />
            </div>

            {/* CHALLENGES INPUT */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Bottlenecks & Gaps (Challenges)
              </label>
              <textarea
                required
                rows={3}
                placeholder="What limits scaling? (e.g. High customer churn, no cash flow forecasting, manual invoice collection...)"
                value={answers[currentStep].challenges}
                onChange={(e) => handleTextChange('challenges', e.target.value)}
                className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm resize-none transition-all"
              />
            </div>
          </div>

          {/* NAV CONTROLS */}
          <div className="flex justify-between pt-6 border-t border-white/5">
            <button
              onClick={handlePrev}
              disabled={currentStep === 0}
              className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 disabled:opacity-40 transition-colors flex items-center space-x-1"
            >
              <ChevronLeft size={14} />
              <span>Back</span>
            </button>

            {currentStep < dimensionsList.length - 1 ? (
              <button
                onClick={handleNext}
                className="px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-xs font-semibold text-white flex items-center space-x-1"
              >
                <span>Continue</span>
                <ChevronRight size={14} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-xs font-bold text-white shadow-glow flex items-center space-x-1.5 disabled:opacity-55"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={12} className="animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle size={14} />
                    <span>Complete Analysis</span>
                  </>
                )}
              </button>
            )}
          </div>

        </div>
      ) : (
        
        /* DIAGNOSIS RESULTS VIEW */
        <div className="space-y-10">
          
          {/* DIMENSION DETAILS */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-6">
              <h3 className="font-display font-bold text-xl text-white">Dimension Diagnostics</h3>
              <div className="space-y-4">
                {currentDiagnosis.dimensions.map((dim) => (
                  <div key={dim.id} className="glass-panel rounded-2xl p-5 space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="font-semibold text-white">{dim.name}</h4>
                      <div className="flex items-center space-x-0.5">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            size={12}
                            className={i < dim.rating ? 'text-amber-400 fill-amber-400' : 'text-slate-700'}
                          />
                        ))}
                      </div>
                    </div>
                    
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {dim.findings}
                    </p>

                    <div className="p-3 bg-violet-500/5 rounded-xl border border-violet-500/10 text-xs text-slate-300">
                      <div className="flex items-center space-x-1.5 text-violet-400 mb-1 font-semibold uppercase tracking-wider text-[10px]">
                        <Sparkles size={12} />
                        <span>Executive Recommendation</span>
                      </div>
                      {dim.recommendations}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* SWOT / FODA GRID */}
            <div className="space-y-6">
              <h3 className="font-display font-bold text-xl text-white">SWOT Analysis Framework</h3>
              
              {swot && (
                <div className="grid grid-cols-2 gap-4">
                  
                  {/* STRENGTHS */}
                  <div className="p-5 rounded-2xl bg-emerald-500/5 border border-emerald-500/15 space-y-2">
                    <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest block">
                      Strengths (Fortalezas)
                    </span>
                    <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                      {swot.strengths.map((s, idx) => <li key={idx}>{s}</li>)}
                    </ul>
                  </div>

                  {/* WEAKNESSES */}
                  <div className="p-5 rounded-2xl bg-rose-500/5 border border-rose-500/15 space-y-2">
                    <span className="text-[10px] font-bold text-rose-400 uppercase tracking-widest block">
                      Weaknesses (Debilidades)
                    </span>
                    <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                      {swot.weaknesses.map((w, idx) => <li key={idx}>{w}</li>)}
                    </ul>
                  </div>

                  {/* OPPORTUNITIES */}
                  <div className="p-5 rounded-2xl bg-indigo-500/5 border border-indigo-500/15 space-y-2">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block">
                      Opportunities (Oportunidades)
                    </span>
                    <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                      {swot.opportunities.map((o, idx) => <li key={idx}>{o}</li>)}
                    </ul>
                  </div>

                  {/* THREATS */}
                  <div className="p-5 rounded-2xl bg-amber-500/5 border border-amber-500/15 space-y-2">
                    <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block">
                      Threats (Amenazas)
                    </span>
                    <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                      {swot.threats.map((t, idx) => <li key={idx}>{t}</li>)}
                    </ul>
                  </div>

                </div>
              )}
            </div>
          </div>

        </div>
      )}

    </div>
  );
};
export default Diagnose;
