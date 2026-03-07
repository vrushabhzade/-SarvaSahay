import React from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';

const ApplicationsPage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>My Applications</Typography>
          <Typography>Application management coming soon...</Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default ApplicationsPage;
