import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  Typography,
  Divider
} from '@mui/material';
import {
  Download as DownloadIcon,
  FileDownload as FileDownloadIcon,
  TableChart as TableChartIcon,
  Description as DescriptionIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { ExportService } from '../../services/exportService';
import type { CompanyData, ProblemData, StudyPlan } from '../../types';

interface ExportMenuProps {
  data: CompanyData[] | ProblemData[] | StudyPlan[];
  dataType: 'companies' | 'problems' | 'studyPlans';
  buttonText?: string;
  variant?: 'contained' | 'outlined' | 'text';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
}

interface ExportOptionsDialogProps {
  open: boolean;
  onClose: () => void;
  onExport: (options: { includeQualityMetrics: boolean; format: 'csv' | 'json' }) => void;
  dataType: 'companies' | 'problems' | 'studyPlans';
}

const ExportOptionsDialog: React.FC<ExportOptionsDialogProps> = ({
  open,
  onClose,
  onExport,
  dataType
}) => {
  const [includeQualityMetrics, setIncludeQualityMetrics] = useState(true);
  const [format, setFormat] = useState<'csv' | 'json'>('csv');

  const handleExport = () => {
    onExport({ includeQualityMetrics, format });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Export Options</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Choose your export preferences for {dataType}.
        </Typography>

        {dataType === 'problems' && (
          <FormControlLabel
            control={
              <Checkbox
                checked={includeQualityMetrics}
                onChange={(e) => setIncludeQualityMetrics(e.target.checked)}
              />
            }
            label="Include quality metrics (likes, dislikes, originality score)"
            sx={{ mb: 2 }}
          />
        )}

        <Typography variant="subtitle2" gutterBottom>
          Export Format:
        </Typography>
        <FormControlLabel
          control={
            <Checkbox
              checked={format === 'csv'}
              onChange={() => setFormat('csv')}
            />
          }
          label="CSV (Spreadsheet format)"
        />
        <FormControlLabel
          control={
            <Checkbox
              checked={format === 'json'}
              onChange={() => setFormat('json')}
            />
          }
          label="JSON (Data format)"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleExport} variant="contained">
          Export
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export const ExportMenu: React.FC<ExportMenuProps> = ({
  data,
  dataType,
  buttonText = 'Export',
  variant = 'outlined',
  size = 'medium',
  disabled = false
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [optionsDialogOpen, setOptionsDialogOpen] = useState(false);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleExportWithOptions = (options: { includeQualityMetrics: boolean; format: 'csv' | 'json' }) => {
    switch (dataType) {
      case 'companies':
        if (options.format === 'csv') {
          ExportService.exportCompanyDataToCSV(data as CompanyData[], options);
        } else {
          // JSON export for companies
          const jsonContent = JSON.stringify(data, null, 2);
          const blob = new Blob([jsonContent], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `company-data-${new Date().toISOString().split('T')[0]}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
        break;
      case 'problems':
        if (options.format === 'csv') {
          ExportService.exportProblemsToCSV(data as ProblemData[], options);
        } else {
          // JSON export for problems
          const jsonContent = JSON.stringify(data, null, 2);
          const blob = new Blob([jsonContent], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `problems-data-${new Date().toISOString().split('T')[0]}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
        break;
      case 'studyPlans':
        if (data.length === 1) {
          ExportService.exportStudyPlan(data[0] as StudyPlan);
        } else {
          ExportService.exportMultipleStudyPlans(data as StudyPlan[]);
        }
        break;
    }
  };

  const handleQuickExportCSV = () => {
    handleExportWithOptions({ includeQualityMetrics: true, format: 'csv' });
    handleClose();
  };

  const handleQuickExportJSON = () => {
    handleExportWithOptions({ includeQualityMetrics: true, format: 'json' });
    handleClose();
  };

  const handlePrintView = () => {
    if (dataType === 'studyPlans' && data.length > 0) {
      const studyPlan = data[0] as StudyPlan;
      const printContent = ExportService.generatePrintableStudyMaterial(studyPlan);
      
      // Create a new window for printing
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>Study Plan - ${studyPlan.name}</title>
              <style>
                body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
                h1, h2 { color: #333; }
                h1 { border-bottom: 2px solid #333; }
                h2 { border-bottom: 1px solid #ccc; }
                strong { font-weight: bold; }
                @media print {
                  body { margin: 0; }
                  .no-print { display: none; }
                }
              </style>
            </head>
            <body>
              <div style="white-space: pre-line;">${printContent}</div>
              <div class="no-print" style="margin-top: 20px;">
                <button onclick="window.print()">Print</button>
                <button onclick="window.close()">Close</button>
              </div>
            </body>
          </html>
        `);
        printWindow.document.close();
      }
    }
    handleClose();
  };

  const handleCustomExport = () => {
    setOptionsDialogOpen(true);
    handleClose();
  };

  return (
    <>
      <Button
        variant={variant}
        size={size}
        startIcon={<DownloadIcon />}
        onClick={handleClick}
        disabled={disabled || data.length === 0}
      >
        {buttonText}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
      >
        <MenuItem onClick={handleQuickExportCSV}>
          <ListItemIcon>
            <TableChartIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Export as CSV</ListItemText>
        </MenuItem>

        <MenuItem onClick={handleQuickExportJSON}>
          <ListItemIcon>
            <FileDownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Export as JSON</ListItemText>
        </MenuItem>

        {dataType === 'studyPlans' && (
          <>
            <Divider />
            <MenuItem onClick={handlePrintView}>
              <ListItemIcon>
                <PrintIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Print Study Material</ListItemText>
            </MenuItem>
          </>
        )}

        <Divider />
        <MenuItem onClick={handleCustomExport}>
          <ListItemIcon>
            <DescriptionIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Custom Export...</ListItemText>
        </MenuItem>
      </Menu>

      <ExportOptionsDialog
        open={optionsDialogOpen}
        onClose={() => setOptionsDialogOpen(false)}
        onExport={handleExportWithOptions}
        dataType={dataType}
      />
    </>
  );
};

export default ExportMenu;