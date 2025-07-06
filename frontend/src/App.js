import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import './App.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

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

  const DashboardTab = () => {
    const [analyticsData, setAnalyticsData] = useState({});
    const [comparisonData, setComparisonData] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      fetchAnalyticsData();
      if (user.role === 'headquarters') {
        fetchComparisonData();
      }
    }, []);

    const fetchAnalyticsData = async () => {
      try {
        const response = await axios.get(`${API}/analytics/trends?days=30`);
        setAnalyticsData(response.data);
      } catch (error) {
        console.error('Failed to fetch analytics data:', error);
        toast.error('Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    const fetchComparisonData = async () => {
      try {
        const response = await axios.get(`${API}/analytics/factory-comparison?days=30`);
        setComparisonData(response.data);
      } catch (error) {
        console.error('Failed to fetch comparison data:', error);
      }
    };

    const exportToExcel = async () => {
      try {
        toast.loading('Generating Excel report...');
        const response = await axios.get(`${API}/export-excel`, {
          responseType: 'blob'
        });
        
        const blob = new Blob([response.data], { 
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `factory_report_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        toast.success('Excel report downloaded successfully!');
      } catch (error) {
        console.error('Failed to export Excel:', error);
        toast.error('Failed to export Excel report');
      }
    };

    const productionChartData = {
      labels: analyticsData.dates || [],
      datasets: [
        {
          label: 'Production',
          data: analyticsData.production || [],
          borderColor: 'rgb(26, 53, 91)',
          backgroundColor: 'rgba(26, 53, 91, 0.1)',
          tension: 0.1,
        },
        {
          label: 'Sales',
          data: analyticsData.sales || [],
          borderColor: 'rgb(255, 199, 44)',
          backgroundColor: 'rgba(255, 199, 44, 0.1)',
          tension: 0.1,
        },
      ],
    };

    const downtimeChartData = {
      labels: analyticsData.dates || [],
      datasets: [
        {
          label: 'Downtime Hours',
          data: analyticsData.downtime || [],
          backgroundColor: 'rgba(239, 68, 68, 0.6)',
          borderColor: 'rgb(239, 68, 68)',
          borderWidth: 1,
        },
      ],
    };

    const factoryComparisonData = {
      labels: Object.values(comparisonData).map(factory => factory.name),
      datasets: [
        {
          label: 'Production',
          data: Object.values(comparisonData).map(factory => factory.production),
          backgroundColor: 'rgba(26, 53, 91, 0.6)',
        },
        {
          label: 'Sales',
          data: Object.values(comparisonData).map(factory => factory.sales),
          backgroundColor: 'rgba(255, 199, 44, 0.6)',
        },
      ],
    };

    const efficiencyData = {
      labels: Object.values(comparisonData).map(factory => factory.name),
      datasets: [
        {
          label: 'Efficiency %',
          data: Object.values(comparisonData).map(factory => factory.efficiency),
          backgroundColor: [
            'rgba(26, 53, 91, 0.6)',
            'rgba(255, 199, 44, 0.6)',
            'rgba(34, 197, 94, 0.6)',
            'rgba(168, 85, 247, 0.6)',
          ],
          borderColor: [
            'rgb(26, 53, 91)',
            'rgb(255, 199, 44)',
            'rgb(34, 197, 94)',
            'rgb(168, 85, 247)',
          ],
          borderWidth: 1,
        },
      ],
    };

    return (
      <div className="space-y-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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

        {/* Export Button */}
        <div className="flex justify-end">
          <button
            onClick={exportToExcel}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
            </svg>
            <span>Export Excel Report</span>
          </button>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Production & Sales Trend */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Production & Sales Trend (30 Days)</h3>
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : (
              <Line data={productionChartData} options={{
                responsive: true,
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }} />
            )}
          </div>

          {/* Downtime Analysis */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Downtime Analysis (30 Days)</h3>
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : (
              <Bar data={downtimeChartData} options={{
                responsive: true,
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }} />
            )}
          </div>

          {/* Factory Comparison - Only for headquarters */}
          {user.role === 'headquarters' && (
            <>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Factory Performance Comparison</h3>
                {Object.keys(comparisonData).length > 0 ? (
                  <Bar data={factoryComparisonData} options={{
                    responsive: true,
                    scales: {
                      y: {
                        beginAtZero: true,
                      },
                    },
                  }} />
                ) : (
                  <div className="flex justify-center items-center h-64">
                    <p className="text-gray-500">No data available</p>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Factory Efficiency</h3>
                {Object.keys(comparisonData).length > 0 ? (
                  <Doughnut data={efficiencyData} options={{
                    responsive: true,
                    plugins: {
                      legend: {
                        position: 'bottom',
                      },
                    },
                  }} />
                ) : (
                  <div className="flex justify-center items-center h-64">
                    <p className="text-gray-500">No data available</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Factory Summaries */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Factory Summaries</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(dashboardData.factory_summaries || {}).map(([factoryId, summary]) => (
              <div key={factoryId} className="border rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">{summary.name}</h4>
                <div className="space-y-1 text-sm">
                  <p>Production: <span className="font-semibold">{summary.production?.toLocaleString()}</span></p>
                  <p>Sales: <span className="font-semibold">{summary.sales?.toLocaleString()}</span></p>
                  <p>Downtime: <span className="font-semibold">{summary.downtime}h</span></p>
                  <p>Stock: <span className="font-semibold">{summary.stock?.toLocaleString()}</span></p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

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
      const submitToast = toast.loading('Submitting daily log...');
      
      try {
        await axios.post(`${API}/daily-logs`, {
          ...formData,
          factory_id: selectedFactory,
          date: new Date(formData.date).toISOString()
        });
        
        toast.success('Daily log submitted successfully!', { id: submitToast });
        fetchDailyLogs();
        fetchDashboardData();
        
        // Reset form
        setFormData({
          date: new Date().toISOString().split('T')[0],
          production_data: {},
          sales_data: {},
          downtime_hours: 0,
          downtime_reason: '',
          stock_data: {}
        });
        setSelectedFactory('');
        
      } catch (error) {
        toast.error('Failed to submit daily log: ' + (error.response?.data?.detail || 'Unknown error'), { id: submitToast });
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
              <button
                onClick={() => setActiveTab('reports')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'reports'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Reports & Analytics
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