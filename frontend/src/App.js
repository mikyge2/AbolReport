import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/login`, { username, password });
      const { access_token, user_info } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user_info);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const Login = () => {
  const { login } = React.useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    const success = await login(username, password);
    if (!success) {
      setError('Invalid username or password');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    // Simple registration form - you can enhance this
    const role = 'headquarters'; // For demo, defaulting to headquarters
    
    try {
      await axios.post(`${API}/register`, {
        username,
        email: `${username}@company.com`,
        password,
        role
      });
      
      const success = await login(username, password);
      if (!success) {
        setError('Registration successful but login failed');
      }
    } catch (error) {
      setError('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">Factory Portal</h1>
          <p className="text-gray-600">Production & Sales Management System</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={isRegistering ? handleRegister : handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-primary hover:bg-primary-dark text-white font-medium py-2 px-4 rounded-md transition-colors"
          >
            {isRegistering ? 'Register' : 'Login'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-primary hover:text-primary-dark font-medium"
          >
            {isRegistering ? 'Already have an account? Login' : 'Need an account? Register'}
          </button>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Demo Credentials:</p>
          <p>Username: admin | Password: admin123</p>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = React.useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [factories, setFactories] = useState({});
  const [dailyLogs, setDailyLogs] = useState([]);
  const [dashboardData, setDashboardData] = useState({});

  useEffect(() => {
    fetchFactories();
    fetchDashboardData();
    fetchDailyLogs();
  }, []);

  const fetchFactories = async () => {
    try {
      const response = await axios.get(`${API}/factories`);
      setFactories(response.data);
    } catch (error) {
      console.error('Failed to fetch factories:', error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard-summary`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const fetchDailyLogs = async () => {
    try {
      const response = await axios.get(`${API}/daily-logs`);
      setDailyLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch daily logs:', error);
    }
  };

  const DashboardTab = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Total Production</h3>
        <p className="text-3xl font-bold text-primary">{dashboardData.total_production?.toLocaleString() || 0}</p>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Total Sales</h3>
        <p className="text-3xl font-bold text-secondary">{dashboardData.total_sales?.toLocaleString() || 0}</p>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Total Downtime</h3>
        <p className="text-3xl font-bold text-red-600">{dashboardData.total_downtime?.toLocaleString() || 0}h</p>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Total Stock</h3>
        <p className="text-3xl font-bold text-green-600">{dashboardData.total_stock?.toLocaleString() || 0}</p>
      </div>
    </div>
  );

  const LoggingTab = () => {
    const [selectedFactory, setSelectedFactory] = useState('');
    const [formData, setFormData] = useState({
      date: new Date().toISOString().split('T')[0],
      production_data: {},
      sales_data: {},
      downtime_hours: 0,
      downtime_reason: '',
      stock_data: {}
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/daily-logs`, {
          ...formData,
          factory_id: selectedFactory,
          date: new Date(formData.date).toISOString()
        });
        alert('Daily log submitted successfully!');
        fetchDailyLogs();
        fetchDashboardData();
      } catch (error) {
        alert('Failed to submit daily log: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-primary mb-6">Daily Production Log</h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Factory</label>
              <select
                value={selectedFactory}
                onChange={(e) => setSelectedFactory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                required
              >
                <option value="">Select Factory</option>
                {Object.entries(factories).map(([key, factory]) => (
                  <option key={key} value={key}>{factory.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({...formData, date: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Downtime Hours</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={formData.downtime_hours}
                onChange={(e) => setFormData({...formData, downtime_hours: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Downtime Reason</label>
              <input
                type="text"
                value={formData.downtime_reason}
                onChange={(e) => setFormData({...formData, downtime_reason: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., Machine maintenance, Power outage"
              />
            </div>
          </div>

          {selectedFactory && factories[selectedFactory] && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Products ({factories[selectedFactory].sku_unit})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {factories[selectedFactory].products.map((product) => (
                  <div key={product} className="border rounded-lg p-4">
                    <h4 className="font-medium text-gray-700 mb-2">{product}</h4>
                    <div className="space-y-2">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Production"
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        onChange={(e) => setFormData({
                          ...formData,
                          production_data: {
                            ...formData.production_data,
                            [product]: parseFloat(e.target.value) || 0
                          }
                        })}
                      />
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Sales Amount"
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        onChange={(e) => setFormData({
                          ...formData,
                          sales_data: {
                            ...formData.sales_data,
                            [product]: {
                              ...formData.sales_data[product],
                              amount: parseFloat(e.target.value) || 0
                            }
                          }
                        })}
                      />
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Unit Price"
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        onChange={(e) => setFormData({
                          ...formData,
                          sales_data: {
                            ...formData.sales_data,
                            [product]: {
                              ...formData.sales_data[product],
                              unit_price: parseFloat(e.target.value) || 0
                            }
                          }
                        })}
                      />
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Current Stock"
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        onChange={(e) => setFormData({
                          ...formData,
                          stock_data: {
                            ...formData.stock_data,
                            [product]: parseFloat(e.target.value) || 0
                          }
                        })}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-primary hover:bg-primary-dark text-white font-medium py-3 px-6 rounded-md transition-colors"
          >
            Submit Daily Log
          </button>
        </form>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-primary">Factory Portal</h1>
            </div>
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
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'dashboard'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('logging')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'logging'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Daily Logging
              </button>
            </nav>
          </div>
        </div>

        {activeTab === 'dashboard' && <DashboardTab />}
        {activeTab === 'logging' && <LoggingTab />}
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  return (
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
  );
};

export default App;