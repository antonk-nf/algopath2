import React, { useState } from 'react';
import {
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography
} from '@mui/material';
import {
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { ExportService } from '../../services/exportService';
import type { ProblemData } from '../../types';

interface BookmarkButtonProps {
  problem: ProblemData;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  onBookmarkChange?: (isBookmarked: boolean) => void;
}

interface BookmarkDialogProps {
  open: boolean;
  onClose: () => void;
  problem: ProblemData;
  existingBookmark?: any;
  onSave: (notes: string, tags: string[], priority: 'high' | 'medium' | 'low') => void;
}

const BookmarkDialog: React.FC<BookmarkDialogProps> = ({
  open,
  onClose,
  problem,
  existingBookmark,
  onSave
}) => {
  const [notes, setNotes] = useState(existingBookmark?.notes || '');
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>(
    existingBookmark?.priority || 'medium'
  );
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>(existingBookmark?.tags || []);

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSave = () => {
    onSave(notes, tags, priority);
    onClose();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTag();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {existingBookmark ? 'Edit Bookmark' : 'Add Bookmark'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary">
            {problem.title} ({problem.difficulty})
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {problem.company} • {problem.topics.join(', ')}
          </Typography>
        </Box>

        <TextField
          fullWidth
          label="Notes"
          multiline
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add your notes about this problem..."
          sx={{ mb: 2 }}
        />

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Priority</InputLabel>
          <Select
            value={priority}
            label="Priority"
            onChange={(e) => setPriority(e.target.value as 'high' | 'medium' | 'low')}
          >
            <MenuItem value="low">Low</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="high">High</MenuItem>
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="Add Tags"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Press Enter to add tags"
          sx={{ mb: 1 }}
        />

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {tags.map((tag) => (
            <Chip
              key={tag}
              label={tag}
              onDelete={() => handleRemoveTag(tag)}
              size="small"
            />
          ))}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          Save Bookmark
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export const BookmarkButton: React.FC<BookmarkButtonProps> = ({
  problem,
  size = 'medium',
  showLabel = false,
  onBookmarkChange
}) => {
  const [isBookmarked, setIsBookmarked] = useState(
    ExportService.isBookmarked(problem.title)
  );
  const [dialogOpen, setDialogOpen] = useState(false);
  const [existingBookmark, setExistingBookmark] = useState<any>(null);

  const handleBookmarkClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (isBookmarked) {
      // If already bookmarked, show edit dialog
      const bookmarks = ExportService.getBookmarkedProblems();
      const bookmark = bookmarks.find(b => b.title === problem.title);
      setExistingBookmark(bookmark);
      setDialogOpen(true);
    } else {
      // If not bookmarked, show add dialog
      setExistingBookmark(null);
      setDialogOpen(true);
    }
  };

  const handleSaveBookmark = (notes: string, tags: string[], priority: 'high' | 'medium' | 'low') => {
    ExportService.addBookmark(problem, notes, tags, priority);
    setIsBookmarked(true);
    onBookmarkChange?.(true);
  };

  const handleRemoveBookmark = (e: React.MouseEvent) => {
    e.stopPropagation();
    ExportService.removeBookmark(problem.title);
    setIsBookmarked(false);
    onBookmarkChange?.(false);
  };

  return (
    <>
      <Tooltip title={isBookmarked ? "Edit bookmark" : "Add bookmark"}>
        <IconButton
          onClick={handleBookmarkClick}
          size={size}
          color={isBookmarked ? "primary" : "default"}
        >
          {isBookmarked ? <BookmarkIcon /> : <BookmarkBorderIcon />}
        </IconButton>
      </Tooltip>

      {showLabel && isBookmarked && (
        <Tooltip title="Remove bookmark">
          <Button
            size="small"
            startIcon={<EditIcon />}
            onClick={handleRemoveBookmark}
            sx={{ ml: 1 }}
          >
            Bookmarked
          </Button>
        </Tooltip>
      )}

      <BookmarkDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        problem={problem}
        existingBookmark={existingBookmark}
        onSave={handleSaveBookmark}
      />
    </>
  );
};

export default BookmarkButton;