import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Autocomplete,
  FormHelperText,
  Alert,
  Slider,
  Stack
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import type { StudyPlanFormData, CompanyData } from '../../types';
import { studyPlanService } from '../../services/studyPlanService';

interface StudyPlanFormProps {
  companies: CompanyData[];
  onSubmit: (formData: StudyPlanFormData) => void;
  loading?: boolean;
}

export function StudyPlanForm({ companies, onSubmit, loading = false }: StudyPlanFormProps) {
  const [formData, setFormData] = useState<StudyPlanFormData>({
    name: '',
    targetCompanies: [],
    duration: 8, // weeks
    dailyGoal: 2, // problems per day
    skillLevel: 'intermediate',
    focusAreas: [],
    startDate: new Date().toISOString().split('T')[0],
    learningMode: 'balanced',
    qualityPreference: 'balanced',
    adaptiveDifficulty: true,
    includeQualityMetrics: true
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [focusAreaOptions] = useState(studyPlanService.getRecommendedFocusAreas());

  // Popular companies for quick selection
  const popularCompanies = ['Google', 'Amazon', 'Microsoft', 'Meta', 'Apple', 'Netflix'];
  const availableCompanies = companies.map(c => c.company).sort();

  const handleInputChange = (field: keyof StudyPlanFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Study plan name is required';
    }

    if (formData.targetCompanies.length === 0) {
      newErrors.targetCompanies = 'Please select at least one target company';
    }

    if (formData.duration < 1 || formData.duration > 52) {
      newErrors.duration = 'Duration must be between 1 and 52 weeks';
    }

    if (formData.dailyGoal < 1 || formData.dailyGoal > 10) {
      newErrors.dailyGoal = 'Daily goal must be between 1 and 10 problems';
    }

    if (!formData.startDate) {
      newErrors.startDate = 'Start date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleQuickCompanySelect = (companyGroup: string[]) => {
    const availableFromGroup = companyGroup.filter(company => 
      availableCompanies.includes(company)
    );
    handleInputChange('targetCompanies', availableFromGroup);
  };

  const totalProblems = formData.duration * 7 * formData.dailyGoal;
  const estimatedHours = totalProblems * 0.75; // Assuming 45 minutes per problem

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Create Study Plan
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Generate a personalized study plan based on your target companies and preparation timeline.
          </Typography>

          <Box component="form" onSubmit={handleSubmit}>
            <Stack spacing={3}>
              {/* Study Plan Name */}
              <TextField
                fullWidth
                label="Study Plan Name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                error={!!errors.name}
                helperText={errors.name}
                placeholder="e.g., FAANG Prep - Winter 2024"
              />

              {/* Target Companies */}
              <FormControl fullWidth error={!!errors.targetCompanies}>
                <Autocomplete
                  multiple
                  options={availableCompanies}
                  value={formData.targetCompanies}
                  onChange={(_, newValue) => handleInputChange('targetCompanies', newValue)}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={option}
                        {...getTagProps({ index })}
                        key={option}
                      />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Target Companies"
                      placeholder="Select companies..."
                      error={!!errors.targetCompanies}
                    />
                  )}
                />
                {errors.targetCompanies && (
                  <FormHelperText>{errors.targetCompanies}</FormHelperText>
                )}
              </FormControl>

              {/* Quick Selection Buttons */}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => handleQuickCompanySelect(popularCompanies)}
                >
                  FAANG
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => handleQuickCompanySelect(['Google', 'Amazon', 'Microsoft'])}
                >
                  Big Tech
                </Button>
              </Box>

              {/* Duration and Daily Goal */}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
                <Box>
                  <Typography gutterBottom>
                    Study Duration: {formData.duration} weeks
                  </Typography>
                  <Slider
                    value={formData.duration}
                    onChange={(_, value) => handleInputChange('duration', value)}
                    min={1}
                    max={24}
                    step={1}
                    marks={[
                      { value: 4, label: '1 month' },
                      { value: 8, label: '2 months' },
                      { value: 12, label: '3 months' },
                      { value: 24, label: '6 months' }
                    ]}
                    valueLabelDisplay="auto"
                  />
                  {errors.duration && (
                    <FormHelperText error>{errors.duration}</FormHelperText>
                  )}
                </Box>

                <Box>
                  <Typography gutterBottom>
                    Daily Goal: {formData.dailyGoal} problems/day
                  </Typography>
                  <Slider
                    value={formData.dailyGoal}
                    onChange={(_, value) => handleInputChange('dailyGoal', value)}
                    min={1}
                    max={5}
                    step={1}
                    marks={[
                      { value: 1, label: '1' },
                      { value: 2, label: '2' },
                      { value: 3, label: '3' },
                      { value: 4, label: '4' },
                      { value: 5, label: '5' }
                    ]}
                    valueLabelDisplay="auto"
                  />
                  {errors.dailyGoal && (
                    <FormHelperText error>{errors.dailyGoal}</FormHelperText>
                  )}
                </Box>
              </Box>

              {/* Skill Level and Start Date */}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
                <FormControl fullWidth>
                  <InputLabel>Skill Level</InputLabel>
                  <Select
                    value={formData.skillLevel}
                    label="Skill Level"
                    onChange={(e) => handleInputChange('skillLevel', e.target.value)}
                  >
                    <MenuItem value="beginner">
                      Beginner - Focus on Easy problems
                    </MenuItem>
                    <MenuItem value="intermediate">
                      Intermediate - Mix of Easy/Medium problems
                    </MenuItem>
                    <MenuItem value="advanced">
                      Advanced - Focus on Medium/Hard problems
                    </MenuItem>
                  </Select>
                </FormControl>

                <DatePicker
                  label="Start Date"
                  value={new Date(formData.startDate)}
                  onChange={(date) => 
                    handleInputChange('startDate', date?.toISOString().split('T')[0] || '')
                  }
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.startDate,
                      helperText: errors.startDate
                    }
                  }}
                />
              </Box>

              {/* Focus Areas */}
              <Autocomplete
                multiple
                options={focusAreaOptions}
                value={formData.focusAreas}
                onChange={(_, newValue) => handleInputChange('focusAreas', newValue)}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      size="small"
                      {...getTagProps({ index })}
                      key={option}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Focus Areas (Optional)"
                    placeholder="Select topics to prioritize..."
                  />
                )}
              />

              {/* Learning Mode Selection */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Learning Mode
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>Learning Approach</InputLabel>
                    <Select
                      value={formData.learningMode || 'balanced'}
                      label="Learning Approach"
                      onChange={(e) => handleInputChange('learningMode', e.target.value)}
                    >
                      <MenuItem value="balanced">
                        Balanced Learning - Mix of classics and discoveries
                      </MenuItem>
                      <MenuItem value="interview_classics">
                        Interview Classics - Focus on most-liked problems
                      </MenuItem>
                      <MenuItem value="hidden_gems">
                        Hidden Gems - Discover high-quality, less-known problems
                      </MenuItem>
                      <MenuItem value="adaptive">
                        Adaptive - Smart progression based on performance
                      </MenuItem>
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>Quality Preference</InputLabel>
                    <Select
                      value={formData.qualityPreference || 'balanced'}
                      label="Quality Preference"
                      onChange={(e) => handleInputChange('qualityPreference', e.target.value)}
                    >
                      <MenuItem value="balanced">
                        Balanced - Quality and popularity mix
                      </MenuItem>
                      <MenuItem value="quality_first">
                        Quality First - Highest originality scores
                      </MenuItem>
                      <MenuItem value="popularity_first">
                        Popularity First - Most-liked problems
                      </MenuItem>
                      <MenuItem value="discovery">
                        Discovery Mode - Emphasize hidden gems
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </Box>

              {/* Advanced Options */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Advanced Options
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant={formData.adaptiveDifficulty ? 'contained' : 'outlined'}
                    size="small"
                    onClick={() => handleInputChange('adaptiveDifficulty', !formData.adaptiveDifficulty)}
                  >
                    Adaptive Difficulty Progression
                  </Button>
                  <Button
                    variant={formData.includeQualityMetrics ? 'contained' : 'outlined'}
                    size="small"
                    onClick={() => handleInputChange('includeQualityMetrics', !formData.includeQualityMetrics)}
                  >
                    Include Quality Metrics
                  </Button>
                </Box>
              </Box>

              {/* Study Plan Summary */}
              <Alert severity="info">
                <Typography variant="subtitle2" gutterBottom>
                  Study Plan Summary
                </Typography>
                <Stack spacing={0.5}>
                  <Typography variant="body2">
                    • Total Problems: {totalProblems}
                  </Typography>
                  <Typography variant="body2">
                    • Estimated Time: ~{Math.round(estimatedHours)} hours
                  </Typography>
                  <Typography variant="body2">
                    • Companies: {formData.targetCompanies.length} selected
                  </Typography>
                  <Typography variant="body2">
                    • Duration: {formData.duration} weeks ({formData.duration * 7} days)
                  </Typography>
                  <Typography variant="body2">
                    • Learning Mode: {formData.learningMode?.replace('_', ' ') || 'Balanced'}
                  </Typography>
                  <Typography variant="body2">
                    • Quality Focus: {formData.qualityPreference?.replace('_', ' ') || 'Balanced'}
                  </Typography>
                  {formData.adaptiveDifficulty && (
                    <Typography variant="body2">
                      • ✓ Adaptive difficulty progression enabled
                    </Typography>
                  )}
                  {formData.includeQualityMetrics && (
                    <Typography variant="body2">
                      • ✓ Quality metrics and recommendations included
                    </Typography>
                  )}
                </Stack>
              </Alert>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={loading}
                sx={{ mt: 2 }}
              >
                {loading ? 'Generating Study Plan...' : 'Generate Study Plan'}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </LocalizationProvider>
  );
}