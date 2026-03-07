/**
 * Footer Component
 * Bottom footer with links and copyright
 */

import React from 'react';
import { Box, Container, Typography, Link, Grid } from '@mui/material';
import { Phone, Email, LocationOn } from '@mui/icons-material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        bgcolor: 'primary.main',
        color: 'white',
        py: 6,
        mt: 'auto',
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* About */}
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="h6" gutterBottom>
              SarvaSahay Platform
            </Typography>
            <Typography variant="body2">
              AI-powered government scheme eligibility and enrollment platform
              for rural Indian citizens.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              सरकारी योजनाओं के लिए पात्रता जांच और नामांकन मंच
            </Typography>
          </Grid>

          {/* Quick Links */}
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="h6" gutterBottom>
              Quick Links
            </Typography>
            <Box>
              <Link href="/" color="inherit" display="block" sx={{ mb: 1 }}>
                Home
              </Link>
              <Link href="/eligibility" color="inherit" display="block" sx={{ mb: 1 }}>
                Check Eligibility
              </Link>
              <Link href="/help" color="inherit" display="block" sx={{ mb: 1 }}>
                Help & Support
              </Link>
              <Link href="http://localhost:8000/docs" color="inherit" display="block" target="_blank">
                API Documentation
              </Link>
            </Box>
          </Grid>

          {/* Contact */}
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="h6" gutterBottom>
              Contact Us
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Phone sx={{ mr: 1, fontSize: 20 }} />
              <Typography variant="body2">1800-XXX-XXXX (Toll Free)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <LocationOn sx={{ mr: 1, fontSize: 20 }} />
              <Typography variant="body2">Mumbai, Maharashtra, India</Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Copyright */}
        <Box sx={{ mt: 4, pt: 4, borderTop: '1px solid rgba(255,255,255,0.2)' }}>
          <Typography variant="body2" align="center">
            © {new Date().getFullYear()} SarvaSahay Platform. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
