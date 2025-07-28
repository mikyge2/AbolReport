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
        downtime_reasons: [],
        stock_data: {},
    });

    // New states for downtime reasons
    const [currentReason, setCurrentReason] = useState('');
    const [currentHours, setCurrentHours] = useState('');
    const [totalAllocatedHours, setTotalAllocatedHours] = useState(0);

    useEffect(() => {
        fetchFactories();
    }, []);

    // Calculate total allocated hours whenever downtime_reasons changes
    useEffect(() => {
        const total = formData.downtime_reasons.reduce((sum, reason) => sum + reason.hours, 0);
        setTotalAllocatedHours(total);
    }, [formData.downtime_reasons]);

    const fetchFactories = async () => {
        try {
            const res = await axios.get(`${API}/factories`);
            setFactories(res.data);
        } catch (err) {
            toast.error('Failed to load factories');
        }
    };

    const addDowntimeReason = () => {
        if (!currentReason || !currentHours) {
            toast.error('Please enter both reason and hours');
            return;
        }

        const hours = parseFloat(currentHours);
        if (hours <= 0) {
            toast.error('Hours must be greater than 0');
            return;
        }

        const newTotal = totalAllocatedHours + hours;
        if (newTotal > formData.downtime_hours) {
            toast.error(`Total allocated hours (${newTotal}) cannot exceed total downtime hours (${formData.downtime_hours})`);
            return;
        }

        setFormData({
            ...formData,
            downtime_reasons: [...formData.downtime_reasons, { reason: currentReason, hours }]
        });
        setCurrentReason('');
        setCurrentHours('');
    };

    const removeDowntimeReason = (index) => {
        const newReasons = formData.downtime_reasons.filter((_, i) => i !== index);
        setFormData({
            ...formData,
            downtime_reasons: newReasons
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validate downtime reasons if total downtime hours > 0
        if (formData.downtime_hours > 0) {
            if (formData.downtime_reasons.length === 0) {
                toast.error('Please add at least one downtime reason when downtime hours are specified');
                return;
            }
            
            if (Math.abs(totalAllocatedHours - formData.downtime_hours) > 0.01) {
                toast.error(`Total allocated hours (${totalAllocatedHours}) must equal total downtime hours (${formData.downtime_hours})`);
                return;
            }
        }

        const toastId = toast.loading('Submitting daily log...');
        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API}/daily-logs`, {
                ...formData,
                factory_id: selectedFactory,
                date: new Date(formData.date).toISOString(),
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            toast.success('Daily log submitted successfully!', { id: toastId });
            setFormData({
                date: new Date().toISOString().split('T')[0],
                production_data: {},
                sales_data: {},
                downtime_hours: 0,
                downtime_reasons: [],
                stock_data: {},
            });
            setSelectedFactory('');
        } catch (err) {
            console.error('Error submitting daily log:', err);
            toast.error(err.response?.data?.detail || 'Failed to submit daily log', { id: toastId });
        }
    };

    const handleDowntimeHoursChange = (e) => {
        const hours = parseFloat(e.target.value) || 0;
        setFormData({ ...formData, downtime_hours: hours });
        
        // If reducing hours below current allocated total, show warning
        if (hours < totalAllocatedHours) {
            toast.warning(`Reducing downtime hours below allocated total (${totalAllocatedHours}). Please adjust reasons.`);
        }
    };

    const remainingHours = formData.downtime_hours - totalAllocatedHours;

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

                {/* Downtime Section */}
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Total Downtime Hours</label>
                        <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={formData.downtime_hours}
                            onChange={handleDowntimeHoursChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                    </div>

                    {/* Downtime Reasons Section */}
                    {formData.downtime_hours > 0 && (
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="text-lg font-semibold text-gray-800 mb-4">Downtime Breakdown</h3>
                            
                            {/* Add Reason Form */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                                    <input
                                        type="text"
                                        value={currentReason}
                                        onChange={(e) => setCurrentReason(e.target.value)}
                                        placeholder="e.g., Machine failure"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Hours</label>
                                    <input
                                        type="number"
                                        min="0"
                                        step="0.1"
                                        value={currentHours}
                                        onChange={(e) => setCurrentHours(e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                                    />
                                </div>
                                <div className="flex items-end">
                                    <button
                                        type="button"
                                        onClick={addDowntimeReason}
                                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md"
                                    >
                                        Add Reason
                                    </button>
                                </div>
                            </div>

                            {/* Summary */}
                            <div className="bg-white rounded-lg p-3 mb-4">
                                <div className="flex justify-between items-center text-sm">
                                    <span>Total Downtime: <strong>{formData.downtime_hours} hours</strong></span>
                                    <span>Allocated: <strong>{totalAllocatedHours} hours</strong></span>
                                    <span className={`font-medium ${remainingHours === 0 ? 'text-green-600' : remainingHours > 0 ? 'text-orange-600' : 'text-red-600'}`}>
                                        Remaining: <strong>{remainingHours} hours</strong>
                                    </span>
                                </div>
                            </div>

                            {/* Reasons List */}
                            {formData.downtime_reasons.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="text-md font-medium text-gray-700">Added Reasons:</h4>
                                    {formData.downtime_reasons.map((reason, index) => (
                                        <div key={index} className="flex items-center justify-between bg-white rounded-lg p-3 border">
                                            <div>
                                                <span className="font-medium text-gray-800">{reason.reason}</span>
                                                <span className="text-gray-600 ml-2">({reason.hours} hours)</span>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => removeDowntimeReason(index)}
                                                className="text-red-600 hover:text-red-800 font-medium"
                                            >
                                                Remove
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
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
