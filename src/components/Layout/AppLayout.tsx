import React from 'react';
import { Box, AppBar, Toolbar, Typography } from '@mui/material';
import { Navigation } from './Navigation';
import { HealthIndicator } from './HealthIndicator';
import { PageContainer } from './PageContainer';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header */}
      <AppBar position="static" color="primary" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
            Interview Prep Dashboard
          </Typography>
          <HealthIndicator />
        </Toolbar>
      </AppBar>

      {/* Navigation */}
      <Navigation />

      {/* Main Content Area */}
      <Box sx={{ flex: 1, py: 3 }}>
        <PageContainer component="main" role="main">
          {children}
        </PageContainer>
      </Box>
    </Box>
  );
}
