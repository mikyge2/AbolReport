// src/components/Dashboard.js
import React, { useState, useContext } from 'react';
import DashboardTab from './DashboardTab';
import LoggingTab from './LoggingTab';
import ReportsTab from './ReportsTab';
import { AuthContext } from '../context/AuthContext';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { user, logout } = useContext(AuthContext);

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
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'dashboard'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('logging')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'logging'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Daily Logging
            </button>
            <button
              onClick={() => setActiveTab('reports')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'reports'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              Reports & Analytics
            </button>
          </nav>
        </div>

        {activeTab === 'dashboard' && <DashboardTab />}
        {activeTab === 'logging' && <LoggingTab />}
        {activeTab === 'reports' && <ReportsTab />}
      </div>
    </div>
  );
};

export default Dashboard;
