import React from 'react';
import { Container, Typography, Paper, Box, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { ExpandMore } from '@mui/icons-material';

const HelpPage: React.FC = () => {
  const faqs = [
    {
      question: 'What is SarvaSahay?',
      answer: 'SarvaSahay is an AI-powered platform that helps rural Indian citizens discover and apply for government schemes they are eligible for.',
    },
    {
      question: 'How do I check my eligibility?',
      answer: 'Create your profile with basic information, and our AI will match you with eligible government schemes in under 5 seconds.',
    },
    {
      question: 'Is this service free?',
      answer: 'Yes, SarvaSahay is completely free for all citizens.',
    },
    {
      question: 'Which languages are supported?',
      answer: 'We support English, Hindi (हिंदी), and Marathi (मराठी).',
    },
  ];

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>Help & Support</Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          सहायता और समर्थन
        </Typography>

        <Paper sx={{ p: 4, mb: 4 }}>
          <Typography variant="h6" gutterBottom>Frequently Asked Questions</Typography>
          {faqs.map((faq, index) => (
            <Accordion key={index}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>{faq.question}</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography color="text.secondary">{faq.answer}</Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Paper>

        <Paper sx={{ p: 4 }}>
          <Typography variant="h6" gutterBottom>Contact Support</Typography>
          <Typography>Phone: 1800-XXX-XXXX (Toll Free)</Typography>
          <Typography>Email: support@sarvasahay.gov.in</Typography>
          <Typography>SMS: Send HELP to 12345</Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default HelpPage;
