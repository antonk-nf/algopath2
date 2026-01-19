import React, { useState, useMemo } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Download as DownloadIcon,
  FileDownload as FileDownloadIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { ExportService, type BookmarkedProblem } from '../services/exportService';
import BookmarkButton from '../components/Common/BookmarkButton';
import { PageContainer } from '../components/Layout';

const BookmarksPage: React.FC = () => {
  const [bookmarks, setBookmarks] = useState<BookmarkedProblem[]>(
    ExportService.getBookmarkedProblems()
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [problemToDelete, setProblemToDelete] = useState<string | null>(null);

  // Get all unique tags from bookmarks
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    bookmarks.forEach(bookmark => {
      bookmark.tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [bookmarks]);

  // Filter bookmarks based on search and filters
  const filteredBookmarks = useMemo(() => {
    return bookmarks.filter(bookmark => {
      const matchesSearch = searchQuery === '' || 
        bookmark.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        bookmark.topics.some(topic => topic.toLowerCase().includes(searchQuery.toLowerCase())) ||
        bookmark.company.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesPriority = priorityFilter === 'all' || bookmark.priority === priorityFilter;
      const matchesDifficulty = difficultyFilter === 'all' || bookmark.difficulty === difficultyFilter;
      const matchesTag = selectedTag === 'all' || bookmark.tags?.includes(selectedTag);

      return matchesSearch && matchesPriority && matchesDifficulty && matchesTag;
    });
  }, [bookmarks, searchQuery, priorityFilter, difficultyFilter, selectedTag]);

  const handleDeleteBookmark = (problemTitle: string) => {
    setProblemToDelete(problemTitle);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (problemToDelete) {
      ExportService.removeBookmark(problemToDelete);
      setBookmarks(ExportService.getBookmarkedProblems());
      setDeleteDialogOpen(false);
      setProblemToDelete(null);
    }
  };

  const handleBookmarkChange = () => {
    setBookmarks(ExportService.getBookmarkedProblems());
  };

  const handleExportJSON = () => {
    ExportService.exportBookmarks();
  };

  const handleExportCSV = () => {
    ExportService.exportBookmarksToCSV();
  };

  const clearAllFilters = () => {
    setSearchQuery('');
    setPriorityFilter('all');
    setDifficultyFilter('all');
    setSelectedTag('all');
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'EASY': return 'success';
      case 'MEDIUM': return 'warning';
      case 'HARD': return 'error';
      default: return 'default';
    }
  };

  return (
    <PageContainer maxWidth="1200px" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Bookmarked Problems
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your saved problems with notes, tags, and quality metrics
        </Typography>
      </Box>

      {/* Export Actions */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleExportJSON}
          disabled={bookmarks.length === 0}
        >
          Export JSON
        </Button>
        <Button
          variant="outlined"
          startIcon={<FileDownloadIcon />}
          onClick={handleExportCSV}
          disabled={bookmarks.length === 0}
        >
          Export CSV
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <Box sx={{ minWidth: 200, flex: 1 }}>
              <TextField
                fullWidth
                label="Search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
                size="small"
              />
            </Box>
            <Box sx={{ minWidth: 120 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Priority</InputLabel>
                <Select
                  value={priorityFilter}
                  label="Priority"
                  onChange={(e) => setPriorityFilter(e.target.value)}
                >
                  <MenuItem value="all">All Priorities</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ minWidth: 120 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Difficulty</InputLabel>
                <Select
                  value={difficultyFilter}
                  label="Difficulty"
                  onChange={(e) => setDifficultyFilter(e.target.value)}
                >
                  <MenuItem value="all">All Difficulties</MenuItem>
                  <MenuItem value="EASY">Easy</MenuItem>
                  <MenuItem value="MEDIUM">Medium</MenuItem>
                  <MenuItem value="HARD">Hard</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ minWidth: 120 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Tag</InputLabel>
                <Select
                  value={selectedTag}
                  label="Tag"
                  onChange={(e) => setSelectedTag(e.target.value)}
                >
                  <MenuItem value="all">All Tags</MenuItem>
                  {allTags.map(tag => (
                    <MenuItem key={tag} value={tag}>{tag}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            <Box>
              <Button
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={clearAllFilters}
                size="small"
              >
                Clear Filters
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredBookmarks.length} of {bookmarks.length} bookmarked problems
        </Typography>
      </Box>

      {/* Bookmarks List */}
      {filteredBookmarks.length === 0 ? (
        <Alert severity="info">
          {bookmarks.length === 0 
            ? "No bookmarked problems yet. Start bookmarking problems to build your collection!"
            : "No problems match your current filters. Try adjusting your search criteria."
          }
        </Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {filteredBookmarks.map((bookmark) => (
            <Box key={bookmark.title}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" component="h3" gutterBottom>
                        {bookmark.title}
                        {bookmark.link && (
                          <Tooltip title="Open problem">
                            <IconButton
                              size="small"
                              onClick={() => window.open(bookmark.link, '_blank')}
                              sx={{ ml: 1 }}
                            >
                              <LinkIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                        <Chip
                          label={bookmark.difficulty}
                          color={getDifficultyColor(bookmark.difficulty)}
                          size="small"
                        />
                        <Chip
                          label={bookmark.priority || 'medium'}
                          color={getPriorityColor(bookmark.priority)}
                          size="small"
                        />
                        {bookmark.qualityTier && (
                          <Chip
                            label={bookmark.qualityTier}
                            variant="outlined"
                            size="small"
                          />
                        )}
                      </Box>

                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Company:</strong> {bookmark.company} • 
                        <strong> Topics:</strong> {bookmark.topics.join(', ')}
                      </Typography>

                      {bookmark.originalityScore && (
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Quality:</strong> {bookmark.likes} likes, {bookmark.dislikes} dislikes 
                          (Score: {bookmark.originalityScore.toFixed(3)})
                        </Typography>
                      )}

                      {bookmark.notes && (
                        <Typography variant="body2" sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                          <strong>Notes:</strong> {bookmark.notes}
                        </Typography>
                      )}

                      {bookmark.tags && bookmark.tags.length > 0 && (
                        <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {bookmark.tags.map(tag => (
                            <Chip key={tag} label={tag} size="small" variant="outlined" />
                          ))}
                        </Box>
                      )}

                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                        Bookmarked on {new Date(bookmark.bookmarkedAt).toLocaleDateString()}
                      </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <BookmarkButton
                        problem={bookmark}
                        onBookmarkChange={handleBookmarkChange}
                      />
                      <Tooltip title="Delete bookmark">
                        <IconButton
                          color="error"
                          onClick={() => handleDeleteBookmark(bookmark.title)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          ))}
        </Box>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Bookmark</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this bookmark? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
};

export default BookmarksPage;
