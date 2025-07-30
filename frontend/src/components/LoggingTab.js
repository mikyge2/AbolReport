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

    // New states for existing logs and editing
    const [existingLogs, setExistingLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [editingLog, setEditingLog] = useState(null);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deletingLog, setDeletingLog] = useState(null);
    const [activeTab, setActiveTab] = useState('create'); // 'create' or 'manage'

    useEffect(() => {
        fetchFactories();
        fetchExistingLogs();
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

    const fetchExistingLogs = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${API}/daily-logs?created_by_me=true`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            setExistingLogs(res.data);
        } catch (err) {
            toast.error('Failed to load existing logs');
        } finally {
            setLoading(false);
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
            toast.error(`Total allocated hours cannot exceed total downtime hours (${formData.downtime_hours})`);
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

    const handleEditLog = (log) => {
        setEditingLog(log);
        setFormData({
            date: new Date(log.date).toISOString().split('T')[0],
            production_data: log.production_data,
            sales_data: log.sales_data,
            downtime_hours: log.downtime_hours,
            downtime_reasons: log.downtime_reasons,
            stock_data: log.stock_data,
        });
        setSelectedFactory(log.factory_id);
        setShowEditModal(true);
    };

    const handleUpdateLog = async (e) => {
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

        const toastId = toast.loading('Updating daily log...');
        try {
            const token = localStorage.getItem('token');
            await axios.put(`${API}/daily-logs/${editingLog.id}`, {
                ...formData,
                factory_id: selectedFactory,
                date: new Date(formData.date).toISOString(),
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            toast.success('Daily log updated successfully!', { id: toastId });
            setShowEditModal(false);
            setEditingLog(null);
            resetForm();
            fetchExistingLogs(); // Refresh the logs list
        } catch (err) {
            console.error('Error updating daily log:', err);
            toast.error(err.response?.data?.detail || 'Failed to update daily log', { id: toastId });
        }
    };

    const handleDeleteLog = (log) => {
        setDeletingLog(log);
        setShowDeleteConfirm(true);
    };

    const confirmDeleteLog = async () => {
        const toastId = toast.loading('Deleting daily log...');
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${API}/daily-logs/${deletingLog.id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            toast.success('Daily log deleted successfully!', { id: toastId });
            setShowDeleteConfirm(false);
            setDeletingLog(null);
            fetchExistingLogs(); // Refresh the logs list
        } catch (err) {
            console.error('Error deleting daily log:', err);
            toast.error(err.response?.data?.detail || 'Failed to delete daily log', { id: toastId });
        }
    };

    const resetForm = () => {
        setFormData({
            date: new Date().toISOString().split('T')[0],
            production_data: {},
            sales_data: {},
            downtime_hours: 0,
            downtime_reasons: [],
            stock_data: {},
        });
        setSelectedFactory('');
        setCurrentReason('');
        setCurrentHours('');
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
            resetForm();
            fetchExistingLogs(); // Refresh the logs list
        } catch (err) {
            console.error('Error submitting daily log:', err);
            toast.error(err.response?.data?.detail || 'Failed to submit daily log', { id: toastId });
        }
    };

    const handleDowntimeHoursChange = (hours) => {
        if (hours < totalAllocatedHours) {
            toast.warning(`Reducing downtime hours below allocated total (${totalAllocatedHours}). Please adjust reasons.`);
        }
    };

    const remainingHours = formData.downtime_hours - totalAllocatedHours;

    // Helper function to render the form (used in both create and edit)
    const renderForm = (onSubmit, isEditing = false) => (
        <form onSubmit={onSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Factory</label>
                    <select
                        value={selectedFactory}
                        onChange={(e) => setSelectedFactory(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        disabled={isEditing && user?.role === 'factory_employer'}
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
            <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Downtime Information</h3>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Total Downtime Hours</label>
                        <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={formData.downtime_hours}
                            onChange={(e) => {
                                const hours = parseFloat(e.target.value) || 0;
                                setFormData({ ...formData, downtime_hours: hours });
                                handleDowntimeHoursChange(hours);
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        />
                    </div>

                    {formData.downtime_hours > 0 && (
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="text-md font-medium text-gray-700 mb-3">Add Downtime Reasons</h4>
                            
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                                    <input
                                        type="text"
                                        value={currentReason}
                                        onChange={(e) => setCurrentReason(e.target.value)}
                                        placeholder="e.g., Equipment Maintenance"
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
            </div>

            {/* Products Section */}
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
                                    value={formData.production_data[product] || ''}
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
                                    value={formData.sales_data[product]?.amount || ''}
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
                                    value={formData.sales_data[product]?.unit_price || ''}
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
                                    value={formData.stock_data[product] || ''}
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
                {isEditing ? 'Update Daily Log' : 'Submit Daily Log'}
            </button>
        </form>
    );

    return (
        <div className="space-y-8">
            {/* Tab Navigation */}
            <div className="flex space-x-2 backdrop-blur-lg bg-white/5 rounded-2xl p-2 border border-white/10">
                <button
                    onClick={() => setActiveTab('create')}
                    className={`nav-tab ${activeTab === 'create' ? 'active' : ''}`}
                >
                    Create New Log
                </button>
                <button
                    onClick={() => setActiveTab('manage')}
                    className={`nav-tab ${activeTab === 'manage' ? 'active' : ''}`}
                >
                    Manage Existing Logs
                </button>
            </div>

            {/* Tab Content */}
            <div className="glass-card-light">
                <div className="p-6">
                    {activeTab === 'create' && (
                        <div>
                            <h2 className="text-2xl font-bold text-futuristic-primary mb-6">Create Daily Production Log</h2>
                            {renderForm(handleSubmit, false)}
                        </div>
                    )}

                    {activeTab === 'manage' && (
                        <div>
                            <h2 className="text-2xl font-bold text-futuristic-primary mb-6">Manage Existing Logs</h2>
                            
                            {loading ? (
                                <div className="flex justify-center items-center py-8">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                    <span className="ml-2 text-gray-600">Loading logs...</span>
                                </div>
                            ) : existingLogs.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <p>No daily logs found. Create your first log using the "Create New Log" tab.</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {existingLogs.map((log) => {
                                        const factory = factories[log.factory_id];
                                        const isOwnLog = log.created_by === user?.username;
                                        
                                        return (
                                            <div key={log.id} className="bg-gray-50 rounded-lg p-4 border">
                                                <div className="flex justify-between items-start">
                                                    <div className="flex-1">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <h3 className="text-lg font-medium text-gray-800">
                                                                {factory?.name || log.factory_id}
                                                            </h3>
                                                            <span className="text-sm text-gray-500">
                                                                {new Date(log.date).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                        
                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                                                            <div>
                                                                <span className="font-medium">Total Production:</span>
                                                                <br />
                                                                {Object.values(log.production_data).reduce((sum, val) => sum + val, 0)} {factory?.sku_unit || 'units'}
                                                            </div>
                                                            <div>
                                                                <span className="font-medium">Total Sales:</span>
                                                                <br />
                                                                {Object.values(log.sales_data).reduce((sum, item) => sum + (item.amount || 0), 0)} {factory?.sku_unit || 'units'}
                                                            </div>
                                                            <div>
                                                                <span className="font-medium">Downtime:</span>
                                                                <br />
                                                                {log.downtime_hours} hours
                                                            </div>
                                                            <div>
                                                                <span className="font-medium">Created by:</span>
                                                                <br />
                                                                {log.created_by}
                                                            </div>
                                                        </div>

                                                        {log.downtime_reasons && log.downtime_reasons.length > 0 && (
                                                            <div className="mb-3">
                                                                <span className="font-medium text-gray-700 text-sm">Downtime Reasons:</span>
                                                                <div className="flex flex-wrap gap-2 mt-1">
                                                                    {log.downtime_reasons.map((reason, index) => (
                                                                        <span key={index} className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                                                            {reason.reason} ({reason.hours}h)
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                    
                                                    {isOwnLog && (
                                                        <div className="flex space-x-2 ml-4">
                                                            <button
                                                                onClick={() => handleEditLog(log)}
                                                                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium"
                                                            >
                                                                Edit
                                                            </button>
                                                            <button
                                                                onClick={() => handleDeleteLog(log)}
                                                                className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium"
                                                            >
                                                                Delete
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Edit Modal */}
            {showEditModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-2xl font-bold text-primary">Edit Daily Log</h2>
                                <button
                                    onClick={() => {
                                        setShowEditModal(false);
                                        setEditingLog(null);
                                        resetForm();
                                    }}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                            {renderForm(handleUpdateLog, true)}
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Dialog */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
                        <div className="p-6">
                            <div className="flex items-center mb-4">
                                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                                    <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                    </svg>
                                </div>
                            </div>
                            <div className="text-center">
                                <h3 className="text-lg font-medium text-gray-900 mb-2">Delete Daily Log</h3>
                                <p className="text-sm text-gray-500 mb-4">
                                    Are you sure you want to delete this daily log for {factories[deletingLog?.factory_id]?.name} on {new Date(deletingLog?.date).toLocaleDateString()}? This action cannot be undone.
                                </p>
                                <div className="flex justify-center space-x-4">
                                    <button
                                        onClick={() => {
                                            setShowDeleteConfirm(false);
                                            setDeletingLog(null);
                                        }}
                                        className="bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded font-medium"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={confirmDeleteLog}
                                        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-medium"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LoggingTab;