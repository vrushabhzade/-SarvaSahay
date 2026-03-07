/**
 * Main App Component
 * Root component with routing and theme configuration
 */

import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import api from './services/api';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import EligibilityPage from './pages/EligibilityPage';
import DocumentsPage from './pages/DocumentsPage';
import ApplicationsPage from './pages/ApplicationsPage';
import TrackingPage from './pages/TrackingPage';
import HelpPage from './pages/HelpPage';

// Components
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';

// Theme configuration
const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Green - Government
    },
    secondary: {
      main: '#FF6F00', // Orange - India
    },
    success: {
      main: '#4CAF50',
    },
    error: {
      main: '#F44336',
    },
    warning: {
      main: '#FF9800',
    },
    info: {
      main: '#2196F3',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Noto Sans Devanagari", sans-serif',
  },
});

function App() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check backend connection on mount
  useEffect(() => {
    checkBackendConnection();
    checkAuthentication();
  }, []);

  const checkBackendConnection = async () => {
    try {
      const response = await api.get('/');
      console.log('Backend connected:', response.data);
      setBackendStatus('connected');
    } catch (error) {
      console.error('Backend connection failed:', error);
      setBackendStatus('error');
    }
  };

  const checkAuthentication = () => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar isAuthenticated={isAuthenticated} backendStatus={backendStatus} />
          
          <Box component="main" sx={{ flexGrow: 1, py: 3 }}>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage onLogin={() => setIsAuthenticated(true)} />} />
              <Route path="/help" element={<HelpPage />} />
              
              {/* Protected routes */}
              <Route
                path="/profile"
                element={isAuthenticated ? <ProfilePage /> : <Navigate to="/login" />}
              />
              <Route
                path="/eligibility"
                element={isAuthenticated ? <EligibilityPage /> : <Navigate to="/login" />}
              />
              <Route
                path="/documents"
                element={isAuthenticated ? <DocumentsPage /> : <Navigate to="/login" />}
              />
              <Route
                path="/applications"
                element={isAuthenticated ? <ApplicationsPage /> : <Navigate to="/login" />}
              />
              <Route
                path="/tracking"
                element={isAuthenticated ? <TrackingPage /> : <Navigate to="/login" />}
              />
              
              {/* 404 */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Box>
          
          <Footer />
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
