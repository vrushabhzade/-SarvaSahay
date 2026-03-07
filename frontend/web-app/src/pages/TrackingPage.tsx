import React from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';

const TrackingPage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>Track Applications</Typography>
          <Typography>Application tracking coming soon...</Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default TrackingPage;
