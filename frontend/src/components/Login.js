// src/components/Login.js
import React, { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';

const Login = () => {
    const { login } = React.useContext(AuthContext);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        // Add a slight delay for better UX
        await new Promise(resolve => setTimeout(resolve, 500));

        const success = await login(username, password);
        if (!success) {
            setError('Invalid username or password');
        }
        setIsLoading(false);
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const role = 'headquarters';

        try {
            await axios.post(`${API}/register`, {
                username,
                email: `${username}@company.com`,
                password,
                role
            });

            const success = await login(username, password);
            if (!success) {
                setError('Registration successful but login failed');
            }
        } catch (error) {
            setError('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'));
        }
        setIsLoading(false);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-[#1a355b] to-black flex items-center justify-center p-4 relative overflow-hidden">
            {/* Animated background elements */}
            <div className="absolute inset-0 opacity-20">
                <div className="absolute top-20 left-20 w-72 h-72 bg-[#ffc72c] rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
                <div className="absolute top-40 right-20 w-72 h-72 bg-[#1a355b] rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-1000"></div>
                <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-2000"></div>
            </div>

            {/* Floating geometric shapes */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-4 h-4 bg-[#ffc72c] opacity-60 rotate-45 animate-float"></div>
                <div className="absolute top-1/3 right-1/3 w-6 h-6 border-2 border-[#ffc72c] opacity-40 animate-float-delayed"></div>
                <div className="absolute bottom-1/4 left-1/3 w-3 h-3 bg-white opacity-30 rounded-full animate-float-slow"></div>
                <div className="absolute bottom-1/3 right-1/4 w-5 h-5 border-2 border-white opacity-20 rotate-45 animate-float"></div>
            </div>

            <div className="relative z-10 w-full max-w-md">
                {/* Glassmorphism container */}
                <div className="backdrop-blur-lg bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-8 relative">
                    {/* Glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-[#1a355b]/20 to-[#ffc72c]/20 rounded-2xl blur-xl -z-10"></div>

                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-[#1a355b] to-[#ffc72c] rounded-xl mb-4 shadow-lg">
                            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-[#ffc72c] bg-clip-text text-transparent mb-2">
                            Factory Portal
                        </h1>
                        <p className="text-gray-300 text-sm">Production & Sales Management System</p>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="bg-red-500/20 border border-red-500/30 text-red-200 px-4 py-3 rounded-xl mb-6 backdrop-blur-sm animate-shake">
                            <div className="flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {error}
                            </div>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={isRegistering ? handleRegister : handleLogin} className="space-y-6">
                        {/* Username field */}
                        <div className="relative">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#ffc72c] focus:border-transparent backdrop-blur-sm transition-all duration-300 hover:bg-white/20"
                                    placeholder="Enter your username"
                                    required
                                />
                                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Password field */}
                        <div className="relative">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                            <div className="relative">
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#ffc72c] focus:border-transparent backdrop-blur-sm transition-all duration-300 hover:bg-white/20"
                                    placeholder="Enter your password"
                                    required
                                />
                                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Submit button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-[#1a355b] to-[#ffc72c] hover:from-[#1a355b]/90 hover:to-[#ffc72c]/90 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 transform hover:scale-[1.02] hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden group"
                        >
                            {/* Button glow effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-[#1a355b] to-[#ffc72c] opacity-0 group-hover:opacity-20 transition-opacity duration-300 blur-xl"></div>

                            <div className="relative flex items-center justify-center">
                                {isLoading ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        {isRegistering ? 'Create Account' : 'Sign In'}
                                        <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                        </svg>
                                    </>
                                )}
                            </div>
                        </button>
                    </form>

                    {/* Toggle register/login */}
                    <div className="mt-8 text-center">
                        <button
                            onClick={() => setIsRegistering(!isRegistering)}
                            className="text-[#ffc72c] hover:text-[#ffc72c]/80 font-medium transition-colors duration-300 underline decoration-dotted underline-offset-4"
                        >
                            {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Create One'}
                        </button>
                    </div>

                    {/* Demo credentials */}
                    <div className="mt-8 text-center">
                        <div className="bg-[#1a355b]/20 border border-[#1a355b]/30 rounded-xl p-4 backdrop-blur-sm">
                            <p className="text-[#ffc72c] text-sm font-medium mb-2">Demo Credentials</p>
                            <div className="text-gray-300 text-xs space-y-1">
                                <p>Username: <span className="font-mono bg-white/10 px-2 py-1 rounded">admin</span></p>
                                <p>Password: <span className="font-mono bg-white/10 px-2 py-1 rounded">admin123</span></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
