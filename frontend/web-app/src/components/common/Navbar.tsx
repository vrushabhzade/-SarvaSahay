/**
 * Navigation Bar Component
 * Top navigation with menu, language selector, and auth status
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Container,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Language,
  CheckCircle,
  Error,
} from '@mui/icons-material';

interface NavbarProps {
  isAuthenticated: boolean;
  backendStatus: 'checking' | 'connected' | 'error';
}

const Navbar: React.FC<NavbarProps> = ({ isAuthenticated, backendStatus }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [langAnchorEl, setLangAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLangMenu = (event: React.MouseEvent<HTMLElement>) => {
    setLangAnchorEl(event.currentTarget);
  };

  const handleLangClose = () => {
    setLangAnchorEl(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  const menuItems = [
    { label: 'Home', path: '/' },
    { label: 'Eligibility', path: '/eligibility' },
    { label: 'Documents', path: '/documents' },
    { label: 'Applications', path: '/applications' },
    { label: 'Tracking', path: '/tracking' },
    { label: 'Help', path: '/help' },
  ];

  return (
    <AppBar position="sticky">
      <Container maxWidth="lg">
        <Toolbar disableGutters>
          {/* Logo */}
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 0, mr: 4, cursor: 'pointer', fontWeight: 'bold' }}
            onClick={() => navigate('/')}
          >
            🇮🇳 SarvaSahay
          </Typography>

          {/* Desktop Menu */}
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
            {menuItems.map((item) => (
              <Button
                key={item.path}
                onClick={() => navigate(item.path)}
                sx={{ color: 'white', mx: 1 }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          {/* Backend Status */}
          <Chip
            icon={
              backendStatus === 'connected' ? (
                <CheckCircle />
              ) : backendStatus === 'error' ? (
                <Error />
              ) : undefined
            }
            label={
              backendStatus === 'connected'
                ? 'Online'
                : backendStatus === 'error'
                ? 'Offline'
                : 'Checking...'
            }
            color={
              backendStatus === 'connected'
                ? 'success'
                : backendStatus === 'error'
                ? 'error'
                : 'default'
            }
            size="small"
            sx={{ mr: 2, display: { xs: 'none', sm: 'flex' } }}
          />

          {/* Language Selector */}
          <IconButton
            size="large"
            onClick={handleLangMenu}
            color="inherit"
            sx={{ mr: 1 }}
          >
            <Language />
          </IconButton>
          <Menu
            anchorEl={langAnchorEl}
            open={Boolean(langAnchorEl)}
            onClose={handleLangClose}
          >
            <MenuItem onClick={handleLangClose}>English</MenuItem>
            <MenuItem onClick={handleLangClose}>हिंदी (Hindi)</MenuItem>
            <MenuItem onClick={handleLangClose}>मराठी (Marathi)</MenuItem>
          </Menu>

          {/* Auth Button */}
          {isAuthenticated ? (
            <>
              <IconButton
                size="large"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircle />
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem onClick={() => { handleClose(); navigate('/profile'); }}>
                  Profile
                </MenuItem>
                <MenuItem onClick={() => { handleClose(); handleLogout(); }}>
                  Logout
                </MenuItem>
              </Menu>
            </>
          ) : (
            <Button
              color="inherit"
              onClick={() => navigate('/login')}
              sx={{ ml: 2 }}
            >
              Login
            </Button>
          )}

          {/* Mobile Menu */}
          <IconButton
            size="large"
            onClick={handleMenu}
            color="inherit"
            sx={{ display: { xs: 'flex', md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Navbar;
