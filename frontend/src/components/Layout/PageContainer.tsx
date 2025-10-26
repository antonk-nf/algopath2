import { Box, type BoxProps } from '@mui/material';

interface PageContainerProps extends BoxProps {
  maxWidth?: string | number;
}

export function PageContainer({
  children,
  maxWidth = '1400px',
  sx,
  ...boxProps
}: PageContainerProps) {
  return (
    <Box
      sx={{
        maxWidth,
        width: '100%',
        mx: 'auto',
        px: { xs: 2, md: 3 },
        ...sx
      }}
      {...boxProps}
    >
      {children}
    </Box>
  );
}
