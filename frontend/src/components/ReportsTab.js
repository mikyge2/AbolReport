// src/components/ReportsTab.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ReportsTab = () => {
    const [reportData, setReportData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({
        factory: '',
        startDate: '',
        endDate: ''
    });

    useEffect(() => {
        fetchReportData();
    }, []);

    const fetchReportData = async () => {
        try {
            const response = await axios.get(`${API}/daily-logs`);
            setReportData(response.data);
        } catch (error) {
            console.error('Failed to fetch report data:', error);
            toast.error('Failed to load report data');
        } finally {
            setLoading(false);
        }
    };

    const exportFilteredData = async () => {
        try {
            const params = new URLSearchParams();
            if (filter.factory) params.append('factory_id', filter.factory);
            if (filter.startDate) params.append('start_date', new Date(filter.startDate).toISOString());
            if (filter.endDate) params.append('end_date', new Date(filter.endDate).toISOString());

            toast.loading('Generating filtered Excel report...');
            const response = await axios.get(`${API}/export-excel?${params.toString()}`, {
                responseType: 'blob'
            });

            const blob = new Blob([response.data], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            });

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `factory_report_filtered_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            toast.success('Filtered Excel report downloaded successfully!');
        } catch (error) {
            console.error('Failed to export filtered data:', error);
            toast.error('Failed to export filtered report');
        }
    };

    const filteredData = reportData.filter(log => {
        let matches = true;

        if (filter.factory && log.factory_id !== filter.factory) {
            matches = false;
        }

        if (filter.startDate) {
            const logDate = new Date(log.date);
            const startDate = new Date(filter.startDate);
            if (logDate < startDate) matches = false;
        }

        if (filter.endDate) {
            const logDate = new Date(log.date);
            const endDate = new Date(filter.endDate);
            if (logDate > endDate) matches = false;
        }

        return matches;
    });

    const calculateTotals = (data) => {
        return data.reduce((acc, log) => {
            acc.production += Object.values(log.production_data || {}).reduce((sum, val) => sum + val, 0);
            acc.sales += Object.values(log.sales_data || {}).reduce((sum, item) => sum + (item.amount || 0), 0);
            acc.revenue += Object.values(log.sales_data || {}).reduce((sum, item) => sum + ((item.amount || 0) * (item.unit_price || 0)), 0);
            acc.downtime += log.downtime_hours || 0;
            return acc;
        }, { production: 0, sales: 0, revenue: 0, downtime: 0 });
    };

    const totals = calculateTotals(filteredData);

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-primary mb-6">Reports & Analytics</h2>

                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Factory</label>
                        <select
                            value={filter.factory}
                            onChange={(e) => setFilter({ ...filter, factory: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            <option value="">All Factories</option>
                            {Object.entries(factories).map(([key, factory]) => (
                                <option key={key} value={key}>{factory.name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                        <input
                            type="date"
                            value={filter.startDate}
                            onChange={(e) => setFilter({ ...filter, startDate: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                        <input
                            type="date"
                            value={filter.endDate}
                            onChange={(e) => setFilter({ ...filter, endDate: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                    </div>

                    <div className="flex items-end">
                        <button
                            onClick={exportFilteredData}
                            className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                        >
                            Export Filtered Data
                        </button>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-blue-600 mb-1">Total Production</h3>
                        <p className="text-2xl font-bold text-blue-800">{totals.production.toLocaleString()}</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-green-600 mb-1">Total Sales</h3>
                        <p className="text-2xl font-bold text-green-800">{totals.sales.toLocaleString()}</p>
                    </div>
                    <div className="bg-yellow-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-yellow-600 mb-1">Total Revenue</h3>
                        <p className="text-2xl font-bold text-yellow-800">${totals.revenue.toLocaleString()}</p>
                    </div>
                    <div className="bg-red-50 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-red-600 mb-1">Total Downtime</h3>
                        <p className="text-2xl font-bold text-red-800">{totals.downtime.toLocaleString()}h</p>
                    </div>
                </div>

                {/* Data Table */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Factory</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Production</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sales</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Downtime</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created By</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan="7" className="px-6 py-4 text-center">
                                        <div className="flex justify-center">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                        </div>
                                    </td>
                                </tr>
                            ) : filteredData.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                                        No data found for the selected filters
                                    </td>
                                </tr>
                            ) : (
                                filteredData.map((log, index) => {
                                    const production = Object.values(log.production_data || {}).reduce((sum, val) => sum + val, 0);
                                    const sales = Object.values(log.sales_data || {}).reduce((sum, item) => sum + (item.amount || 0), 0);
                                    const revenue = Object.values(log.sales_data || {}).reduce((sum, item) => sum + ((item.amount || 0) * (item.unit_price || 0)), 0);

                                    return (
                                        <tr key={index} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {new Date(log.date).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {factories[log.factory_id]?.name || log.factory_id}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {production.toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {sales.toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                ${revenue.toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {log.downtime_hours}h
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {log.created_by}
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default ReportsTab;
