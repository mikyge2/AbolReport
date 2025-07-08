// src/components/DashboardTab.js
import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DashboardTab = () => {
    const { user } = useContext(AuthContext);
    const [analyticsData, setAnalyticsData] = useState({});
    const [comparisonData, setComparisonData] = useState({});
    const [dashboardData, setDashboardData] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnalyticsData();
        fetchDashboardData();
        if (user?.role === 'headquarters') {
            fetchComparisonData();
        }
    }, []);

    const fetchAnalyticsData = async () => {
        try {
            const res = await axios.get(`${API}/analytics/trends?days=30`);
            setAnalyticsData(res.data);
        } catch (err) {
            toast.error('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    const fetchDashboardData = async () => {
        try {
            const res = await axios.get(`${API}/dashboard-summary`);
            setDashboardData(res.data);
        } catch (err) {
            toast.error('Failed to load dashboard data');
        }
    };

    const fetchComparisonData = async () => {
        try {
            const res = await axios.get(`${API}/analytics/factory-comparison?days=30`);
            setComparisonData(res.data);
        } catch (err) {
            toast.error('Failed to load comparison data');
        }
    };

    const exportToExcel = async () => {
        try {
            toast.loading('Generating Excel report...');
            const res = await axios.get(`${API}/export-excel`, { responseType: 'blob' });
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
            toast.error('Failed to export Excel report');
        }
    };

    // Create separate production chart data for each factory
    const createFactoryProductionChartData = (factoryData, factoryName) => {
        return {
            labels: factoryData?.dates || [],
            datasets: [
                {
                    label: 'Production',
                    data: factoryData?.production || [],
                    borderColor: 'rgb(26,53,91)',
                    backgroundColor: 'rgba(26,53,91,0.1)',
                    tension: 0.1,
                },
            ],
        };
    };

    // Create separate sales chart data for each factory
    const createFactorySalesChartData = (factoryData, factoryName) => {
        return {
            labels: factoryData?.dates || [],
            datasets: [
                {
                    label: 'Sales',
                    data: factoryData?.sales || [],
                    borderColor: 'rgb(255,199,44)',
                    backgroundColor: 'rgba(255,199,44,0.1)',
                    tension: 0.1,
                },
            ],
        };
    };

    const factoryProductionData = {
        labels: Object.values(comparisonData || {}).map((f) => f.name),
        datasets: [
            {
                label: 'Production',
                data: Object.values(comparisonData || {}).map((f) => f.production),
                backgroundColor: 'rgba(26,53,91,0.6)',
                // Add SKU/unit data for tooltips
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
                // Add SKU/unit data for tooltips
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

    return (
        <div className="space-y-8">
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
                {/* Factory-specific Production and Sales Charts */}
                {user?.role === 'headquarters' && analyticsData?.factories && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {Object.entries(analyticsData.factories).map(([factoryId, factoryData]) => (
                            <React.Fragment key={factoryId}>
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold mb-4">
                                        {factoryData.name} - Production Trend (30 Days)
                                    </h3>
                                    {loading ? (
                                        <p>Loading...</p>
                                    ) : (
                                        <Line 
                                            data={createFactoryProductionChartData(factoryData, factoryData.name)} 
                                            options={lineChartOptions} 
                                        />
                                    )}
                                </div>
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold mb-4">
                                        {factoryData.name} - Sales Trend (30 Days)
                                    </h3>
                                    {loading ? (
                                        <p>Loading...</p>
                                    ) : (
                                        <Line 
                                            data={createFactorySalesChartData(factoryData, factoryData.name)} 
                                            options={lineChartOptions} 
                                        />
                                    )}
                                </div>
                            </React.Fragment>
                        ))}
                    </div>
                )}

                {/* Factory-specific Production vs Sales Combined Charts */}
                {user?.role === 'headquarters' && analyticsData?.factories && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {Object.entries(analyticsData.factories).map(([factoryId, factoryData]) => (
                            <div key={`combined-${factoryId}`} className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold mb-4">
                                    {factoryData.name} - Production vs Sales Trend (30 Days)
                                </h3>
                                {loading ? (
                                    <p>Loading...</p>
                                ) : (
                                    <Line 
                                        data={{
                                            labels: factoryData?.dates || [],
                                            datasets: [
                                                {
                                                    label: 'Production',
                                                    data: factoryData?.production || [],
                                                    borderColor: 'rgb(26,53,91)',
                                                    backgroundColor: 'rgba(26,53,91,0.1)',
                                                    tension: 0.1,
                                                },
                                                {
                                                    label: 'Sales',
                                                    data: factoryData?.sales || [],
                                                    borderColor: 'rgb(255,199,44)',
                                                    backgroundColor: 'rgba(255,199,44,0.1)',
                                                    tension: 0.1,
                                                },
                                            ],
                                        }} 
                                        options={lineChartOptions} 
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Single factory view - show combined production and sales */}
                {user?.role !== 'headquarters' && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-4">Production & Sales Trend (30 Days)</h3>
                        {loading ? (
                            <p>Loading...</p>
                        ) : (
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
                                        },
                                        {
                                            label: 'Sales',
                                            data: analyticsData?.sales || [],
                                            borderColor: 'rgb(255,199,44)',
                                            backgroundColor: 'rgba(255,199,44,0.1)',
                                            tension: 0.1,
                                        },
                                    ],
                                }} 
                                options={lineChartOptions} 
                            />
                        )}
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
                                <p>No data available</p>
                            )}
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-4">Factory Sales Comparison</h3>
                            {Object.keys(comparisonData || {}).length > 0 ? (
                                <Bar data={factorySalesData} options={barChartOptions}/>
                            ) : (
                                <p>No data available</p>
                            )}
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-4">Downtime Comparison</h3>
                            {Object.keys(comparisonData || {}).length > 0 ? (
                                <Bar data={factoryDowntimeData} options={downtimeBarChartOptions} />
                            ) : (
                                <p>No data available</p>
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
                                <p>No data available</p>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DashboardTab;