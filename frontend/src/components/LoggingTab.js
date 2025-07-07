// src/components/LoggingTab.js
import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LoggingTab = () => {
    const { user } = useContext(AuthContext);
    const [factories, setFactories] = useState({});
    const [selectedFactory, setSelectedFactory] = useState('');
    const [formData, setFormData] = useState({
        date: new Date().toISOString().split('T')[0],
        production_data: {},
        sales_data: {},
        downtime_hours: 0,
        downtime_reason: '',
        stock_data: {},
    });

    useEffect(() => {
        fetchFactories();
    }, []);

    const fetchFactories = async () => {
        try {
            const res = await axios.get(`${API}/factories`);
            setFactories(res.data);
        } catch (err) {
            toast.error('Failed to load factories');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const toastId = toast.loading('Submitting daily log...');
        try {
            await axios.post(`${API}/daily-logs`, {
                ...formData,
                factory_id: selectedFactory,
                date: new Date(formData.date).toISOString(),
            });
            toast.success('Daily log submitted successfully!', { id: toastId });
            setFormData({
                date: new Date().toISOString().split('T')[0],
                production_data: {},
                sales_data: {},
                downtime_hours: 0,
                downtime_reason: '',
                stock_data: {},
            });
            setSelectedFactory('');
        } catch (err) {
            toast.error('Failed to submit daily log', { id: toastId });
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
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        >
                            <option value="">Select Factory</option>
                            {Object.entries(factories || {}).map(([key, factory]) => (
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
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Downtime Hours</label>
                        <input
                            type="number"
                            min="0"
                            value={formData.downtime_hours}
                            onChange={(e) => setFormData({ ...formData, downtime_hours: parseFloat(e.target.value) || 0 })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Downtime Reason</label>
                        <input
                            type="text"
                            value={formData.downtime_reason}
                            onChange={(e) => setFormData({ ...formData, downtime_reason: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            placeholder="e.g., Maintenance"
                        />
                    </div>
                </div>

                {selectedFactory && factories[selectedFactory]?.products?.length > 0 && (
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Products</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {factories[selectedFactory].products.map((product) => (
                                <div key={product} className="border rounded p-4 space-y-2">
                                    <h4 className="font-medium text-gray-700">{product}</h4>
                                    <input
                                        type="number"
                                        min="0"
                                        placeholder="Production"
                                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                production_data: {
                                                    ...formData.production_data,
                                                    [product]: parseFloat(e.target.value) || 0,
                                                },
                                            })
                                        }
                                    />
                                    <input
                                        type="number"
                                        min="0"
                                        placeholder="Sales Amount"
                                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                sales_data: {
                                                    ...formData.sales_data,
                                                    [product]: {
                                                        ...(formData.sales_data[product] || {}),
                                                        amount: parseFloat(e.target.value) || 0,
                                                    },
                                                },
                                            })
                                        }
                                    />
                                    <input
                                        type="number"
                                        min="0"
                                        placeholder="Unit Price"
                                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                sales_data: {
                                                    ...formData.sales_data,
                                                    [product]: {
                                                        ...(formData.sales_data[product] || {}),
                                                        unit_price: parseFloat(e.target.value) || 0,
                                                    },
                                                },
                                            })
                                        }
                                    />
                                    <input
                                        type="number"
                                        min="0"
                                        placeholder="Current Stock"
                                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                stock_data: {
                                                    ...formData.stock_data,
                                                    [product]: parseFloat(e.target.value) || 0,
                                                },
                                            })
                                        }
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <button
                    type="submit"
                    className="w-full bg-primary hover:bg-primary-dark text-white font-medium py-3 px-6 rounded-md"
                >
                    Submit Daily Log
                </button>
            </form>
        </div>
    );
};

export default LoggingTab;
