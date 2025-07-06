// src/components/LoggingTab.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
                            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
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
                            onChange={(e) => setFormData({ ...formData, downtime_hours: parseFloat(e.target.value) || 0 })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Downtime Reason</label>
                        <input
                            type="text"
                            value={formData.downtime_reason}
                            onChange={(e) => setFormData({ ...formData, downtime_reason: e.target.value })}
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

export default LoggingTab;
