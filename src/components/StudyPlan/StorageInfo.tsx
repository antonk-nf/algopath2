import { Card, CardContent, Typography, LinearProgress, Box, Button } from '@mui/material';
import { studyPlanService } from '../../services/studyPlanService';

interface StorageInfoProps {
  onExport: () => void;
}

export function StorageInfo({ onExport }: StorageInfoProps) {
  const storage = studyPlanService.getStorageInfo();

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ flex: 1, pr: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Storage Usage (local backup)
            </Typography>
            <LinearProgress
              variant="determinate"
              value={Math.min(storage.percentage, 100)}
              sx={{ height: 8, borderRadius: 4, mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              Used: {storage.used} KB · Available: {Math.max(storage.available, 0)} KB
            </Typography>
          </Box>
          <Button variant="outlined" onClick={onExport}>
            Export Plans
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}
