// src/components/DashboardTab.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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

    // Separate factory comparison charts
    const factoryProductionData = {
        labels: Object.values(comparisonData).map(factory => factory.name),
        datasets: [
            {
                label: 'Production',
                data: Object.values(comparisonData).map(factory => factory.production),
                backgroundColor: 'rgba(26, 53, 91, 0.6)',
                borderColor: 'rgb(26, 53, 91)',
                borderWidth: 1,
            },
        ],
    };

    const factorySalesData = {
        labels: Object.values(comparisonData).map(factory => factory.name),
        datasets: [
            {
                label: 'Sales',
                data: Object.values(comparisonData).map(factory => factory.sales),
                backgroundColor: 'rgba(255, 199, 44, 0.6)',
                borderColor: 'rgb(255, 199, 44)',
                borderWidth: 1,
            },
        ],
    };

    const factoryDowntimeData = {
        labels: Object.values(comparisonData).map(factory => factory.name),
        datasets: [
            {
                label: 'Downtime Hours',
                data: Object.values(comparisonData).map(factory => factory.downtime),
                backgroundColor: 'rgba(239, 68, 68, 0.6)',
                borderColor: 'rgb(239, 68, 68)',
                borderWidth: 1,
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
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2-2H5a2 2 0 01-2-2z" />
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

                {/* Factory Performance Comparison - Only for headquarters */}
                {user.role === 'headquarters' && (
                    <>
                        {/* Factory Production Comparison */}
                        <div className="bg-white rounded-lg shadow-md p-6">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">Factory Production Comparison</h3>
                            {Object.keys(comparisonData).length > 0 ? (
                                <Bar data={factoryProductionData} options={{
                                    responsive: true,
                                    scales: {
                                        y: {
                                            beginAtZero: true,
                                        },
                                    },
                                    plugins: {
                                        legend: {
                                            display: true,
                                        },
                                    },
                                }} />
                            ) : (
                                <div className="flex justify-center items-center h-64">
                                    <p className="text-gray-500">No data available</p>
                                </div>
                            )}
                        </div>

                        {/* Factory Sales Comparison */}
                        <div className="bg-white rounded-lg shadow-md p-6">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">Factory Sales Comparison</h3>
                            {Object.keys(comparisonData).length > 0 ? (
                                <Bar data={factorySalesData} options={{
                                    responsive: true,
                                    scales: {
                                        y: {
                                            beginAtZero: true,
                                        },
                                    },
                                    plugins: {
                                        legend: {
                                            display: true,
                                        },
                                    },
                                }} />
                            ) : (
                                <div className="flex justify-center items-center h-64">
                                    <p className="text-gray-500">No data available</p>
                                </div>
                            )}
                        </div>

                        {/* Factory Downtime Comparison */}
                        <div className="bg-white rounded-lg shadow-md p-6">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">Factory Downtime Comparison</h3>
                            {Object.keys(comparisonData).length > 0 ? (
                                <Bar data={factoryDowntimeData} options={{
                                    responsive: true,
                                    scales: {
                                        y: {
                                            beginAtZero: true,
                                        },
                                    },
                                    plugins: {
                                        legend: {
                                            display: true,
                                        },
                                    },
                                }} />
                            ) : (
                                <div className="flex justify-center items-center h-64">
                                    <p className="text-gray-500">No data available</p>
                                </div>
                            )}
                        </div>

                        {/* Factory Efficiency */}
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

export default DashboardTab;