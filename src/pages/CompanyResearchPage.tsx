
import { useState } from 'react';
import { 
  Box, 
  Typography, 
  Alert
} from '@mui/material';
import { 
  Business as BusinessIcon
} from '@mui/icons-material';
import { 
  CompanyList, 
  CompanyFilters, 
  CompanyDetail 
} from '../components/Company';
import { ExportMenu } from '../components/Common/ExportMenu';
import { useCompanyData, useCompanyDetails } from '../hooks/useCompanyData';
import type { CompanyFilterCriteria } from '../types/company';

export function CompanyResearchPage() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  
  const {
    filteredCompanies,
    stats,
    loading,
    error,
    refetch,
    applyFilters,
    clearFilters,
    currentFilters
  } = useCompanyData();

  const {
    company: companyDetails,
    loading: detailsLoading,
    error: detailsError,
    refetch: refetchDetails
  } = useCompanyDetails(selectedCompany);

  const handleCompanyClick = (companyName: string) => {
    setSelectedCompany(companyName);
  };

  const handleBackToList = () => {
    setSelectedCompany(null);
  };

  const handleFiltersChange = (filters: CompanyFilterCriteria) => {
    applyFilters(filters);
  };

  // Show company detail view
  if (selectedCompany) {
    return (
      <CompanyDetail
        company={companyDetails}
        loading={detailsLoading}
        error={detailsError}
        onBack={handleBackToList}
        onRetry={refetchDetails}
      />
    );
  }

  // Show company list view
  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <BusinessIcon sx={{ mr: 1, fontSize: 32 }} />
          <Typography variant="h4" component="h1">
            Company Research
          </Typography>
        </Box>
        <ExportMenu
          data={filteredCompanies}
          dataType="companies"
          buttonText="Export Companies"
          disabled={loading || filteredCompanies.length === 0}
        />
      </Box>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Analyze interview patterns and problem statistics from top tech companies. 
        Get insights into difficulty distributions, popular topics, and recent trends.
      </Typography>

      {/* API Status Alert */}
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>API Notice:</strong> {error}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            The company endpoints may be experiencing issues. Some features might be limited.
          </Typography>
        </Alert>
      )}

      {/* Filters */}
      <CompanyFilters
        filters={currentFilters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={clearFilters}
        totalCompanies={stats.totalCompanies}
        filteredCount={filteredCompanies.length}
      />

      {/* Company List */}
      <CompanyList
        companies={filteredCompanies}
        loading={loading}
        error={error}
        onCompanyClick={handleCompanyClick}
        onRetry={refetch}
      />
    </Box>
  );
}
