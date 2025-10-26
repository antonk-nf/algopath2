import React from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import { useAppContext } from '../../hooks/useAppContext';
import { PageContainer } from './PageContainer';

const navigationTabs = [
  { value: 'overview', label: 'Overview' },
  { value: 'company', label: 'Company Research' },
  { value: 'study', label: 'Study Planner' },
] as const;

export function Navigation() {
  const { state, dispatch } = useAppContext();

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    dispatch({
      type: 'SET_CURRENT_VIEW',
      payload: newValue as typeof state.currentView,
    });
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <PageContainer>
        <Tabs
          value={state.currentView}
          onChange={handleTabChange}
          aria-label="navigation tabs"
          sx={{ minHeight: 48 }}
        >
          {navigationTabs.map((tab) => (
            <Tab
              key={tab.value}
              label={tab.label}
              value={tab.value}
              sx={{ textTransform: 'none', minHeight: 48 }}
            />
          ))}
        </Tabs>
      </PageContainer>
    </Box>
  );
}
