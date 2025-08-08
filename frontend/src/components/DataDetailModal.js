// src/components/DataDetailModal.js
import React from 'react';

const DataDetailModal = ({ isOpen, onClose, data, type }) => {
    if (!isOpen || !data) return null;

    const formatCurrency = (value) => `$${parseFloat(value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    const formatNumber = (value) => parseFloat(value).toLocaleString();

    const renderDailyLogDetails = () => (
        <div className="space-y-3 sm:space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="bg-blue-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2 text-sm sm:text-base">📊 Production Data</h4>
                    <div className="space-y-1">
                        {Object.entries(data.production_data || {}).map(([product, quantity]) => (
                            <div key={product} className="flex justify-between text-xs sm:text-sm">
                                <span className="text-gray-600 truncate mr-2">{product}:</span>
                                <span className="font-medium flex-shrink-0">{formatNumber(quantity)} units</span>
                            </div>
                        ))}
                        <div className="pt-2 border-t border-blue-200">
                            <div className="flex justify-between font-semibold text-blue-800 text-xs sm:text-sm">
                                <span>Total Production:</span>
                                <span>{formatNumber(Object.values(data.production_data || {}).reduce((a, b) => a + b, 0))} units</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-yellow-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-yellow-800 mb-2 text-sm sm:text-base">💰 Sales Data</h4>
                    <div className="space-y-1">
                        {Object.entries(data.sales_data || {}).map(([product, sales]) => {
                            const amount = typeof sales === 'object' ? sales.amount : sales;
                            const price = typeof sales === 'object' ? sales.unit_price : 0;
                            return (
                                <div key={product} className="text-xs sm:text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600 truncate mr-2">{product}:</span>
                                        <span className="font-medium flex-shrink-0">{formatNumber(amount)} units</span>
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
                            <div className="flex justify-between font-semibold text-yellow-800 text-xs sm:text-sm">
                                <span>Total Sales:</span>
                                <span>{formatNumber(Object.values(data.sales_data || {}).reduce((acc, sales) => {
                                    const amount = typeof sales === 'object' ? sales.amount : sales;
                                    return acc + amount;
                                }, 0))} units</span>
                            </div>
                            <div className="flex justify-between font-semibold text-yellow-800 text-xs sm:text-sm">
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="bg-red-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-red-800 mb-2 text-sm sm:text-base">⏱️ Downtime Information</h4>
                    <div className="space-y-2">
                        <div className="flex justify-between text-xs sm:text-sm">
                            <span className="text-gray-600">Total Downtime:</span>
                            <span className="font-medium">{data.downtime_hours?.toFixed(2) || '0.00'} hours</span>
                        </div>
                        {data.downtime_reasons && data.downtime_reasons.length > 0 && (
                            <div>
                                <span className="text-xs sm:text-sm font-medium text-gray-700">Reasons:</span>
                                <div className="mt-1 space-y-1">
                                    {data.downtime_reasons.map((reason, index) => (
                                        <div key={index} className="flex justify-between text-xs sm:text-sm bg-white p-2 rounded">
                                            <span className="text-gray-600 truncate mr-2">{reason.reason}:</span>
                                            <span className="font-medium flex-shrink-0">{reason.hours?.toFixed(2) || '0.00'} hrs</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="bg-green-50 p-3 rounded-lg">
                    <h4 className="font-semibold text-green-800 mb-2 text-sm sm:text-base">📦 Stock Data</h4>
                    <div className="space-y-1">
                        {Object.entries(data.stock_data || {}).map(([product, stock]) => (
                            <div key={product} className="flex justify-between text-xs sm:text-sm">
                                <span className="text-gray-600 truncate mr-2">{product}:</span>
                                <span className="font-medium flex-shrink-0">{formatNumber(stock)} units</span>
                            </div>
                        ))}
                        <div className="pt-2 border-t border-green-200">
                            <div className="flex justify-between font-semibold text-green-800 text-xs sm:text-sm">
                                <span>Total Stock:</span>
                                <span>{formatNumber(Object.values(data.stock_data || {}).reduce((a, b) => a + b, 0))} units</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-gray-50 p-3 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 text-sm sm:text-base">ℹ️ Log Information</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-xs sm:text-sm">
                    <div className="space-y-2">
                        <div>
                            <span className="text-gray-600 block sm:inline">Report ID:</span>
                            <span className="font-medium ml-0 sm:ml-2 font-mono text-blue-600 bg-blue-50 px-2 py-1 rounded block sm:inline mt-1 sm:mt-0">
                                {data.report_id || 'N/A'}
                            </span>
                        </div>
                        <div>
                            <span className="text-gray-600 block sm:inline">Date:</span>
                            <span className="font-medium ml-0 sm:ml-2 block sm:inline">{new Date(data.date).toLocaleDateString()}</span>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <div>
                            <span className="text-gray-600 block sm:inline">Created by:</span>
                            <span className="font-medium ml-0 sm:ml-2 block sm:inline">{data.created_by}</span>
                        </div>
                        <div>
                            <span className="text-gray-600 block sm:inline">Factory:</span>
                            <span className="font-medium ml-0 sm:ml-2 block sm:inline">{data.factory_name || data.factory_id}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderChartDataDetails = () => (
        <div className="space-y-3 sm:space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="bg-blue-50 p-3 sm:p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2 text-sm sm:text-base">📊 Production</h4>
                    <div className="text-xl sm:text-2xl font-bold text-blue-900">{formatNumber(data.production)} units</div>
                    {data.production_breakdown && (
                        <div className="mt-2 space-y-1">
                            {Object.entries(data.production_breakdown).map(([product, quantity]) => (
                                <div key={product} className="flex justify-between text-xs sm:text-sm">
                                    <span className="text-gray-600 truncate mr-2">{product}:</span>
                                    <span className="flex-shrink-0">{formatNumber(quantity)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="bg-yellow-50 p-3 sm:p-4 rounded-lg">
                    <h4 className="font-semibold text-yellow-800 mb-2 text-sm sm:text-base">💰 Sales</h4>
                    <div className="text-xl sm:text-2xl font-bold text-yellow-900">{formatNumber(data.sales)} units</div>
                    {data.revenue && (
                        <div className="text-base sm:text-lg font-semibold text-yellow-800 mt-1">
                            Revenue: {formatCurrency(data.revenue)}
                        </div>
                    )}
                </div>
            </div>

            <div className="bg-gray-50 p-3 sm:p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2 text-sm sm:text-base">📅 Date Information</h4>
                <div className="text-base sm:text-lg font-medium">{data.date}</div>
                {data.factory_name && (
                    <div className="text-xs sm:text-sm text-gray-600 mt-1">Factory: {data.factory_name}</div>
                )}
            </div>
        </div>
    );

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
            <div className="bg-white rounded-lg w-full max-w-xs sm:max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto modal-content-mobile">
                <div className="sticky top-0 bg-white border-b border-gray-200 px-3 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
                    <div className="flex-1 mr-3">
                        <h3 className="text-base sm:text-xl font-bold text-gray-800">
                            <span className="hidden sm:inline">
                                {type === 'daily_log' ? '📋 Daily Production Report Details' : '📊 Chart Data Point Details'}
                            </span>
                            <span className="sm:hidden">
                                {type === 'daily_log' ? '📋 Report Details' : '📊 Data Details'}
                            </span>
                        </h3>
                        {data?.report_id && (
                            <span className="font-mono text-xs sm:text-sm text-blue-600 bg-blue-50 px-2 sm:px-3 py-1 rounded-full mt-1 inline-block">
                                {data.report_id}
                            </span>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0 p-1"
                    >
                        <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="p-3 sm:p-6">
                    {type === 'daily_log' ? renderDailyLogDetails() : renderChartDataDetails()}
                </div>

                <div className="sticky bottom-0 bg-gray-50 px-3 sm:px-6 py-3 border-t border-gray-200">
                    <button
                        onClick={onClose}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm sm:text-base touch-friendly"
                    >
                        Close Details
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DataDetailModal;