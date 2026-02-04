import React from 'react';
import InfoPanel from './InfoPanel';
import ChatWidget from './ChatWidget';
import UsageStats from './UsageStats';

const LiveDemoTab: React.FC = () => {
  return (
    <div className="animate-in fade-in duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Side - Info Panel */}
        <div className="lg:col-span-5">
          <InfoPanel />
        </div>

        {/* Right Side - Chat Widget (Mobile style) */}
        <div className="lg:col-span-7">
           <ChatWidget />
        </div>
      </div>

      {/* Bottom - Usage Stats */}
      <UsageStats />
    </div>
  );
};

export default LiveDemoTab;