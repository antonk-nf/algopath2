import { useState, useEffect, useCallback, useMemo } from 'react';
import { companyService } from '../services/companyService';
import type { CompanyData, CompanyFilterCriteria, CompanyStats } from '../types/company';
import { useAppContext } from './useAppContext';

interface UseCompanyDataState {
  companies: CompanyData[];
  filteredCompanies: CompanyData[];
  stats: CompanyStats;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  applyFilters: (criteria: CompanyFilterCriteria) => void;
  clearFilters: () => void;
  currentFilters: CompanyFilterCriteria;
}

export function useCompanyData(): UseCompanyDataState {
  const [companies, setCompanies] = useState<CompanyData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<CompanyFilterCriteria>({
    sortBy: 'totalProblems',
    sortOrder: 'desc'
  });
  
  const { dispatch } = useAppContext();

  const fetchCompanies = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    // Update global loading state
    dispatch({
      type: 'SET_LOADING',
      payload: { key: 'companies', loading: true }
    });

    try {
      const data = await companyService.getCompanyStats();
      setCompanies(data);
      
      // If we got an empty array, it might be due to API issues
      if (data.length === 0) {
        const warningMessage = 'No company data available. The company endpoints may be experiencing issues.';
        setError(warningMessage);
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'companies', error: warningMessage }
        });
      } else {
        // Clear any previous errors if we got data
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'companies', error: null }
        });
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch company data';
      setError(errorMessage);
      
      // Update global error state
      dispatch({
        type: 'SET_ERROR',
        payload: { key: 'companies', error: errorMessage }
      });
      
      console.error('Company data fetch error:', err);
      // Ensure companies is set to empty array on error
      setCompanies([]);
    } finally {
      setLoading(false);
      
      // Update global loading state
      dispatch({
        type: 'SET_LOADING',
        payload: { key: 'companies', loading: false }
      });
    }
  }, [dispatch]);

  // Filter and sort companies based on current criteria
  const filteredCompanies = useMemo(() => {
    // Ensure companies is always an array, even if API fails
    const safeCompanies = Array.isArray(companies) ? companies : [];
    return companyService.filterCompanies(safeCompanies, filters);
  }, [companies, filters]);

  // Calculate statistics
  const stats = useMemo(() => {
    // Ensure filteredCompanies is always an array
    const safeCompanies = Array.isArray(filteredCompanies) ? filteredCompanies : [];
    return companyService.calculateStats(safeCompanies);
  }, [filteredCompanies]);

  const applyFilters = useCallback((criteria: CompanyFilterCriteria) => {
    setFilters(prev => ({ ...prev, ...criteria }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      sortBy: 'totalProblems',
      sortOrder: 'desc'
    });
  }, []);

  // Fetch data on mount
  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  return {
    companies,
    filteredCompanies,
    stats,
    loading,
    error,
    refetch: fetchCompanies,
    applyFilters,
    clearFilters,
    currentFilters: filters
  };
}

// Hook for individual company details
export function useCompanyDetails(companyName: string | null) {
  const [company, setCompany] = useState<CompanyData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { dispatch } = useAppContext();

  const fetchCompanyDetails = useCallback(async (name: string) => {
    setLoading(true);
    setError(null);
    
    const loadingKey = `company-${name}`;
    dispatch({
      type: 'SET_LOADING',
      payload: { key: loadingKey, loading: true }
    });

    try {
      const data = await companyService.getCompanyDetails(name);
      setCompany(data);
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: loadingKey, error: null }
      });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `Failed to fetch details for ${name}`;
      setError(errorMessage);
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: loadingKey, error: errorMessage }
      });
      
    } finally {
      setLoading(false);
      
      dispatch({
        type: 'SET_LOADING',
        payload: { key: loadingKey, loading: false }
      });
    }
  }, [dispatch]);

  useEffect(() => {
    if (companyName) {
      fetchCompanyDetails(companyName);
    } else {
      setCompany(null);
      setError(null);
    }
  }, [companyName, fetchCompanyDetails]);

  return {
    company,
    loading,
    error,
    refetch: companyName ? () => fetchCompanyDetails(companyName) : () => Promise.resolve()
  };
}