import React, { useState } from 'react';
import ValueAddedTab from './components/ValueAddedTab';
import LiveDemoTab from './components/LiveDemoTab';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './components/pages/Dashboard';
import Configuration from './components/pages/Configuration';
import Evaluation from './components/pages/Evaluation';
import Reports from './components/pages/Reports';

type TabType = 'dashboard' | 'configuration' | 'evaluation' | 'reports' | 'value' | 'demo';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  // Check URL hash for hidden tabs (legacy chatbot access)
  React.useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (hash === 'chatbot' || hash === 'demo') {
      setActiveTab('demo');
    } else if (hash === 'value') {
      setActiveTab('value');
    }
  }, []);

  const handleNavigate = (tab: string) => {
    setActiveTab(tab as TabType);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'configuration':
        return <Configuration />;
      case 'evaluation':
        return <Evaluation />;
      case 'reports':
        return <Reports />;
      case 'value':
        return <ValueAddedTab />;
      case 'demo':
        return <LiveDemoTab />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  // Navigation items for the new LLM Evaluation Tool
  const navItems: { id: TabType; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '&#127968;' },
    { id: 'configuration', label: 'Configuration', icon: '&#9881;&#65039;' },
    { id: 'evaluation', label: 'Evaluation', icon: '&#9889;' },
    { id: 'reports', label: 'Reports', icon: '&#128202;' },
  ];

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-[#f5f7fa] pb-12">
        {/* Header Container */}
        <div className="max-w-[1400px] mx-auto pt-6 px-4 md:px-8">
          <div className="bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 rounded-b-2xl shadow-xl p-6 flex items-center justify-between relative overflow-hidden">
            {/* Background Decorative Circles */}
            <div className="absolute top-0 left-0 w-64 h-64 bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2 blur-2xl pointer-events-none"></div>
            <div className="absolute bottom-0 right-0 w-64 h-64 bg-black/10 rounded-full translate-x-1/2 translate-y-1/2 blur-2xl pointer-events-none"></div>

            {/* Left Icon */}
            <div className="hidden md:flex w-[140px] h-[80px] bg-white rounded-lg p-[3px] shrink-0 items-center justify-center shadow-lg">
              <img src="public/left-icon.png" alt="Logo" className="w-full h-full object-contain" />
            </div>

            {/* Title Section */}
            <div className="flex-1 text-center z-10">
              <div className="flex items-center justify-center gap-3">
                <div className="flex flex-col items-center">
                  <h1 className="text-2xl md:text-3xl font-bold text-white drop-shadow-md tracking-tight">
                    LLM Evaluation Tool
                  </h1>
                  <p className="text-blue-200 text-sm font-medium mt-1 opacity-90">
                    Baseline vs Target Model Comparison
                  </p>
                </div>
              </div>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-4 z-10">
              <div className="hidden md:flex w-[140px] h-[80px] bg-white rounded-lg p-[3px] shrink-0 items-center justify-center shadow-lg">
                <img src="public/right-icon.png" alt="Company Logo" className="w-full h-full object-contain" />
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="mt-8 mb-6 flex space-x-2 border-b border-gray-200">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-6 py-3 font-semibold text-sm rounded-t-lg transition-all duration-200 flex items-center gap-2 ${
                  activeTab === item.id
                    ? 'bg-white text-blue-700 border-b-2 border-blue-700 shadow-sm'
                    : 'text-gray-500 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                <span className="text-lg" dangerouslySetInnerHTML={{ __html: item.icon }} />
                {item.label}
              </button>
            ))}
          </div>

          {/* Main Content Area */}
          <main className="min-h-[600px]">
            {renderContent()}
          </main>

          {/* Footer */}
          <footer className="mt-12 text-center text-gray-500 text-sm">
            <p>LLM Evaluation Tool | Compare baseline and target model capabilities</p>
            <p className="mt-1 text-xs text-gray-400">
              Access legacy chatbot: <a href="#chatbot" className="text-blue-500 hover:underline" onClick={() => setActiveTab('demo')}>Chatbot Demo</a>
            </p>
          </footer>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default App;
