import React, { useState } from 'react';
import ValueAddedTab from './components/ValueAddedTab';
import LiveDemoTab from './components/LiveDemoTab';
import ErrorBoundary from './components/ErrorBoundary';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'value' | 'demo'>('value');

  return (
    <ErrorBoundary>
    <div className="min-h-screen bg-[#f5f7fa] pb-12">
      {/* Header Container */}
      <div className="max-w-[1400px] mx-auto pt-6 px-4 md:px-8">
        <div className="bg-gradient-to-br from-teal-700 via-teal-600 to-teal-800 rounded-b-2xl shadow-xl p-6 flex items-center justify-between relative overflow-hidden">
          {/* Background Decorative Circles */}
          <div className="absolute top-0 left-0 w-64 h-64 bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2 blur-2xl pointer-events-none"></div>
          <div className="absolute bottom-0 right-0 w-64 h-64 bg-black/10 rounded-full translate-x-1/2 translate-y-1/2 blur-2xl pointer-events-none"></div>

          {/* Left Icon */}
          <div className="hidden md:flex w-[140px] h-[80px] bg-white rounded-lg p-[3px] shrink-0 items-center justify-center shadow-lg">
             <img src="public/left-icon.png" alt="SPB Logo" className="w-full h-full object-contain" />
          </div>

          {/* Title Section */}
          <div className="flex-1 text-center z-10">
            <div className="flex items-center justify-center gap-3">
              <span className="text-2xl">🚚</span>
              <div className="flex flex-col items-center">
                <h1 className="text-2xl md:text-3xl font-bold text-yellow-400 drop-shadow-md tracking-tight">
                  SPB - Conversational Chatbot
                </h1>
                <p className="text-indigo-100 text-sm font-medium mt-1 opacity-90">
                  Dispatch & Operations Assistant
                </p>
              </div>
              <span className="text-2xl">⛽</span>
              <span className="bg-yellow-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg border border-yellow-400/50">
                POC4
              </span>
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4 z-10">
            <div className="hidden md:flex w-[140px] h-[80px] bg-white rounded-lg p-[3px] shrink-0 items-center justify-center shadow-lg">
               <img src="public/right-icon.png" alt="Norconsult Telematics" className="w-full h-full object-contain" />
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mt-8 mb-6 flex space-x-2 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('value')}
            className={`px-6 py-3 font-semibold text-sm rounded-t-lg transition-all duration-200 flex items-center gap-2 ${
              activeTab === 'value'
                ? 'bg-white text-teal-700 border-b-2 border-teal-700 shadow-sm'
                : 'text-gray-500 hover:text-teal-600 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">💡</span> Value Added
          </button>
          <button
            onClick={() => setActiveTab('demo')}
            className={`px-6 py-3 font-semibold text-sm rounded-t-lg transition-all duration-200 flex items-center gap-2 ${
              activeTab === 'demo'
                ? 'bg-white text-teal-700 border-b-2 border-teal-700 shadow-sm'
                : 'text-gray-500 hover:text-teal-600 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">🎯</span> Live Demo
          </button>
        </div>

        {/* Main Content Area */}
        <main className="min-h-[600px]">
          {activeTab === 'value' ? <ValueAddedTab /> : <LiveDemoTab />}
        </main>
      </div>
    </div>
    </ErrorBoundary>
  );
};

export default App;