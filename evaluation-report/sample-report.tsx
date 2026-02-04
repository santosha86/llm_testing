/**
 * LLM Evaluation Report - Next.js Sample Component
 *
 * This is a sample report format showing how evaluation results
 * can be displayed in a modern web dashboard.
 */

import React from 'react';

// Types for the report data
interface TestResult {
  id: string;
  category: 'math' | 'logic' | 'reasoning' | 'long-context';
  question: string;
  expectedAnswer: string;
  baselineResponse: string;
  customerResponse: string;
  baselinePass: boolean;
  customerPass: boolean;
  baselineLatency: number;
  customerLatency: number;
}

interface CategoryScore {
  category: string;
  baselineScore: number;
  customerScore: number;
  gap: number;
  icon: string;
}

interface ReportData {
  reportDate: string;
  baselineProvider: string;
  customerProvider: string;
  overallBaseline: number;
  overallCustomer: number;
  categoryScores: CategoryScore[];
  testResults: TestResult[];
  criticalFailures: string[];
}

// Sample data - replace with actual API data
const sampleData: ReportData = {
  reportDate: '2026-02-04',
  baselineProvider: 'OpenAI GPT-4',
  customerProvider: 'Customer LLM',
  overallBaseline: 94,
  overallCustomer: 42,
  categoryScores: [
    { category: 'Mathematical Calculations', baselineScore: 85, customerScore: 35, gap: -50, icon: '🔢' },
    { category: 'Multi-Condition Logic', baselineScore: 90, customerScore: 40, gap: -50, icon: '🧠' },
    { category: 'Reasoning', baselineScore: 88, customerScore: 45, gap: -43, icon: '💡' },
    { category: 'Long-Context Retrieval', baselineScore: 95, customerScore: 30, gap: -65, icon: '📄' },
  ],
  testResults: [
    {
      id: 'M-1',
      category: 'math',
      question: 'Calculate annual energy output for Al Faisaliah (15 MW, 28% CF)',
      expectedAnswer: '36,792 MWh',
      baselineResponse: '36,792 MWh',
      customerResponse: 'Approximately 35,000 MWh',
      baselinePass: true,
      customerPass: false,
      baselineLatency: 1.2,
      customerLatency: 3.5,
    },
    {
      id: 'L-1',
      category: 'logic',
      question: 'Is Bidder C eligible based on all 5 rules?',
      expectedAnswer: 'NO - fails local content requirement (28% < 30%)',
      baselineResponse: 'No, Bidder C is not eligible. Local content is 28%, below the 30% minimum.',
      customerResponse: 'Yes, Bidder C appears to meet the requirements.',
      baselinePass: true,
      customerPass: false,
      baselineLatency: 1.8,
      customerLatency: 2.1,
    },
    {
      id: 'LC-1',
      category: 'long-context',
      question: 'When did the ECRA framework become effective?',
      expectedAnswer: 'March 15, 2023',
      baselineResponse: 'The framework became effective on March 15, 2023.',
      customerResponse: 'The framework was implemented in 2023.',
      baselinePass: true,
      customerPass: false,
      baselineLatency: 2.0,
      customerLatency: 4.5,
    },
  ],
  criticalFailures: [
    'Math accuracy: Customer LLM fails 65% of numerical calculations',
    'Hallucination detected: Invented details for non-existent projects',
    'Context loss: Cannot retrieve information beyond first 20% of document',
    'Logic errors: Fails to apply multiple conditions correctly',
  ],
};

// Score Card Component
const ScoreCard: React.FC<{ title: string; score: number; color: string; subtitle?: string }> = ({
  title,
  score,
  color,
  subtitle,
}) => (
  <div className="bg-white rounded-xl shadow-lg p-6 border-l-4" style={{ borderLeftColor: color }}>
    <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wide">{title}</h3>
    <div className="mt-2 flex items-baseline">
      <span className="text-4xl font-bold" style={{ color }}>
        {score}%
      </span>
      {subtitle && <span className="ml-2 text-sm text-gray-500">{subtitle}</span>}
    </div>
  </div>
);

// Progress Bar Component
const ProgressBar: React.FC<{ baseline: number; customer: number; label: string; icon: string }> = ({
  baseline,
  customer,
  label,
  icon,
}) => (
  <div className="mb-6">
    <div className="flex justify-between items-center mb-2">
      <span className="text-sm font-medium text-gray-700">
        {icon} {label}
      </span>
      <span className="text-sm text-gray-500">
        Gap: <span className="text-red-600 font-semibold">{customer - baseline}%</span>
      </span>
    </div>
    <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
      {/* Baseline bar */}
      <div
        className="absolute top-0 left-0 h-4 bg-green-500 rounded-full"
        style={{ width: `${baseline}%` }}
      />
      {/* Customer bar */}
      <div
        className="absolute bottom-0 left-0 h-4 bg-red-400 rounded-full"
        style={{ width: `${customer}%` }}
      />
    </div>
    <div className="flex justify-between mt-1 text-xs text-gray-500">
      <span>Baseline: {baseline}%</span>
      <span>Customer: {customer}%</span>
    </div>
  </div>
);

// Test Result Row Component
const TestResultRow: React.FC<{ result: TestResult }> = ({ result }) => (
  <tr className="border-b hover:bg-gray-50">
    <td className="py-4 px-4">
      <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">{result.id}</span>
    </td>
    <td className="py-4 px-4">
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${
          result.category === 'math'
            ? 'bg-blue-100 text-blue-800'
            : result.category === 'logic'
            ? 'bg-purple-100 text-purple-800'
            : result.category === 'reasoning'
            ? 'bg-yellow-100 text-yellow-800'
            : 'bg-green-100 text-green-800'
        }`}
      >
        {result.category}
      </span>
    </td>
    <td className="py-4 px-4 max-w-xs">
      <p className="text-sm text-gray-900 truncate" title={result.question}>
        {result.question}
      </p>
    </td>
    <td className="py-4 px-4">
      <code className="text-xs bg-gray-100 px-2 py-1 rounded">{result.expectedAnswer}</code>
    </td>
    <td className="py-4 px-4 text-center">
      {result.baselinePass ? (
        <span className="text-green-600 text-xl">✓</span>
      ) : (
        <span className="text-red-600 text-xl">✗</span>
      )}
      <div className="text-xs text-gray-500">{result.baselineLatency}s</div>
    </td>
    <td className="py-4 px-4 text-center">
      {result.customerPass ? (
        <span className="text-green-600 text-xl">✓</span>
      ) : (
        <span className="text-red-600 text-xl">✗</span>
      )}
      <div className="text-xs text-gray-500">{result.customerLatency}s</div>
    </td>
  </tr>
);

// Main Report Component
const LLMEvaluationReport: React.FC<{ data?: ReportData }> = ({ data = sampleData }) => {
  const passRateDiff = data.overallBaseline - data.overallCustomer;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 to-blue-700 text-white py-8">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="text-3xl font-bold">LLM Capability Evaluation Report</h1>
          <p className="mt-2 text-blue-200">
            Comparative analysis: {data.baselineProvider} vs {data.customerProvider}
          </p>
          <p className="text-sm text-blue-300 mt-1">Generated: {data.reportDate}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Executive Summary */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Executive Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <ScoreCard
              title="Baseline (GPT-4)"
              score={data.overallBaseline}
              color="#10B981"
              subtitle="Pass Rate"
            />
            <ScoreCard
              title="Customer LLM"
              score={data.overallCustomer}
              color="#EF4444"
              subtitle="Pass Rate"
            />
            <ScoreCard title="Performance Gap" score={passRateDiff} color="#F59E0B" subtitle="Difference" />
          </div>
        </section>

        {/* Key Finding Alert */}
        <section className="mb-10">
          <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-r-lg">
            <div className="flex items-start">
              <span className="text-2xl mr-4">⚠️</span>
              <div>
                <h3 className="text-lg font-semibold text-red-800">Critical Finding</h3>
                <p className="text-red-700 mt-1">
                  Customer LLM shows a <strong>{passRateDiff}% lower pass rate</strong> compared to baseline.
                  This gap indicates significant capability limitations that may impact production use cases.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Category Breakdown */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Performance by Category</h2>
          <div className="bg-white rounded-xl shadow-lg p-6">
            {data.categoryScores.map((cat) => (
              <ProgressBar
                key={cat.category}
                baseline={cat.baselineScore}
                customer={cat.customerScore}
                label={cat.category}
                icon={cat.icon}
              />
            ))}
          </div>
        </section>

        {/* Critical Failures */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Critical Failures Identified</h2>
          <div className="bg-white rounded-xl shadow-lg p-6">
            <ul className="space-y-3">
              {data.criticalFailures.map((failure, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-red-500 mr-3">●</span>
                  <span className="text-gray-700">{failure}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Detailed Test Results */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Detailed Test Results</h2>
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">
                      Test ID
                    </th>
                    <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">
                      Category
                    </th>
                    <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">
                      Question
                    </th>
                    <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">
                      Expected
                    </th>
                    <th className="py-3 px-4 text-center text-xs font-semibold text-gray-600 uppercase">
                      Baseline
                    </th>
                    <th className="py-3 px-4 text-center text-xs font-semibold text-gray-600 uppercase">
                      Customer
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.testResults.map((result) => (
                    <TestResultRow key={result.id} result={result} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Recommendations */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Recommendations</h2>
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border-l-4 border-yellow-500 pl-4">
                <h3 className="font-semibold text-gray-800">Short-term</h3>
                <p className="text-gray-600 mt-1">
                  Use baseline LLM (GPT-4) for production to ensure accuracy and reliability.
                </p>
              </div>
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-semibold text-gray-800">Long-term</h3>
                <p className="text-gray-600 mt-1">
                  Work with customer to fine-tune their model on domain-specific data to improve performance.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center text-gray-500 text-sm py-8 border-t">
          <p>LLM Evaluation Report | Generated automatically by the evaluation framework</p>
          <p className="mt-1">For questions, contact the AI/ML team</p>
        </footer>
      </main>
    </div>
  );
};

export default LLMEvaluationReport;
