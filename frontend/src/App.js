// src/App.js
import React, { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { registerCharts } from './utils/registerCharts';
import './App.css';

const App = () => {
  useEffect(() => {
    registerCharts();
  }, []);

  return (
    <div>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            iconTheme: {
              primary: '#4ade80',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <AuthProvider>
        <AuthContext.Consumer>
          {({ user, loading }) => {
            if (loading) {
              return (
                <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading...</p>
                  </div>
                </div>
              );
            }
            return user ? <Dashboard /> : <Login />;
          }}
        </AuthContext.Consumer>
        
      </AuthProvider>
    </div>
  );
};

export default App;
