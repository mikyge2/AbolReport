// src/components/Dashboard.js
import React, { useState, useContext, useMemo, Suspense, lazy } from 'react';
import { AuthContext } from '../context/AuthContext';

// Lazy load components for better performance
const DashboardTab = lazy(() => import('./DashboardTab'));
const LoggingTab = lazy(() => import('./LoggingTab'));
const ReportsTab = lazy(() => import('./ReportsTab'));
const UserManagementTab = lazy(() => import('./UserManagementTab'));

// Futuristic loading skeleton component
const LoadingSkeleton = () => (
  <div className="space-y-4 sm:space-y-6">
    <div className="glass-card p-4 sm:p-6">
      <div className="animate-pulse">
        <div className="h-6 sm:h-8 bg-gradient-to-r from-white/20 to-white/10 rounded w-1/2 sm:w-1/3 mb-3 sm:mb-4"></div>
        <div className="space-y-2 sm:space-y-3">
          <div className="h-3 sm:h-4 bg-gradient-to-r from-white/20 to-white/10 rounded w-full"></div>
          <div className="h-3 sm:h-4 bg-gradient-to-r from-white/20 to-white/10 rounded w-3/4"></div>
          <div className="h-3 sm:h-4 bg-gradient-to-r from-white/20 to-white/10 rounded w-1/2"></div>
        </div>
      </div>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="glass-card p-4 sm:p-6">
          <div className="animate-pulse">
            <div className="h-5 sm:h-6 bg-gradient-to-r from-white/20 to-white/10 rounded w-2/3 mb-2 sm:mb-3"></div>
            <div className="h-24 sm:h-32 bg-gradient-to-r from-white/20 to-white/10 rounded mb-2 sm:mb-3"></div>
            <div className="h-3 sm:h-4 bg-gradient-to-r from-white/20 to-white/10 rounded w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isTabLoading, setIsTabLoading] = useState(false);
  const { user, logout } = useContext(AuthContext);

  // Memoize tab configuration to prevent unnecessary re-renders
  const tabs = useMemo(() => [
    { id: 'dashboard', label: 'Dashboard', component: DashboardTab },
    { id: 'logging', label: 'Daily Logging', component: LoggingTab },
    { id: 'reports', label: 'Reports & Analytics', component: ReportsTab },
    ...(user?.role === 'headquarters' ? [{ id: 'users', label: 'User Management', component: UserManagementTab }] : [])
  ], [user?.role]);

  const handleTabChange = (tabId) => {
    if (tabId !== activeTab) {
      setIsTabLoading(true);
      setActiveTab(tabId);
      // Simulate tab loading time for smooth UX
      setTimeout(() => setIsTabLoading(false), 300);
    }
  };

  const renderActiveTab = () => {
    const currentTab = tabs.find(tab => tab.id === activeTab);
    if (!currentTab) return null;

    const Component = currentTab.component;
    return (
      <Suspense fallback={<LoadingSkeleton />}>
        <div className={`transition-opacity duration-300 ${isTabLoading ? 'opacity-50' : 'opacity-100'}`}>
          <Component />
        </div>
      </Suspense>
    );
  };

  return (
    <div className="min-h-screen futuristic-bg">
      {/* Floating background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-4 h-4 bg-[#ffc72c] opacity-40 rotate-45 animate-float"></div>
        <div className="absolute top-1/3 right-1/3 w-6 h-6 border-2 border-[#ffc72c] opacity-30 animate-float-delayed"></div>
        <div className="absolute bottom-1/4 left-1/3 w-3 h-3 bg-white opacity-20 rounded-full animate-float-slow"></div>
        <div className="absolute bottom-1/3 right-1/4 w-5 h-5 border-2 border-white opacity-15 rotate-45 animate-float"></div>
        <div className="absolute top-1/2 left-1/6 w-2 h-2 bg-[#1a355b] opacity-25 animate-float-delayed"></div>
        <div className="absolute top-3/4 right-1/6 w-3 h-3 border border-[#ffc72c] opacity-20 animate-float-slow"></div>
      </div>

      <nav className="futuristic-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-r from-[#1a355b] to-[#ffc72c] rounded-lg flex items-center justify-center">
                <svg className="w-3 h-3 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h1 className="text-lg sm:text-xl font-bold text-futuristic-primary">Factory Portal</h1>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="hidden sm:block">
                <span className="text-xs sm:text-sm text-futuristic-secondary">Welcome, {user?.username}</span>
              </div>
              <span className="text-xxs sm:text-xs bg-gradient-to-r from-[#ffc72c] to-[#1a355b] text-white px-2 py-1 sm:px-3 sm:py-1 rounded-full font-medium">
                {user?.role === 'headquarters' ? 'HQ' : 'Factory'}
              </span>
              <button
                onClick={logout}
                className="text-xs sm:text-sm text-futuristic-muted hover:text-[#ffc72c] transition-colors duration-200 px-2 py-1"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-8">
        <div className="mb-4 sm:mb-8">
          <nav className="flex space-x-1 sm:space-x-2 backdrop-blur-lg bg-white/5 rounded-2xl p-1 sm:p-2 border border-white/10 nav-mobile-wrapper">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''} touch-friendly`}
                disabled={isTabLoading}
              >
                <span className="block sm:inline">{tab.label}</span>
                {isTabLoading && activeTab === tab.id && (
                  <span className="ml-1 sm:ml-2 inline-block w-3 h-3 border border-[#ffc72c] border-t-transparent rounded-full animate-spin"></span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="transition-all duration-500 ease-in-out">
          {renderActiveTab()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
