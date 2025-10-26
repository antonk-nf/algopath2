import React, { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper
} from '@mui/material';
import { CompanyCard } from './CompanyCard';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import type { CompanyData } from '../../types/company';

interface CompanyListProps {
  companies: CompanyData[];
  loading: boolean;
  error: string | null;
  onCompanyClick?: (companyName: string) => void;
  onRetry?: () => void;
}

const ITEMS_PER_PAGE_OPTIONS = [12, 24, 48, 96];

export function CompanyList({
  companies,
  loading,
  error,
  onCompanyClick,
  onRetry
}: CompanyListProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(24);

  // Calculate pagination
  const totalPages = Math.ceil(companies.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentCompanies = companies.slice(startIndex, endIndex);

  const handlePageChange = (_event: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (event: any) => {
    setItemsPerPage(event.target.value);
    setCurrentPage(1); // Reset to first page
  };

  // Loading state
  if (loading && companies.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <LoadingSpinner message="Loading company data..." size={60} />
      </Box>
    );
  }

  // Error state
  if (error && companies.length === 0) {
    return (
      <Box sx={{ py: 4 }}>
        <ErrorMessage
          title="Failed to Load Companies"
          message={error}
          onRetry={onRetry}
          variant="card"
        />
      </Box>
    );
  }

  // No companies found
  if (!loading && companies.length === 0) {
    return (
      <Paper sx={{ p: 6, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Companies Found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Try adjusting your search criteria or filters to find companies.
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Error banner for partial failures */}
      {error && companies.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Some company data may be incomplete due to API issues: {error}
          </Typography>
        </Alert>
      )}

      {/* Pagination Controls - Top */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 3,
        flexWrap: 'wrap',
        gap: 2
      }}>
        <Typography variant="body1" color="text.secondary">
          Showing {startIndex + 1}-{Math.min(endIndex, companies.length)} of {companies.length} companies
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Per Page</InputLabel>
            <Select
              value={itemsPerPage}
              label="Per Page"
              onChange={handleItemsPerPageChange}
            >
              {ITEMS_PER_PAGE_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {totalPages > 1 && (
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={handlePageChange}
              color="primary"
              size="small"
            />
          )}
        </Box>
      </Box>

      {/* Company Grid */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { 
          xs: '1fr', 
          sm: '1fr 1fr', 
          md: '1fr 1fr 1fr', 
          lg: '1fr 1fr 1fr 1fr' 
        }, 
        gap: 3 
      }}>
        {currentCompanies.map((company) => (
          <CompanyCard
            key={company.company}
            company={company}
            onClick={onCompanyClick}
          />
        ))}
      </Box>

      {/* Loading overlay for additional data */}
      {loading && companies.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <LoadingSpinner message="Updating company data..." />
        </Box>
      )}

      {/* Pagination Controls - Bottom */}
      {totalPages > 1 && (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          mt: 4 
        }}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={handlePageChange}
            color="primary"
            size="large"
            showFirstButton
            showLastButton
          />
        </Box>
      )}
    </Box>
  );
}