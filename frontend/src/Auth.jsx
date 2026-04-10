import { useState, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Camera, LogIn, LogOut, Settings2, Play, Square, RefreshCcw } from 'lucide-react';

const AuthContext = createContext();

// Use relative URL so it perfectly aligns with whatever IP or host name the user uses.
// (In development, this will be proxied by Vite to the backend)
axios.defaults.baseURL = '';

function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token') || null);

  const login = async (password) => {
    const formData = new URLSearchParams();
    formData.append('username', 'admin');
    formData.append('password', password);
    const res = await axios.post('/api/auth/token', formData);
    setToken(res.data.access_token);
    localStorage.setItem('token', res.data.access_token);
    // Setup axios default
    axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  // Set initial header
  if (token && !axios.defaults.headers.common['Authorization']) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function Login() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      await login(password);
      navigate('/');
    } catch (err) {
      setError('Invalid password');
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-panel login-card">
        <div style={{ textAlign: 'center' }}>
          <Camera size={48} color="var(--accent-color)" style={{ margin: '0 auto 1rem' }} />
          <h2>Camera Dashboard</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Welcome back! Please enter your admin password to continue.</p>
        </div>
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <input
            type="password"
            placeholder="Admin Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          {error && <p style={{ color: 'var(--danger-color)', fontSize: '0.875rem' }}>{error}</p>}
          <button type="submit">
            <LogIn size={20} /> Login
          </button>
        </form>
      </div>
    </div>
  );
}

// ... will split dashboard in next call
export { AuthProvider, Login, AuthContext };
