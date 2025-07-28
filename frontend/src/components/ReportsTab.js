// src/components/ReportsTab.js
import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ReportsTab = () => {
    const { user } = useContext(AuthContext);
    const [factories, setFactories] = useState({});
    const [reportData, setReportData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({
        factory: '',
        startDate: '',
        endDate: '',
    });

    useEffect(() => {
        fetchFactories();
        fetchReportData();
    }, []);

    const fetchFactories = async () => {
        try {
            const res = await axios.get(`${API}/factories`);
            setFactories(res.data);
        } catch (err) {
            toast.error('Failed to load factories');
        }
    };

    const fetchReportData = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${API}/daily-logs`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            setReportData(res.data);
        } catch (err) {
            console.error('Error fetching report data:', err);
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
            const res = await axios.get(`${API}/export-excel?${params.toString()}`, { responseType: 'blob' });
            const blob = new Blob([res.data], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `factory_report_filtered_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            toast.success('Filtered Excel report downloaded!');
        } catch (err) {
            toast.error('Failed to export filtered report');
        }
    };

    const filteredData = reportData.filter((log) => {
        let matches = true;
        if (filter.factory && log.factory_id !== filter.factory) matches = false;
        if (filter.startDate) {
            const logDate = new Date(log.date);
            const start = new Date(filter.startDate);
            if (logDate < start) matches = false;
        }
        if (filter.endDate) {
            const logDate = new Date(log.date);
            const end = new Date(filter.endDate);
            if (logDate > end) matches = false;
        }
        return matches;
    });

    const totals = filteredData.reduce(
        (acc, log) => {
            acc.production += Object.values(log.production_data || {}).reduce((s, v) => s + v, 0);
            acc.sales += Object.values(log.sales_data || {}).reduce((s, v) => s + (v?.amount || 0), 0);
            acc.revenue += Object.values(log.sales_data || {}).reduce((s, v) => s + (v?.amount || 0) * (v?.unit_price || 0), 0);
            acc.downtime += log.downtime_hours || 0;
            return acc;
        },
        { production: 0, sales: 0, revenue: 0, downtime: 0 }
    );

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
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        >
                            <option value="">All Factories</option>
                            {Object.entries(factories || {}).map(([key, factory]) => (
                                <option key={key} value={key}>
                                    {factory.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                        <input
                            type="date"
                            value={filter.startDate}
                            onChange={(e) => setFilter({ ...filter, startDate: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                        <input
                            type="date"
                            value={filter.endDate}
                            onChange={(e) => setFilter({ ...filter, endDate: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                    </div>
                    <div className="flex items-end">
                        <button
                            onClick={exportFilteredData}
                            className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md"
                        >
                            Export Filtered Data
                        </button>
                    </div>
                </div>

                {/* Summary Cards - Only Total Revenue and Total Downtime */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-yellow-50 rounded p-4">
                        <h3 className="text-sm font-medium text-yellow-600 mb-1">Total Revenue</h3>
                        <p className="text-2xl font-bold text-yellow-800">${totals.revenue.toLocaleString()}</p>
                    </div>
                    <div className="bg-red-50 rounded p-4">
                        <h3 className="text-sm font-medium text-red-600 mb-1">Total Downtime</h3>
                        <p className="text-2xl font-bold text-red-800">{totals.downtime}h</p>
                    </div>
                </div>

                {/* Data Table */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Factory</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Production</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sales</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Revenue</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Downtime</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created By</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan="7" className="text-center p-6">
                                        <div className="animate-spin h-8 w-8 border-b-2 border-primary mx-auto" />
                                    </td>
                                </tr>
                            ) : filteredData.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="text-center p-6 text-gray-500">
                                        No data found for selected filters.
                                    </td>
                                </tr>
                            ) : (
                                filteredData.map((log, i) => {
                                    const production = Object.values(log.production_data || {}).reduce((s, v) => s + v, 0);
                                    const sales = Object.values(log.sales_data || {}).reduce((s, v) => s + (v?.amount || 0), 0);
                                    const revenue = Object.values(log.sales_data || {}).reduce((s, v) => s + (v?.amount || 0) * (v?.unit_price || 0), 0);

                                    return (
                                        <tr key={i} className="hover:bg-gray-50">
                                            <td className="px-6 py-4">{new Date(log.date).toLocaleDateString()}</td>
                                            <td className="px-6 py-4">{factories[log.factory_id]?.name || log.factory_id}</td>
                                            <td className="px-6 py-4">{production}</td>
                                            <td className="px-6 py-4">{sales}</td>
                                            <td className="px-6 py-4">${revenue}</td>
                                            <td className="px-6 py-4">{log.downtime_hours}h</td>
                                            <td className="px-6 py-4">{log.created_by}</td>
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
