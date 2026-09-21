import React from 'react';
import { Box, Card, Grid, Skeleton, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({ rows = 5, columns = 5 }) => {
  return (
    <Box sx={{ width: '100%', overflowX: 'auto' }}>
      <Table>
        <TableHead>
          <TableRow>
            {Array.from({ length: columns }).map((_, index) => (
              <TableCell key={index}>
                <Skeleton variant="text" width="60%" height={20} />
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {Array.from({ length: rows }).map((_, rIndex) => (
            <TableRow key={rIndex}>
              {Array.from({ length: columns }).map((_, cIndex) => (
                <TableCell key={cIndex}>
                  <Skeleton variant="rounded" width={cIndex === 0 ? '80%' : '50%'} height={24} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
};

export const DashboardSkeleton: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Grid container spacing={3}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} sm={6} lg={3} key={item}>
            <Card sx={{ p: 2.5 }}>
              <Skeleton variant="text" width="40%" height={20} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="70%" height={40} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="50%" height={16} />
            </Card>
          </Grid>
        ))}
      </Grid>
      <Card sx={{ p: 3 }}>
        <Skeleton variant="text" width="30%" height={28} sx={{ mb: 2 }} />
        <TableSkeleton rows={4} columns={6} />
      </Card>
    </Box>
  );
};

export const LoadingSkeleton = DashboardSkeleton;

