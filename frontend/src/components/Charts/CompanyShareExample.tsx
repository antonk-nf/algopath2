import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

export function CompanyShareExample() {
  // Example data to illustrate "Share of Company" normalization
  const exampleData = {
    topics: ['Arrays', 'Trees', 'Graphs'],
    companies: ['Google', 'Amazon', 'Microsoft'],
    // Raw frequency matrix
    matrix: [
      [100, 50, 30],  // Arrays:  Google=100, Amazon=50, Microsoft=30
      [20, 40, 60],   // Trees:   Google=20,  Amazon=40, Microsoft=60
      [30, 10, 10]    // Graphs:  Google=30,  Amazon=10, Microsoft=10
    ]
  };

  // Calculate company totals
  const companyTotals = exampleData.companies.map((_, companyIndex) => 
    exampleData.topics.reduce((sum, _, topicIndex) => 
      sum + exampleData.matrix[topicIndex][companyIndex], 0
    )
  );

  // Calculate share of company for each cell
  const shareMatrix = exampleData.matrix.map(row => 
    row.map((value, companyIndex) => 
      companyTotals[companyIndex] > 0 ? (value / companyTotals[companyIndex] * 100) : 0
    )
  );

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        "Share of Company" Normalization Example
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        This shows how each topic represents a percentage of each company's total questions.
        Colors are based on these percentages, making it easy to see each company's focus areas.
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {/* Raw Data */}
        <Box sx={{ flex: '1 1 300px' }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
            Raw Frequency Data
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Topic</TableCell>
                  <TableCell align="center">Google</TableCell>
                  <TableCell align="center">Amazon</TableCell>
                  <TableCell align="center">Microsoft</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exampleData.topics.map((topic, topicIndex) => (
                  <TableRow key={topic}>
                    <TableCell sx={{ fontWeight: 500 }}>{topic}</TableCell>
                    {exampleData.matrix[topicIndex].map((value, companyIndex) => (
                      <TableCell key={companyIndex} align="center">
                        {value}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
                <TableRow sx={{ backgroundColor: 'action.hover' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>Company Total</TableCell>
                  {companyTotals.map((total, index) => (
                    <TableCell key={index} align="center" sx={{ fontWeight: 'bold' }}>
                      {total}
                    </TableCell>
                  ))}
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Box>

        {/* Share of Company */}
        <Box sx={{ flex: '1 1 300px' }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
            Share of Company (%)
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Topic</TableCell>
                  <TableCell align="center">Google</TableCell>
                  <TableCell align="center">Amazon</TableCell>
                  <TableCell align="center">Microsoft</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exampleData.topics.map((topic, topicIndex) => (
                  <TableRow key={topic}>
                    <TableCell sx={{ fontWeight: 500 }}>{topic}</TableCell>
                    {shareMatrix[topicIndex].map((percentage, companyIndex) => (
                      <TableCell 
                        key={companyIndex} 
                        align="center"
                        sx={{ 
                          backgroundColor: `rgba(138, 43, 226, ${percentage / 100 * 0.8 + 0.1})`,
                          color: percentage > 50 ? 'white' : 'inherit',
                          fontWeight: percentage > 40 ? 'bold' : 'normal'
                        }}
                      >
                        {percentage.toFixed(1)}%
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Box>

      <Box sx={{ mt: 3, p: 2, backgroundColor: 'info.light', borderRadius: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
          💡 Key Insights from Share of Company View:
        </Typography>
        <Typography variant="body2" component="div">
          • <strong>Google</strong>: 66.7% Arrays, 13.3% Trees, 20% Graphs - Heavy focus on Arrays<br/>
          • <strong>Amazon</strong>: 50% Arrays, 40% Trees, 10% Graphs - Balanced Arrays/Trees<br/>
          • <strong>Microsoft</strong>: 30% Arrays, 60% Trees, 10% Graphs - Strong focus on Trees
        </Typography>
      </Box>
    </Paper>
  );
}