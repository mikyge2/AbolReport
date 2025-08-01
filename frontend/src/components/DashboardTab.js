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
import DataDetailModal from './DataDetailModal';

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
    const { user } = useContext(AuthContext);
    const token = localStorage.getItem('token');
    const [analyticsData, setAnalyticsData] = useState({});
    const [comparisonData, setComparisonData] = useState({});
    const [dashboardData, setDashboardData] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Modal state for interactive popups
    const [modalData, setModalData] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalType, setModalType] = useState('dailyLog');

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
            console.log('Analytics factories:', res.data.factories);
            console.log('Analytics factories keys:', Object.keys(res.data.factories || {}));
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
            const res = await authAxios.get('/analytics/factory-comparison');
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

    // Modal handlers
    const handleChartClick = async (event, elements, chart) => {
        if (elements.length > 0) {
            const element = elements[0];
            const datasetIndex = element.datasetIndex;
            const index = element.index;
            
            // Get the clicked data point information
            const factoryId = chart.canvas.getAttribute('data-factory-id');
            const date = chart.data.labels[index];
            
            try {
                // Fetch the specific daily log for this factory and date
                const response = await authAxios.get(`/daily-logs`, {
                    params: {
                        factory_id: factoryId,
                        start_date: date,
                        end_date: date
                    }
                });
                
                if (response.data && response.data.length > 0) {
                    const dailyLog = response.data[0];
                    // Add factory name for better display
                    dailyLog.factory_name = analyticsData.factories?.[factoryId]?.name || factoryId;
                    
                    setModalData(dailyLog);
                    setModalType('dailyLog');
                    setIsModalOpen(true);
                }
            } catch (error) {
                console.error('Error fetching daily log details:', error);
                toast.error('Failed to fetch detailed data');
            }
        }
    };
    
    const handleModalClose = () => {
        setIsModalOpen(false);
        setModalData(null);
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
                    borderWidth: 3,
                    tension: 0.1,
                    fill: false,
                    pointBackgroundColor: '#1a355b',
                    pointBorderColor: '#1a355b',
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
                {
                    label: 'Sales',
                    data: factoryData?.sales || [],
                    borderColor: '#ffc72c',
                    backgroundColor: 'rgba(255,199,44,0.1)',
                    borderWidth: 3,
                    tension: 0.1,
                    fill: false,
                    pointBackgroundColor: '#ffc72c',
                    pointBorderColor: '#ffc72c',
                    pointRadius: 5,
                    pointHoverRadius: 7,
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
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        size: 14,
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
                padding: 10,
                callbacks: {
                    label: function (context) {
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
                        size: 14,
                        weight: 'bold'
                    }
                },
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    font: {
                        size: 12
                    }
                }
            },
            y: {
                display: true,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Units',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                },
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    font: {
                        size: 12
                    }
                }
            },
        },
        elements: {
            line: {
                borderWidth: 3
            },
            point: {
                radius: 5,
                hoverRadius: 7
            }
        },
        onClick: handleChartClick
    };
    
    // Create chart options with factory-specific click handler
    const createChartOptionsWithFactory = (factoryId) => ({
        ...dailyTrendChartOptions,
        onClick: (event, elements, chart) => {
            if (elements.length > 0) {
                const element = elements[0];
                const index = element.index;
                const date = chart.data.labels[index];
                
                handleChartPointClick(factoryId, date);
            }
        }
    });
    
    const handleChartPointClick = async (factoryId, date) => {
        try {
            // Fetch the specific daily log for this factory and date
            const response = await authAxios.get(`/daily-logs`, {
                params: {
                    factory_id: factoryId,
                    start_date: date,
                    end_date: date
                }
            });
            
            if (response.data && response.data.length > 0) {
                const dailyLog = response.data[0];
                // Add factory name for better display
                dailyLog.factory_name = analyticsData.factories?.[factoryId]?.name || factoryId;
                
                setModalData(dailyLog);
                setModalType('dailyLog');
                setIsModalOpen(true);
            } else {
                toast.error('No detailed data found for this data point');
            }
        } catch (error) {
            console.error('Error fetching daily log details:', error);
            toast.error('Failed to fetch detailed data');
        }
    };

    // Helper function to categorize Mintu Plast products
    const categorizeMintuPlastProducts = (products) => {
        const preformProducts = [];
        const capProducts = [];
        
        products.forEach(product => {
            if (product.toLowerCase().includes('preform')) {
                preformProducts.push(product);
            } else if (product.toLowerCase().includes('cap')) {
                capProducts.push(product);
            }
        });
        
        return { preformProducts, capProducts };
    };

    // Helper function to create separate data for Preform and Cap products
    const createMintuPlastSeparateData = (factoryData, productType) => {
        if (!factoryData || !factoryData.production_by_product || !factoryData.sales_by_product) {
            return {
                dates: factoryData?.dates || [],
                production: new Array(factoryData?.dates?.length || 0).fill(0),
                sales: new Array(factoryData?.dates?.length || 0).fill(0)
            };
        }

        const { preformProducts, capProducts } = categorizeMintuPlastProducts(
            Object.keys(factoryData.production_by_product)
        );
        
        const relevantProducts = productType === 'preform' ? preformProducts : capProducts;
        
        const dates = factoryData.dates || [];
        const productionData = [];
        const salesData = [];
        
        // Aggregate data for the relevant product category
        dates.forEach((date, index) => {
            let totalProduction = 0;
            let totalSales = 0;
            
            relevantProducts.forEach(product => {
                if (factoryData.production_by_product[product] && factoryData.production_by_product[product][index] !== undefined) {
                    totalProduction += factoryData.production_by_product[product][index];
                }
                if (factoryData.sales_by_product[product] && factoryData.sales_by_product[product][index] !== undefined) {
                    totalSales += factoryData.sales_by_product[product][index];
                }
            });
            
            productionData.push(totalProduction);
            salesData.push(totalSales);
        });
        
        return {
            dates,
            production: productionData,
            sales: salesData,
            name: `Mintu Plast - ${productType.charAt(0).toUpperCase() + productType.slice(1)} Products`
        };
    };

    // Function to get factories data to display based on user role
    const getFactoriesDataToDisplay = () => {
        if (user?.role === 'headquarters') {
            // Headquarters can see all factories
            return analyticsData?.factories || {};
        } else {
            // Factory user can only see their own factory
            if (user?.factory_id && analyticsData?.factories) {
                const userFactory = analyticsData.factories[user.factory_id];
                if (userFactory) {
                    return { [user.factory_id]: userFactory };
                }
            }
            // If user has single factory data format (non-headquarters response)
            if (analyticsData?.dates && analyticsData?.production && analyticsData?.sales) {
                return {
                    [user?.factory_id || 'current']: {
                        name: user?.factory_name || 'Current Factory',
                        dates: analyticsData.dates,
                        production: analyticsData.production,
                        sales: analyticsData.sales
                    }
                };
            }
            return {};
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
                    label: function (context) {
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

    // Show loading state
    if (loading) {
        return (
            <div className="loading-futuristic">
                <div className="loading-spinner-futuristic"></div>
                <p className="text-futuristic-secondary">Loading dashboard data...</p>
            </div>
        );
    }

    // Show error state
    if (error) {
        return (
            <div className="glass-card p-6 border-red-500/30">
                <div className="flex items-center">
                    <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-300">Error Loading Dashboard</h3>
                        <p className="text-sm text-futuristic-muted mt-1">{error}</p>
                        <button
                            onClick={fetchAllData}
                            className="mt-2 btn-futuristic py-1 px-3 text-sm"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Get the factories data to display based on user role
    const factoriesToDisplay = getFactoriesDataToDisplay();

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="glass-card p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-futuristic-primary">Factory Dashboard</h1>
                        <p className="text-futuristic-secondary mt-1">
                            {user?.role === 'headquarters' 
                                ? 'Overview of all factory operations' 
                                : 'Your factory performance overview'
                            }
                        </p>
                    </div>
                    <div className="flex items-center space-x-3">
                        <span className="text-sm text-futuristic-muted">
                            Role: <span className="font-medium text-[#ffc72c]">{user?.role}</span>
                        </span>
                        {user?.factory_id && (
                            <span className="text-sm text-futuristic-muted">
                                Factory: <span className="font-medium text-[#ffc72c]">{user.factory_id}</span>
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="stat-card-futuristic">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-br from-red-500/20 to-red-600/20 rounded-xl flex items-center justify-center backdrop-blur-sm border border-red-500/20">
                                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-futuristic-muted">Total Downtime</p>
                            <p className="text-2xl font-bold text-red-400">
                                {dashboardData?.total_downtime?.toFixed(2) || '0.00'}h
                            </p>
                        </div>
                    </div>
                </div>
                
                <div className="stat-card-futuristic">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-xl flex items-center justify-center backdrop-blur-sm border border-blue-500/20">
                                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-futuristic-muted">Active Factories</p>
                            <p className="text-2xl font-bold text-blue-400">
                                {Object.keys(factoriesToDisplay).length}
                            </p>
                        </div>
                    </div>
                </div>
                
                <div className="stat-card-futuristic">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-br from-green-500/20 to-green-600/20 rounded-xl flex items-center justify-center backdrop-blur-sm border border-green-500/20">
                                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                                </svg>
                            </div>
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-futuristic-muted">Total Stock</p>
                            <p className="text-2xl font-bold text-green-400">
                                {dashboardData?.total_stock?.toLocaleString() || 0}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Export Button */}
            <div className="flex justify-end">
                <button
                    onClick={exportToExcel}
                    className="btn-futuristic flex items-center space-x-2"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>Export Excel Report</span>
                </button>
            </div>

            {/* Headquarters-only comparison charts - MOVED TO TOP */}
            {user?.role === 'headquarters' && Object.keys(comparisonData || {}).length > 0 && (
                <div className="space-y-6">
                    <div className="chart-container-futuristic">
                        <h2 className="text-xl font-bold text-futuristic-primary mb-6">
                            Factory Comparison Analytics - Today ({new Date().toLocaleDateString()})
                        </h2>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="glass-card-light p-6">
                                <h3 className="text-lg font-semibold mb-4 text-gray-800">Production Comparison</h3>
                                <Bar data={factoryProductionData} options={barChartOptions} />
                            </div>
                            <div className="glass-card-light p-6">
                                <h3 className="text-lg font-semibold mb-4 text-gray-800">Sales Comparison</h3>
                                <Bar data={factorySalesData} options={barChartOptions} />
                            </div>
                            <div className="glass-card-light p-6">
                                <h3 className="text-lg font-semibold mb-4 text-gray-800">Downtime Comparison</h3>
                                <Bar data={factoryDowntimeData} options={downtimeBarChartOptions} />
                            </div>
                            <div className="glass-card-light p-6">
                                <h3 className="text-lg font-semibold mb-4 text-gray-800">Factory Efficiency</h3>
                                <Doughnut
                                    data={efficiencyData}
                                    options={{
                                        responsive: true,
                                        plugins: {
                                            legend: { position: 'bottom' },
                                        },
                                    }}
                                />
                                {/* Factory Efficiency Explanation */}
                                <div className="mt-4 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                                    <p className="text-sm text-gray-700">
                                        <strong>Factory Efficiency:</strong> Calculated as the ratio of productive time to total available time. 
                                        Higher efficiency indicates better utilization of resources and minimal downtime. 
                                        Formula: ((Total Hours - Downtime Hours) / Total Hours) × 100%
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Production vs Sales Charts - Separate chart for each factory */}
            <div className="space-y-6">
                <div className="chart-container-futuristic">
                    <h2 className="text-xl font-bold text-futuristic-primary mb-6">
                        📊 {user?.role === 'headquarters' ? 'All Factories Overview' : 'Factory Performance'} - Production vs Sales Trends (30-Day Period)
                    </h2>
                    
                    {Object.keys(factoriesToDisplay).length > 0 ? (
                        <div className="grid grid-cols-1 gap-8">
                            {/* Show graphs for specific factories based on role */}
                            {user?.role === 'headquarters' ? (
                                // For headquarters - show all 4 factories
                                Object.entries(factoriesToDisplay).map(([factoryId, factoryData]) => {
                                    console.log(`Rendering factory ${factoryId}:`, factoryData);
                                    
                                    // Special handling for Mintu Plast - create separate charts for Preform and Cap
                                    if (factoryId === 'mintu_plast') {
                                        const preformData = createMintuPlastSeparateData(factoryData, 'preform');
                                        const capData = createMintuPlastSeparateData(factoryData, 'cap');
                                        
                                        return (
                                            <div key={`daily-trend-${factoryId}`} className="space-y-6">
                                                {/* Preform Chart */}
                                                <div className="glass-card-light p-6">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <h3 className="text-lg font-semibold text-gray-800">
                                                            🏭 Mintu Plast - Preform Products Performance
                                                        </h3>
                                                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-[#1a355b] rounded-full mr-2"></div>
                                                                <span>Production</span>
                                                            </div>
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-[#ffc72c] rounded-full mr-2"></div>
                                                                <span>Sales</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="h-96 w-full">
                                                        <Line
                                                            data={createFactoryProductionVsSalesChart(preformData, preformData.name)}
                                                            options={createChartOptionsWithFactory('mintu_plast')}
                                                        />
                                                    </div>
                                                    
                                                    {/* Preform Summary Stats */}
                                                    <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Production</p>
                                                            <p className="text-lg font-semibold text-[#1a355b]">
                                                                {preformData?.production?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Sales</p>
                                                            <p className="text-lg font-semibold text-[#ffc72c]">
                                                                {preformData?.sales?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Production</p>
                                                            <p className="text-lg font-semibold text-[#1a355b]">
                                                                {preformData?.production?.length > 0 
                                                                    ? Math.round(preformData.production.reduce((a, b) => a + b, 0) / preformData.production.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Sales</p>
                                                            <p className="text-lg font-semibold text-[#ffc72c]">
                                                                {preformData?.sales?.length > 0 
                                                                    ? Math.round(preformData.sales.reduce((a, b) => a + b, 0) / preformData.sales.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                {/* Cap Chart */}
                                                <div className="glass-card-light p-6">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <h3 className="text-lg font-semibold text-gray-800">
                                                            🧴 Mintu Plast - Cap Products Performance
                                                        </h3>
                                                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-[#1a355b] rounded-full mr-2"></div>
                                                                <span>Production</span>
                                                            </div>
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-[#ffc72c] rounded-full mr-2"></div>
                                                                <span>Sales</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="h-96 w-full">
                                                        <Line
                                                            data={createFactoryProductionVsSalesChart(capData, capData.name)}
                                                            options={createChartOptionsWithFactory('mintu_plast')}
                                                        />
                                                    </div>
                                                    
                                                    {/* Cap Summary Stats */}
                                                    <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Production</p>
                                                            <p className="text-lg font-semibold text-[#1a355b]">
                                                                {capData?.production?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Sales</p>
                                                            <p className="text-lg font-semibold text-[#ffc72c]">
                                                                {capData?.sales?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Production</p>
                                                            <p className="text-lg font-semibold text-[#1a355b]">
                                                                {capData?.production?.length > 0 
                                                                    ? Math.round(capData.production.reduce((a, b) => a + b, 0) / capData.production.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Sales</p>
                                                            <p className="text-lg font-semibold text-[#ffc72c]">
                                                                {capData?.sales?.length > 0 
                                                                    ? Math.round(capData.sales.reduce((a, b) => a + b, 0) / capData.sales.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    } else {
                                        // Regular chart for other factories
                                        return (
                                            <div key={`daily-trend-${factoryId}`} className="glass-card-light p-6">
                                                <div className="flex items-center justify-between mb-4">
                                                    <h3 className="text-lg font-semibold text-gray-800">
                                                        {factoryData.name || `Factory ${factoryId}`}
                                                    </h3>
                                                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                        <div className="flex items-center">
                                                            <div className="w-4 h-4 bg-[#1a355b] rounded-full mr-2"></div>
                                                            <span>Production</span>
                                                        </div>
                                                        <div className="flex items-center">
                                                            <div className="w-4 h-4 bg-[#ffc72c] rounded-full mr-2"></div>
                                                            <span>Sales</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="h-96 w-full">
                                                    <Line
                                                        data={createFactoryProductionVsSalesChart(factoryData, factoryData.name || `Factory ${factoryId}`)}
                                                        options={createChartOptionsWithFactory(factoryId)}
                                                    />
                                                </div>
                                                
                                                {/* Factory Summary Stats */}
                                                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Total Production</p>
                                                        <p className="text-lg font-semibold text-[#1a355b]">
                                                            {factoryData?.production?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                        </p>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Total Sales</p>
                                                        <p className="text-lg font-semibold text-[#ffc72c]">
                                                            {factoryData?.sales?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                        </p>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Avg Daily Production</p>
                                                        <p className="text-lg font-semibold text-[#1a355b]">
                                                            {factoryData?.production?.length > 0 
                                                                ? Math.round(factoryData.production.reduce((a, b) => a + b, 0) / factoryData.production.length).toLocaleString()
                                                                : 0}
                                                        </p>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Avg Daily Sales</p>
                                                        <p className="text-lg font-semibold text-[#ffc72c]">
                                                            {factoryData?.sales?.length > 0 
                                                                ? Math.round(factoryData.sales.reduce((a, b) => a + b, 0) / factoryData.sales.length).toLocaleString()
                                                                : 0}
                                                        </p>
                                                    </div>
                                                </div>
                                                
                                                {/* Debug info (can be removed in production) */}
                                                <div className="mt-4 text-xs text-gray-400">
                                                    <p>Data points: {factoryData?.dates?.length || 0} days</p>
                                                    <p>Production data: {factoryData?.production?.length || 0} points</p>
                                                    <p>Sales data: {factoryData?.sales?.length || 0} points</p>
                                                </div>
                                            </div>
                                        );
                                    }
                                })
                            ) : (
                                // For factory users - show only their factory
                                Object.entries(factoriesToDisplay).map(([factoryId, factoryData]) => {
                                    console.log(`Rendering factory ${factoryId}:`, factoryData);
                                    
                                    // Special handling for Mintu Plast - create separate charts for Preform and Cap
                                    if (factoryId === 'mintu_plast') {
                                        const preformData = createMintuPlastSeparateData(factoryData, 'preform');
                                        const capData = createMintuPlastSeparateData(factoryData, 'cap');
                                        
                                        return (
                                            <div key={`daily-trend-${factoryId}`} className="space-y-6">
                                                {/* Preform Chart */}
                                                <div className="bg-white rounded-lg shadow-lg p-6">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <h3 className="text-lg font-semibold text-gray-800">
                                                            {preformData.name}
                                                        </h3>
                                                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-blue-900 rounded-full mr-2"></div>
                                                                <span>Production</span>
                                                            </div>
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                                                                <span>Sales</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="h-96 w-full">
                                                        <Line
                                                            data={createFactoryProductionVsSalesChart(preformData, preformData.name)}
                                                            options={createChartOptionsWithFactory('mintu_plast')}
                                                        />
                                                    </div>
                                                    
                                                    {/* Preform Summary Stats */}
                                                    <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Production</p>
                                                            <p className="text-lg font-semibold text-blue-900">
                                                                {preformData?.production?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Sales</p>
                                                            <p className="text-lg font-semibold text-yellow-600">
                                                                {preformData?.sales?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Production</p>
                                                            <p className="text-lg font-semibold text-blue-700">
                                                                {preformData?.production?.length > 0 
                                                                    ? Math.round(preformData.production.reduce((a, b) => a + b, 0) / preformData.production.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Sales</p>
                                                            <p className="text-lg font-semibold text-yellow-700">
                                                                {preformData?.sales?.length > 0 
                                                                    ? Math.round(preformData.sales.reduce((a, b) => a + b, 0) / preformData.sales.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                {/* Cap Chart */}
                                                <div className="bg-white rounded-lg shadow-lg p-6">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <h3 className="text-lg font-semibold text-gray-800">
                                                            {capData.name}
                                                        </h3>
                                                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-blue-900 rounded-full mr-2"></div>
                                                                <span>Production</span>
                                                            </div>
                                                            <div className="flex items-center">
                                                                <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                                                                <span>Sales</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="h-96 w-full">
                                                        <Line
                                                            data={createFactoryProductionVsSalesChart(capData, capData.name)}
                                                            options={createChartOptionsWithFactory('mintu_plast')}
                                                        />
                                                    </div>
                                                    
                                                    {/* Cap Summary Stats */}
                                                    <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Production</p>
                                                            <p className="text-lg font-semibold text-blue-900">
                                                                {capData?.production?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Total Sales</p>
                                                            <p className="text-lg font-semibold text-yellow-600">
                                                                {capData?.sales?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Production</p>
                                                            <p className="text-lg font-semibold text-blue-700">
                                                                {capData?.production?.length > 0 
                                                                    ? Math.round(capData.production.reduce((a, b) => a + b, 0) / capData.production.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-sm text-gray-500">Avg Daily Sales</p>
                                                            <p className="text-lg font-semibold text-yellow-700">
                                                                {capData?.sales?.length > 0 
                                                                    ? Math.round(capData.sales.reduce((a, b) => a + b, 0) / capData.sales.length).toLocaleString()
                                                                    : 0}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    } else {
                                        // Regular chart for other factories
                                        return (
                                            <div key={`daily-trend-${factoryId}`} className="bg-white rounded-lg shadow-lg p-6">
                                                <div className="flex items-center justify-between mb-4">
                                                    <h3 className="text-lg font-semibold text-gray-800">
                                                        {factoryData.name || `Factory ${factoryId}`}
                                                    </h3>
                                                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                        <div className="flex items-center">
                                                            <div className="w-4 h-4 bg-blue-900 rounded-full mr-2"></div>
                                                            <span>Production</span>
                                                        </div>
                                                        <div className="flex items-center">
                                                            <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                                                            <span>Sales</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="h-96 w-full">
                                                    <Line
                                                        data={createFactoryProductionVsSalesChart(factoryData, factoryData.name || `Factory ${factoryId}`)}
                                                        options={createChartOptionsWithFactory(factoryId)}
                                                    />
                                                </div>
                                                
                                                {/* Factory Summary Stats */}
                                                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Total Production</p>
                                                        <p className="text-lg font-semibold text-blue-900">
                                                            {factoryData?.production?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                        </p>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Total Sales</p>
                                                        <p className="text-lg font-semibold text-yellow-600">
                                                            {factoryData?.sales?.reduce((a, b) => a + b, 0)?.toLocaleString() || 0}
                                                        </p>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Avg Daily Production</p>
                                                        <p className="text-lg font-semibold text-blue-700">
                                                            {factoryData?.production?.length > 0 
                                                                ? Math.round(factoryData.production.reduce((a, b) => a + b, 0) / factoryData.production.length).toLocaleString()
                                                                : 0}
                                                        </p>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm text-gray-500">Avg Daily Sales</p>
                                                        <p className="text-lg font-semibold text-yellow-700">
                                                            {factoryData?.sales?.length > 0 
                                                                ? Math.round(factoryData.sales.reduce((a, b) => a + b, 0) / factoryData.sales.length).toLocaleString()
                                                                : 0}
                                                        </p>
                                                    </div>
                                                </div>
                                                
                                                {/* Debug info (can be removed in production) */}
                                                <div className="mt-4 text-xs text-gray-500">
                                                    <p>Data points: {factoryData?.dates?.length || 0} days</p>
                                                    <p>Production data: {factoryData?.production?.length || 0} points</p>
                                                    <p>Sales data: {factoryData?.sales?.length || 0} points</p>
                                                </div>
                                            </div>
                                        );
                                    }
                                })
                            )}
                        </div>
                    ) : (
                        <div className="glass-card border-yellow-500/30 p-6">
                            <div className="flex items-center">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-yellow-300">No Data Available</h3>
                                    <p className="text-sm text-futuristic-muted mt-1">
                                        No production or sales data found for the last 30 days. Please check if daily logs have been created.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            
            {/* Interactive Data Detail Modal */}
            <DataDetailModal
                isOpen={isModalOpen}
                onClose={handleModalClose}
                data={modalData}
                type={modalType}
            />
        </div>
    );
};

export default DashboardTab;