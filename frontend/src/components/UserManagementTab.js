// src/components/UserManagementTab.js
import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AuthContext } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const UserManagementTab = () => {
    const { user } = useContext(AuthContext);
    const [users, setUsers] = useState([]);
    const [factories, setFactories] = useState({});
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({
        firstName: '',
        lastName: '',
        username: '',
        password: '',
        role: 'factory_employer',
        factoryId: '',
    });

    const [editingUserId, setEditingUserId] = useState(null);

    useEffect(() => {
        fetchUsers();
        fetchFactories();
    }, []);

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${API}/users`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            setUsers(res.data);
        } catch (err) {
            console.error('Error fetching users:', err);
            toast.error('Failed to load users');
        } finally {
            setLoading(false);
        }
    };

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
        if (!form.username) {
            toast.error('Username is required');
            return;
        }

        if (!editingUserId && !form.password) {
            toast.error('Password is required for new users');
            return;
        }

        // Validate factory_id for factory employers
        if (form.role === 'factory_employer' && !form.factoryId) {
            toast.error('Factory selection is required for factory employers');
            return;
        }

        const payload = {
            first_name: form.firstName,
            last_name: form.lastName,
            username: form.username,
            email: form.username + '@company.com', // Generate email from username
            role: form.role,
        };

        // Only include factory_id for factory employers
        if (form.role === 'factory_employer') {
            payload.factory_id = form.factoryId;
        }

        if (form.password) {
            payload.password = form.password;
        }

        try {
            const token = localStorage.getItem('token');
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            };

            if (editingUserId) {
                await axios.put(`${API}/users/${editingUserId}`, payload, { headers });
                toast.success('User updated');
            } else {
                await axios.post(`${API}/users`, payload, { headers });
                toast.success('User created');
            }
            setForm({
                firstName: '',
                lastName: '',
                username: '',
                password: '',
                role: 'factory_employer',
                factoryId: '',
            });
            setEditingUserId(null);
            fetchUsers();
        } catch (err) {
            console.error('Error saving user:', err);
            toast.error(err.response?.data?.detail || 'Failed to save user');
        }
    };

    const handleEdit = (user) => {
        setEditingUserId(user.id);
        setForm({
            firstName: user.first_name || '',
            lastName: user.last_name || '',
            username: user.username,
            password: '',
            role: user.role,
            factoryId: user.factory_id || '',
        });
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this user?')) return;
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${API}/users/${id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            toast.success('User deleted');
            fetchUsers();
        } catch (err) {
            console.error('Error deleting user:', err);
            toast.error('Failed to delete user');
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-primary mb-4">
                    User Management
                </h2>

                {/* User Form */}
                <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            First Name
                        </label>
                        <input
                            type="text"
                            value={form.firstName}
                            onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Last Name
                        </label>
                        <input
                            type="text"
                            value={form.lastName}
                            onChange={(e) => setForm({ ...form, lastName: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Username *
                        </label>
                        <input
                            type="text"
                            value={form.username}
                            onChange={(e) => setForm({ ...form, username: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Password *
                        </label>
                        <input
                            type="password"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                            required={!editingUserId}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Role *
                        </label>
                        <select
                            value={form.role}
                            onChange={(e) => setForm({ ...form, role: e.target.value })}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                            required
                        >
                            <option value="factory_employer">Factory Employer</option>
                            <option value="headquarters">Headquarters</option>
                        </select>
                    </div>
                    {form.role === 'factory_employer' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Working Factory *
                            </label>
                            <select
                                value={form.factoryId}
                                onChange={(e) => setForm({ ...form, factoryId: e.target.value })}
                                className="w-full border border-gray-300 rounded px-3 py-2"
                                required
                            >
                                <option value="">Select Factory</option>
                                {Object.entries(factories || {}).map(([id, f]) => (
                                    <option key={id} value={id}>
                                        {f.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    <div className="md:col-span-2 flex space-x-2">
                        <button
                            type="submit"
                            className="bg-primary hover:bg-primary-dark text-white font-medium py-2 px-4 rounded"
                        >
                            {editingUserId ? 'Update User' : 'Create User'}
                        </button>
                        {editingUserId && (
                            <button
                                type="button"
                                onClick={() => {
                                    setEditingUserId(null);
                                    setForm({
                                        firstName: '',
                                        lastName: '',
                                        username: '',
                                        password: '',
                                        role: 'factory_employer',
                                        factoryId: '',
                                    });
                                }}
                                className="bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded"
                            >
                                Cancel
                            </button>
                        )}
                    </div>
                </form>

                {/* User List */}
                <div className="overflow-x-auto">
                    {loading ? (
                        <p>Loading users...</p>
                    ) : users.length === 0 ? (
                        <p className="text-gray-500">No users found.</p>
                    ) : (
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                        Username
                                    </th>
                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                        Name
                                    </th>
                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                        Role
                                    </th>
                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                                        Factory
                                    </th>
                                    <th className="px-4 py-2"></th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {users.map((u) => (
                                    <tr key={u.id}>
                                        <td className="px-4 py-2">{u.username}</td>
                                        <td className="px-4 py-2">{u.first_name || ''} {u.last_name || ''}</td>
                                        <td className="px-4 py-2">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                u.role === 'headquarters' 
                                                    ? 'bg-purple-100 text-purple-800' 
                                                    : 'bg-blue-100 text-blue-800'
                                            }`}>
                                                {u.role === 'headquarters' ? 'HQ' : 'Factory'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-2">
                                            {u.role === 'headquarters' ? 'All Factories' : (factories[u.factory_id]?.name || u.factory_id)}
                                        </td>
                                        <td className="px-4 py-2 space-x-2">
                                            <button
                                                onClick={() => handleEdit(u)}
                                                className="text-blue-600 hover:text-blue-800 text-sm"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleDelete(u.id)}
                                                className="text-red-600 hover:text-red-800 text-sm"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UserManagementTab;
