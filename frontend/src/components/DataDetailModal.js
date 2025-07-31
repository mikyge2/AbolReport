// src/components/DataDetailModal.js
import React from 'react';

const DataDetailModal = ({ isOpen, onClose, data, type }) => {
    if (!isOpen || !data) return null;

    const formatCurrency = (value) => `$${parseFloat(value).toFixed(2)}`;
    const formatNumber = (value) => parseFloat(value).toLocaleString();

    const renderDailyLogDetails = () => (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2">📊 Production Data</h4>
                    <div className="space-y-1">
                        {Object.entries(data.production_data || {}).map(([product, quantity]) => (
                            <div key={product} className="flex justify-between text-sm">
                                <span className="text-gray-600">{product}:</span>
                                <span className="font-medium">{formatNumber(quantity)} units</span>
                            </div>
                        ))}
                        <div className="pt-2 border-t border-blue-200">
                            <div className="flex justify-between font-semibold text-blue-800">
                                <span>Total Production:</span>
                                <span>{formatNumber(Object.values(data.production_data || {}).reduce((a, b) => a + b, 0))} units</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-yellow-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-yellow-800 mb-2">💰 Sales Data</h4>
                    <div className="space-y-1">
                        {Object.entries(data.sales_data || {}).map(([product, sales]) => {
                            const amount = typeof sales === 'object' ? sales.amount : sales;
                            const price = typeof sales === 'object' ? sales.unit_price : 0;
                            return (
                                <div key={product} className="text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">{product}:</span>
                                        <span className="font-medium">{formatNumber(amount)} units</span>
                                    </div>
                                    {price > 0 && (
                                        <div className="flex justify-between text-xs text-gray-500 ml-2">
                                            <span>@ {formatCurrency(price)}/unit</span>
                                            <span>= {formatCurrency(amount * price)}</span>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                        <div className="pt-2 border-t border-yellow-200">
                            <div className="flex justify-between font-semibold text-yellow-800">
                                <span>Total Sales:</span>
                                <span>{formatNumber(Object.values(data.sales_data || {}).reduce((acc, sales) => {
                                    const amount = typeof sales === 'object' ? sales.amount : sales;
                                    return acc + amount;
                                }, 0))} units</span>
                            </div>
                            <div className="flex justify-between font-semibold text-yellow-800">
                                <span>Total Revenue:</span>
                                <span>{formatCurrency(Object.values(data.sales_data || {}).reduce((acc, sales) => {
                                    if (typeof sales === 'object') {
                                        return acc + (sales.amount * sales.unit_price);
                                    }
                                    return acc;
                                }, 0))}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="bg-red-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-red-800 mb-2">⏱️ Downtime Information</h4>
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <span className="text-gray-600">Total Downtime:</span>
                            <span className="font-medium">{data.downtime_hours?.toFixed(2) || '0.00'} hours</span>
                        </div>
                        {data.downtime_reasons && data.downtime_reasons.length > 0 && (
                            <div>
                                <span className="text-sm font-medium text-gray-700">Reasons:</span>
                                <div className="mt-1 space-y-1">
                                    {data.downtime_reasons.map((reason, index) => (
                                        <div key={index} className="flex justify-between text-sm bg-white p-2 rounded">
                                            <span className="text-gray-600">{reason.reason}:</span>
                                            <span className="font-medium">{reason.hours?.toFixed(2) || '0.00'} hrs</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="bg-green-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-green-800 mb-2">📦 Stock Data</h4>
                    <div className="space-y-1">
                        {Object.entries(data.stock_data || {}).map(([product, stock]) => (
                            <div key={product} className="flex justify-between text-sm">
                                <span className="text-gray-600">{product}:</span>
                                <span className="font-medium">{formatNumber(stock)} units</span>
                            </div>
                        ))}
                        <div className="pt-2 border-t border-green-200">
                            <div className="flex justify-between font-semibold text-green-800">
                                <span>Total Stock:</span>
                                <span>{formatNumber(Object.values(data.stock_data || {}).reduce((a, b) => a + b, 0))} units</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-gray-50 p-3 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">ℹ️ Log Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span className="text-gray-600">Report ID:</span>
                        <span className="font-medium ml-2 font-mono text-blue-600">{data.report_id || 'N/A'}</span>
                    </div>
                    <div>
                        <span className="text-gray-600">Date:</span>
                        <span className="font-medium ml-2">{new Date(data.date).toLocaleDateString()}</span>
                    </div>
                    <div>
                        <span className="text-gray-600">Created by:</span>
                        <span className="font-medium ml-2">{data.created_by}</span>
                    </div>
                    <div>
                        <span className="text-gray-600">Factory:</span>
                        <span className="font-medium ml-2">{data.factory_name || data.factory_id}</span>
                    </div>
                    <div>
                        <span className="text-gray-600">Efficiency:</span>
                        <span className="font-medium ml-2">
                            {data.efficiency ? `${data.efficiency.toFixed(1)}%` : 'N/A'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderChartDataDetails = () => (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2">📊 Production</h4>
                    <div className="text-2xl font-bold text-blue-900">{formatNumber(data.production)} units</div>
                    {data.production_breakdown && (
                        <div className="mt-2 space-y-1">
                            {Object.entries(data.production_breakdown).map(([product, quantity]) => (
                                <div key={product} className="flex justify-between text-sm">
                                    <span className="text-gray-600">{product}:</span>
                                    <span>{formatNumber(quantity)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="bg-yellow-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-yellow-800 mb-2">💰 Sales</h4>
                    <div className="text-2xl font-bold text-yellow-900">{formatNumber(data.sales)} units</div>
                    {data.revenue && (
                        <div className="text-lg font-semibold text-yellow-800 mt-1">
                            Revenue: {formatCurrency(data.revenue)}
                        </div>
                    )}
                </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">📅 Date Information</h4>
                <div className="text-lg font-medium">{data.date}</div>
                {data.factory_name && (
                    <div className="text-sm text-gray-600 mt-1">Factory: {data.factory_name}</div>
                )}
            </div>
        </div>
    );

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                    <h3 className="text-xl font-bold text-gray-800">
                        {type === 'daily_log' ? '📋 Daily Log Details' : '📊 Data Point Details'}
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="p-6">
                    {type === 'daily_log' ? renderDailyLogDetails() : renderChartDataDetails()}
                </div>

                <div className="sticky bottom-0 bg-gray-50 px-6 py-3 border-t border-gray-200">
                    <button
                        onClick={onClose}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Close Details
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DataDetailModal;