import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Box, Typography, useTheme } from '@mui/material';
import type { CompanyData } from '../../types/company';

interface CompanyStatsChartProps {
  companies: CompanyData[];
  height?: number;
  maxCompanies?: number;
}

export function CompanyStatsChart({ 
  companies, 
  height = 300, 
  maxCompanies = 10 
}: CompanyStatsChartProps) {
  const theme = useTheme();

  // Prepare data for the chart - top companies by total problems
  const chartData = [...companies]
    .sort((a, b) => (b.totalProblems ?? 0) - (a.totalProblems ?? 0))
    .slice(0, maxCompanies)
    .map(company => ({
      company: company.company.length > 12 ? `${company.company.substring(0, 12)}...` : company.company,
      fullName: company.company,
      totalProblems: company.totalProblems ?? 0,
      uniqueProblems: company.uniqueProblems ?? 0,
      avgFrequency: company.avgFrequency ?? 0
    }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box
          sx={{
            backgroundColor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            p: 1.5,
            boxShadow: 2,
            minWidth: 200
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
            {data.fullName}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Problems: {data.totalProblems}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Unique Problems: {data.uniqueProblems}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Avg Frequency: {data.avgFrequency.toFixed(1)}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  if (companies.length === 0) {
    return (
      <Box 
        sx={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}
      >
        <Typography variant="body2" color="text.secondary">
          No company data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 60
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
          <XAxis 
            dataKey="company" 
            angle={-45}
            textAnchor="end"
            height={60}
            fontSize={12}
            stroke={theme.palette.text.secondary}
          />
          <YAxis 
            fontSize={12}
            stroke={theme.palette.text.secondary}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="totalProblems" 
            fill={theme.palette.primary.main}
            radius={[4, 4, 0, 0]}
            name="Total Problems"
          />
          <Bar 
            dataKey="uniqueProblems" 
            fill={theme.palette.secondary.main}
            radius={[4, 4, 0, 0]}
            name="Unique Problems"
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
