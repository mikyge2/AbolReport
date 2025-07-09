// src/components/DashboardTab.js
import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
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
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

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

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DashboardTab = () => {
    const { user, token } = useContext(AuthContext);
    const [analyticsData, setAnalyticsData] = useState({});
    const [comparisonData, setComparisonData] = useState({});
    const [dashboardData, setDashboardData] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Create axios instance with auth headers
    const authAxios = axios.create({
        baseURL: API,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });

    useEffect(() => {
        if (token && user) {
            console.log('User:', user);
            console.log('Token exists:', !!token);
            fetchAllData();
        } else {
            console.log('No token or user available');
            setError('Authentication required');
            setLoading(false);
        }
    }, [token, user]);

    const fetchAllData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Fetch analytics data
            await fetchAnalyticsData();
            
            // Fetch dashboard data
            await fetchDashboardData();
            
            // Fetch comparison data for headquarters
            if (user?.role === 'headquarters') {
                await fetchComparisonData();
            }
        } catch (err) {
            console.error('Error fetching dashboard data:', err);
            setError(err.message || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    const fetchAnalyticsData = async () => {
        try {
            console.log('Fetching analytics data...');
            const res = await authAxios.get('/analytics/trends?days=30');
            console.log('Analytics data response:', res.data);
            setAnalyticsData(res.data);
        } catch (err) {
            console.error('Error fetching analytics data:', err);
            if (err.response) {
                console.error('Response status:', err.response.status);
                console.error('Response data:', err.response.data);
            }
            toast.error('Failed to load analytics data');
            throw err;
        }
    };

    const fetchDashboardData = async () => {
        try {
            console.log('Fetching dashboard data...');
            const res = await authAxios.get('/dashboard-summary');
            console.log('Dashboard data response:', res.data);
            setDashboardData(res.data);
        } catch (err) {
            console.error('Error fetching dashboard data:', err);
            if (err.response) {
                console.error('Response status:', err.response.status);
                console.error('Response data:', err.response.data);
            }
            toast.error('Failed to load dashboard data');
            throw err;
        }
    };

    const fetchComparisonData = async () => {
        try {
            console.log('Fetching comparison data...');
            const res = await authAxios.get('/analytics/factory-comparison?days=30');
            console.log('Comparison data response:', res.data);
            setComparisonData(res.data);
        } catch (err) {
            console.error('Error fetching comparison data:', err);
            if (err.response) {
                console.error('Response status:', err.response.status);
                console.error('Response data:', err.response.data);
            }
            toast.error('Failed to load comparison data');
            throw err;
        }
    };

    const exportToExcel = async () => {
        try {
            toast.loading('Generating Excel report...');
            const res = await authAxios.get('/export-excel', { responseType: 'blob' });
            const blob = new Blob([res.data], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
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
        } catch (err) {
            console.error('Error exporting Excel:', err);
            toast.error('Failed to export Excel report');
        }
    };

    // Enhanced function to create factory-specific production vs sales chart
    const createFactoryProductionVsSalesChart = (factoryData, factoryName) => {
        console.log('Creating chart for factory:', factoryName);
        console.log('Factory Data:', factoryData);
        
        const chartData = {
            labels: factoryData?.dates || [],
            datasets: [
                {
                    label: 'Production',
                    data: factoryData?.production || [],
                    borderColor: '#1a355b',
                    backgroundColor: 'rgba(26,53,91,0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: false,
                    pointBackgroundColor: '#1a355b',
                    pointBorderColor: '#1a355b',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Sales',
                    data: factoryData?.sales || [],
                    borderColor: '#ffc72c',
                    backgroundColor: 'rgba(255,199,44,0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: false,
                    pointBackgroundColor: '#ffc72c',
                    pointBorderColor: '#ffc72c',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
            ],
        };
        
        console.log('Chart Data:', chartData);
        return chartData;
    };

    // Enhanced line chart options for daily trends
    const dailyTrendChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        size: 12,
                        weight: 'bold'
                    }
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                callbacks: {
                    label: function(context) {
                        const dataset = context.dataset;
                        const value = context.parsed.y;
                        return `${dataset.label}: ${value?.toLocaleString() || 0} units`;
                    }
                }
            }
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Date',
                    font: {
                        size: 12,
                        weight: 'bold'
                    }
                },
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            y: {
                display: true,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Units',
                    font: {
                        size: 12,
                        weight: 'bold'
                    }
                },
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
        },
        elements: {
            line: {
                borderWidth: 2
            },
            point: {
                radius: 4,
                hoverRadius: 6
            }
        }
    };

    const factoryProductionData = {
        labels: Object.values(comparisonData || {}).map((f) => f.name),
        datasets: [
            {
                label: 'Production',
                data: Object.values(comparisonData || {}).map((f) => f.production),
                backgroundColor: 'rgba(26,53,91,0.6)',
                skuUnit: Object.values(comparisonData || {}).map((f) => f.sku_unit || f.unit || 'units'),
            },
        ],
    };

    const factorySalesData = {
        labels: Object.values(comparisonData || {}).map((f) => f.name),
        datasets: [
            {
                label: 'Sales',
                data: Object.values(comparisonData || {}).map((f) => f.sales),
                backgroundColor: 'rgba(255,199,44,0.6)',
                skuUnit: Object.values(comparisonData || {}).map((f) => f.sku_unit || f.unit || 'units'),
            },
        ],
    };

    const factoryDowntimeData = {
        labels: Object.values(comparisonData || {}).map((f) => f.name),
        datasets: [
            {
                label: 'Downtime Hours',
                data: Object.values(comparisonData || {}).map((f) => f.downtime || 0),
                backgroundColor: 'rgba(239,68,68,0.6)',
                borderColor: 'rgb(239,68,68)',
                borderWidth: 1,
            },
        ],
    };

    const efficiencyData = {
        labels: Object.values(comparisonData || {}).map((f) => f.name),
        datasets: [
            {
                label: 'Efficiency %',
                data: Object.values(comparisonData || {}).map((f) => f.efficiency),
                backgroundColor: [
                    'rgba(26,53,91,0.6)',
                    'rgba(255,199,44,0.6)',
                    'rgba(34,197,94,0.6)',
                    'rgba(168,85,247,0.6)',
                ],
                borderColor: [
                    'rgb(26,53,91)',
                    'rgb(255,199,44)',
                    'rgb(34,197,94)',
                    'rgb(168,85,247)',
                ],
                borderWidth: 1,
            },
        ],
    };

    const barChartOptions = {
        responsive: true,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const dataset = context.dataset;
                        const value = context.parsed.y;
                        const skuUnit = dataset.skuUnit ? dataset.skuUnit[context.dataIndex] : 'units';
                        return `${dataset.label}: ${value.toLocaleString()} ${skuUnit}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    const downtimeBarChartOptions = {
        responsive: true,
        plugins: {
            legend: {
                display: false,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    const lineChartOptions = {
        responsive: true,
        plugins: {
            legend: {
                display: true,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    // Show loading state
    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading dashboard data...</p>
                </div>
            </div>
        );
    }

    // Show error state
    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <div className="flex items-center">
                    <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
                        <p className="text-sm text-red-700 mt-1">{error}</p>
                        <button 
                            onClick={fetchAllData}
                            className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 font-medium py-1 px-3 rounded text-sm"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Debug Information */}
            <div className="bg-gray-100 rounded-lg p-4 text-sm">
                <h4 className="font-medium mb-2">Debug Information:</h4>
                <div className="space-y-1">
                    <p>User Role: {user?.role}</p>
                    <p>User Factory ID: {user?.factory_id || 'N/A'}</p>
                    <p>Analytics Data Available: {Object.keys(analyticsData).length > 0 ? 'Yes' : 'No'}</p>
                    <p>Factories Data: {analyticsData?.factories ? Object.keys(analyticsData.factories).length : 0} factories</p>
                    <p>Comparison Data: {Object.keys(comparisonData).length} factories</p>
                </div>
            </div>

            {/* Summary Cards - Only Total Downtime */}
            <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm text-gray-500 mb-2">Total Downtime</h3>
                    <p className="text-3xl font-bold text-red-600">
                        {dashboardData?.total_downtime?.toLocaleString() || 0}h
                    </p>
                </div>
            </div>

            {/* Export Button */}
            <div className="flex justify-end">
                <button
                    onClick={exportToExcel}
                    className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md"
                >
                    Export Excel Report
                </button>
            </div>

            {/* Charts */}
            <div className="space-y-6">
                {/* Factory-specific Production vs Sales Daily Trend Charts */}
                {user?.role === 'headquarters' && analyticsData?.factories && Object.keys(analyticsData.factories).length > 0 && (
                    <div className="space-y-6">
                        <div className="bg-gray-50 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-800 mb-6">
                                Factory-wise Production vs Sales Daily Trends (Last 30 Days)
                            </h2>
                            <div className="grid grid-cols-1 gap-8">
                                {Object.entries(analyticsData.factories).map(([factoryId, factoryData]) => {
                                    console.log(`Rendering factory ${factoryId}:`, factoryData);
                                    return (
                                        <div key={`daily-trend-${factoryId}`} className="bg-white rounded-lg shadow-lg p-6">
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="text-lg font-semibold text-gray-800">
                                                    {factoryData.name || `Factory ${factoryId}`} - Daily Production vs Sales Trend
                                                </h3>
                                                <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                    <div className="flex items-center">
                                                        <div className="w-4 h-4 bg-blue-600 rounded-full mr-2"></div>
                                                        <span>Production</span>
                                                    </div>
                                                    <div className="flex items-center">
                                                        <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                                                        <span>Sales</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="h-80 w-full">
                                                <Line 
                                                    data={createFactoryProductionVsSalesChart(factoryData, factoryData.name || `Factory ${factoryId}`)} 
                                                    options={dailyTrendChartOptions} 
                                                />
                                            </div>
                                            {/* Debug info */}
                                            <div className="mt-4 text-xs text-gray-500">
                                                <p>Data points: {factoryData?.dates?.length || 0} days</p>
                                                <p>Production data: {factoryData?.production?.length || 0} points</p>
                                                <p>Sales data: {factoryData?.sales?.length || 0} points</p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* Fallback message if no factory data */}
                {user?.role === 'headquarters' && (!analyticsData?.factories || Object.keys(analyticsData.factories).length === 0) && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-yellow-800">No Factory Data Available</h3>
                                <p className="text-sm text-yellow-700 mt-1">
                                    No factory analytics data found. Check the debug information above and console logs for details.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Single factory view - show combined production and sales */}
                {user?.role !== 'headquarters' && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-4">Production & Sales Daily Trend (Last 30 Days)</h3>
                        <div className="h-80">
                            <Line 
                                data={{
                                    labels: analyticsData?.dates || [],
                                    datasets: [
                                        {
                                            label: 'Production',
                                            data: analyticsData?.production || [],
                                            borderColor: 'rgb(26,53,91)',
                                            backgroundColor: 'rgba(26,53,91,0.1)',
                                            tension: 0.1,
                                            fill: false,
                                            pointBackgroundColor: 'rgb(26,53,91)',
                                            pointBorderColor: 'rgb(26,53,91)',
                                            pointRadius: 4,
                                            pointHoverRadius: 6,
                                        },
                                        {
                                            label: 'Sales',
                                            data: analyticsData?.sales || [],
                                            borderColor: 'rgb(255,199,44)',
                                            backgroundColor: 'rgba(255,199,44,0.1)',
                                            tension: 0.1,
                                            fill: false,
                                            pointBackgroundColor: 'rgb(255,199,44)',
                                            pointBorderColor: 'rgb(255,199,44)',
                                            pointRadius: 4,
                                            pointHoverRadius: 6,
                                        },
                                    ],
                                }} 
                                options={dailyTrendChartOptions} 
                            />
                        </div>
                    </div>
                )}

                {/* Headquarters-only comparison charts */}
                {user?.role === 'headquarters' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-4">Factory Production Comparison</h3>
                            {Object.keys(comparisonData || {}).length > 0 ? (
                                <Bar data={factoryProductionData} options={barChartOptions} />
                            ) : (
                                <p>No comparison data available</p>
                            )}
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-4">Factory Sales Comparison</h3>
                            {Object.keys(comparisonData || {}).length > 0 ? (
                                <Bar data={factorySalesData} options={barChartOptions}/>
                            ) : (
                                <p>No comparison data available</p>
                            )}
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-4">Downtime Comparison</h3>
                            {Object.keys(comparisonData || {}).length > 0 ? (
                                <Bar data={factoryDowntimeData} options={downtimeBarChartOptions} />
                            ) : (
                                <p>No comparison data available</p>
                            )}
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-4">Factory Efficiency</h3>
                            {Object.keys(comparisonData || {}).length > 0 ? (
                                <Doughnut
                                    data={efficiencyData}
                                    options={{
                                        responsive: true,
                                        plugins: {
                                            legend: { position: 'bottom' },
                                        },
                                    }}
                                />
                            ) : (
                                <p>No comparison data available</p>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DashboardTab;