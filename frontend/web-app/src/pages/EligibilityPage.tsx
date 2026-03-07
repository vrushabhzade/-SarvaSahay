import React from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';

const EligibilityPage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>Check Eligibility</Typography>
          <Typography>Eligibility checker coming soon...</Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default EligibilityPage;
