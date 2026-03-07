/**
 * Login Page
 * OTP-based authentication
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Phone, Lock } from '@mui/icons-material';
import api, { endpoints } from '../services/api';

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const navigate = useNavigate();
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOTP = async () => {
    if (!phone || phone.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await api.post(endpoints.login, { phone: `+91-${phone}` });
      setStep('otp');
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post(endpoints.verify, {
        phone: `+91-${phone}`,
        otp,
      });

      localStorage.setItem('token', response.data.accessToken);
      onLogin();
      navigate('/profile');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Login to SarvaSahay
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" paragraph>
            सरवसहाय में लॉगिन करें
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {step === 'phone' ? (
            <Box>
              <TextField
                fullWidth
                label="Phone Number"
                placeholder="9876543210"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                InputProps={{
                  startAdornment: <Phone sx={{ mr: 1, color: 'action.active' }} />,
                }}
                sx={{ mb: 3 }}
                helperText="Enter your 10-digit mobile number"
              />

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleSendOTP}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Send OTP'}
              </Button>
            </Box>
          ) : (
            <Box>
              <Alert severity="info" sx={{ mb: 3 }}>
                OTP sent to +91-{phone}
              </Alert>

              <TextField
                fullWidth
                label="Enter OTP"
                placeholder="123456"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                InputProps={{
                  startAdornment: <Lock sx={{ mr: 1, color: 'action.active' }} />,
                }}
                sx={{ mb: 3 }}
                helperText="Enter the 6-digit OTP"
              />

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleVerifyOTP}
                disabled={loading}
                sx={{ mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Verify OTP'}
              </Button>

              <Button
                fullWidth
                variant="text"
                onClick={() => setStep('phone')}
              >
                Change Phone Number
              </Button>
            </Box>
          )}

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account? Create your profile after login.
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;
