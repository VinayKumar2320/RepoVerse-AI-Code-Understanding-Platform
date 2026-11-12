'use client';

import React, { useState, useEffect } from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { AdaptiveExplanation, LearningStep } from '../../types';
import {
  GraduationCap,
  BookOpen,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  Code2,
  FileText,
  Lightbulb,
  AlertTriangle,
  Compass
} from 'lucide-react';

export const AdaptiveLearningStudio: React.FC = () => {
  const { currentRepo, experienceLevel, setSelectedFile } = useRepoStore();
  const [explanation, setExplanation] = useState<AdaptiveExplanation | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [selectedQuizAnswers, setSelectedQuizAnswers] = useState<Record<number, string>>({});

  useEffect(() => {
    const fetchLearning = async () => {
      if (!currentRepo) return;
      setLoading(true);
      try {
        const data = await api.getAdaptiveLearning(currentRepo.id, experienceLevel);
        setExplanation(data);
      } catch (e) {
        console.error('Failed to load adaptive learning explanation:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchLearning();
  }, [currentRepo, experienceLevel]);

  const toggleStepCompleted = (stepId: number) => {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) next.delete(stepId);
      else next.add(stepId);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <GraduationCap className="w-10 h-10 mb-3 animate-bounce text-brand-400" />
        <p>Tailoring adaptive curriculum for {experienceLevel} level...</p>
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="text-center p-12 text-slate-400">
        Adaptive learning not available for this repository yet.
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-2">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center space-x-2 text-brand-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <Compass className="w-4 h-4" />
          <span>Explain This Repository Like I&apos;m New Here ({experienceLevel.toUpperCase()} MODE)</span>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">
          {experienceLevel === 'beginner'
            ? 'Gentle Conceptual Introduction'
            : experienceLevel === 'senior'
            ? 'Architectural Tradeoffs & Cohesion Assessment'
            : 'Engineering Architecture & Source Flow'}
        </h2>
        <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
          {explanation.overview}
        </p>

        {/* Mental Model */}
        {explanation.mental_model && (
          <div className="mt-4 p-4 bg-slate-950/80 rounded-lg border border-indigo-500/20 flex items-start space-x-3">
            <Lightbulb className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-xs font-bold text-amber-300 uppercase tracking-wider block mb-1">
                Mental Model
              </span>
              <p className="text-xs text-slate-300 leading-relaxed">
                {explanation.mental_model}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Senior Mode Patterns & Pitfalls */}
      {experienceLevel === 'senior' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {explanation.tradeoffs_and_patterns && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-bold text-emerald-400 flex items-center space-x-2 mb-3">
                <CheckCircle2 className="w-4 h-4" />
                <span>Verified Architectural Patterns</span>
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {explanation.tradeoffs_and_patterns.map((p, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {explanation.common_pitfalls && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-bold text-rose-400 flex items-center space-x-2 mb-3">
                <AlertTriangle className="w-4 h-4" />
                <span>Hotspots & Refactoring Opportunities</span>
              </h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {explanation.common_pitfalls.map((p, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-rose-500 font-bold">•</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Guided Walkthrough Steps */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-white flex items-center justify-between">
          <span>Guided Walkthrough</span>
          <span className="text-xs text-slate-400 font-normal">
            {completedSteps.size} of {explanation.steps.length} completed
          </span>
        </h3>

        {explanation.steps.map((step) => {
          const isDone = completedSteps.has(step.step_id);

          return (
            <div
              key={step.step_id}
              className={`bg-slate-900 border rounded-xl p-5 transition ${
                isDone ? 'border-emerald-500/40 bg-slate-900/50' : 'border-slate-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <button
                    onClick={() => toggleStepCompleted(step.step_id)}
                    className={`mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition ${
                      isDone
                        ? 'bg-emerald-600 border-emerald-500 text-white'
                        : 'border-slate-700 bg-slate-950 hover:border-slate-500'
                    }`}
                  >
                    {isDone && <CheckCircle2 className="w-3.5 h-3.5" />}
                  </button>
                  <div>
                    <span className="text-xs font-semibold text-brand-400 uppercase tracking-wider block">
                      {step.difficulty}
                    </span>
                    <h4 className="text-base font-bold text-slate-100 mt-0.5">{step.title}</h4>
                  </div>
                </div>
              </div>

              <div className="mt-3 text-sm text-slate-300 leading-relaxed pl-8">
                <p>{step.detailed_explanation}</p>

                {/* Key Takeaways */}
                {step.key_takeaways.length > 0 && (
                  <div className="mt-3 bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      Key Takeaways
                    </span>
                    <ul className="space-y-1 text-xs text-slate-300">
                      {step.key_takeaways.map((k, i) => (
                        <li key={i} className="flex items-center space-x-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-500"></span>
                          <span>{k}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Citations & Suggested Files */}
                {step.citations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {step.citations.map((c, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedFile(c.file_path, c.start_line)}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded-md text-xs font-mono text-indigo-300 border border-slate-700/60 flex items-center space-x-1.5 transition"
                      >
                        <FileText className="w-3 h-3 text-slate-400" />
                        <span>{c.file_path}:{c.start_line}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Comprehension Quiz Check */}
                {step.comprehension_check && (
                  <div className="mt-4 p-4 bg-slate-950 rounded-lg border border-indigo-500/20">
                    <span className="text-xs font-bold text-indigo-400 flex items-center space-x-1 mb-2">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Comprehension Check</span>
                    </span>
                    <p className="text-xs text-slate-200 mb-3">{step.comprehension_check.question}</p>
                    <div className="space-y-2">
                      {step.comprehension_check.options.map((opt, i) => {
                        const isSelected = selectedQuizAnswers[step.step_id] === opt;
                        const isCorrect = opt === step.comprehension_check?.correct;
                        return (
                          <button
                            key={i}
                            onClick={() => setSelectedQuizAnswers((p) => ({ ...p, [step.step_id]: opt }))}
                            className={`w-full text-left px-3 py-1.5 rounded-md text-xs transition border ${
                              isSelected
                                ? isCorrect
                                  ? 'bg-emerald-950/50 border-emerald-500 text-emerald-200'
                                  : 'bg-rose-950/50 border-rose-500 text-rose-200'
                                : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                            }`}
                          >
                            {opt} {isSelected && (isCorrect ? '✓ Correct' : '✗ Try again')}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
