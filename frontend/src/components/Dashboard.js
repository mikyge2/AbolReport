// src/components/Dashboard.js
import React, { useState, useContext, useMemo, Suspense, lazy } from 'react';
import { AuthContext } from '../context/AuthContext';

// Lazy load components for better performance
const DashboardTab = lazy(() => import('./DashboardTab'));
const LoggingTab = lazy(() => import('./LoggingTab'));
const ReportsTab = lazy(() => import('./ReportsTab'));
const UserManagementTab = lazy(() => import('./UserManagementTab'));

// Loading skeleton component
const LoadingSkeleton = () => (
  <div className="space-y-6">
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="animate-pulse">
        <div className="h-8 bg-gray-300 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-300 rounded w-full"></div>
          <div className="h-4 bg-gray-300 rounded w-3/4"></div>
          <div className="h-4 bg-gray-300 rounded w-1/2"></div>
        </div>
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-lg shadow-md p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-2/3 mb-3"></div>
            <div className="h-32 bg-gray-300 rounded mb-3"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
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
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold text-primary">Factory Portal</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.username}</span>
              <span className="text-xs bg-secondary text-primary px-2 py-1 rounded">
                {user?.role === 'headquarters' ? 'HQ' : 'Factory'}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                disabled={isTabLoading}
              >
                {tab.label}
                {isTabLoading && activeTab === tab.id && (
                  <span className="ml-2 inline-block w-3 h-3 border border-primary border-t-transparent rounded-full animate-spin"></span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="transition-all duration-300 ease-in-out">
          {renderActiveTab()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
