/**
 * Home Page
 * Landing page with welcome message and quick actions
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Button,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import {
  CheckCircle,
  Description,
  Assignment,
  TrackChanges,
  Phone,
  Help,
} from '@mui/icons-material';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <CheckCircle sx={{ fontSize: 48, color: 'primary.main' }} />,
      title: 'Check Eligibility',
      titleHindi: 'पात्रता जांचें',
      titleMarathi: 'पात्रता तपासा',
      description: 'Find out which government schemes you qualify for',
      descriptionHindi: 'जानें कि आप किन सरकारी योजनाओं के लिए पात्र हैं',
      descriptionMarathi: 'तुम्ही कोणत्या सरकारी योजनांसाठी पात्र आहात ते शोधा',
      action: () => navigate('/eligibility'),
    },
    {
      icon: <Description sx={{ fontSize: 48, color: 'secondary.main' }} />,
      title: 'Upload Documents',
      titleHindi: 'दस्तावेज़ अपलोड करें',
      titleMarathi: 'कागदपत्रे अपलोड करा',
      description: 'Upload and verify your documents',
      descriptionHindi: 'अपने दस्तावेज़ अपलोड और सत्यापित करें',
      descriptionMarathi: 'तुमची कागदपत्रे अपलोड आणि सत्यापित करा',
      action: () => navigate('/documents'),
    },
    {
      icon: <Assignment sx={{ fontSize: 48, color: 'success.main' }} />,
      title: 'Apply for Schemes',
      titleHindi: 'योजनाओं के लिए आवेदन करें',
      titleMarathi: 'योजनांसाठी अर्ज करा',
      description: 'Submit applications with auto-filled forms',
      descriptionHindi: 'स्वतः भरे गए फॉर्म के साथ आवेदन जमा करें',
      descriptionMarathi: 'स्वयं भरलेल्या फॉर्मसह अर्ज सबमिट करा',
      action: () => navigate('/applications'),
    },
    {
      icon: <TrackChanges sx={{ fontSize: 48, color: 'info.main' }} />,
      title: 'Track Applications',
      titleHindi: 'आवेदन ट्रैक करें',
      titleMarathi: 'अर्ज ट्रॅक करा',
      description: 'Monitor your application status in real-time',
      descriptionHindi: 'अपने आवेदन की स्थिति को रीयल-टाइम में मॉनिटर करें',
      descriptionMarathi: 'तुमच्या अर्जाची स्थिती रिअल-टाइममध्ये पहा',
      action: () => navigate('/tracking'),
    },
  ];

  return (
    <Container maxWidth="lg">
      {/* Hero Section */}
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
          🇮🇳 SarvaSahay Platform
        </Typography>
        <Typography variant="h4" component="h2" gutterBottom color="text.secondary">
          सरवसहाय मंच
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          AI-powered government scheme eligibility and enrollment platform
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          सरकारी योजनाओं के लिए पात्रता जांच और नामांकन मंच
        </Typography>
        
        <Box sx={{ mt: 4 }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/eligibility')}
            sx={{ mr: 2, mb: 2 }}
          >
            Check Eligibility Now
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={() => navigate('/help')}
            sx={{ mb: 2 }}
          >
            Learn More
          </Button>
        </Box>
      </Box>

      {/* Features Grid */}
      <Grid container spacing={4} sx={{ mb: 8 }}>
        {features.map((feature, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                <Typography variant="h6" component="h3" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {feature.titleHindi}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button size="small" onClick={feature.action}>
                  Get Started
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Stats Section */}
      <Box sx={{ bgcolor: 'primary.main', color: 'white', py: 6, px: 4, borderRadius: 2, mb: 8 }}>
        <Grid container spacing={4} textAlign="center">
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="h3" component="div" gutterBottom>
              30+
            </Typography>
            <Typography variant="body1">Government Schemes</Typography>
            <Typography variant="body2">सरकारी योजनाएं</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="h3" component="div" gutterBottom>
              89%
            </Typography>
            <Typography variant="body1">AI Accuracy</Typography>
            <Typography variant="body2">एआई सटीकता</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="h3" component="div" gutterBottom>
              &lt;5s
            </Typography>
            <Typography variant="body1">Response Time</Typography>
            <Typography variant="body2">प्रतिक्रिया समय</Typography>
          </Grid>
        </Grid>
      </Box>

      {/* Multi-Channel Access */}
      <Box sx={{ textAlign: 'center', mb: 8 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Multiple Ways to Access
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Choose the method that works best for you
        </Typography>
        
        <Grid container spacing={2} justifyContent="center" sx={{ mt: 4 }}>
          <Grid size="auto">
            <Button variant="outlined" startIcon={<Phone />}>
              SMS: Send CHECK to 12345
            </Button>
          </Grid>
          <Grid size="auto">
            <Button variant="outlined" startIcon={<Phone />}>
              Call: 1800-XXX-XXXX
            </Button>
          </Grid>
          <Grid size="auto">
            <Button variant="outlined" startIcon={<Help />} onClick={() => navigate('/help')}>
              Help & Support
            </Button>
          </Grid>
        </Grid>
      </Box>

      {/* CTA Section */}
      <Box sx={{ bgcolor: 'grey.100', py: 6, px: 4, borderRadius: 2, textAlign: 'center' }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Ready to discover your benefits?
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Create your profile and find eligible schemes in under 5 minutes
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate('/profile')}
          sx={{ mt: 2 }}
        >
          Create Profile
        </Button>
      </Box>
    </Container>
  );
};

export default HomePage;
