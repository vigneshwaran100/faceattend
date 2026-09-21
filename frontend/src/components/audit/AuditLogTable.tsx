import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Typography,
  Chip,
  TablePagination,
} from '@mui/material';
import { AuditLogRecord } from '../../services/types';
import { StatusChip } from '../common/StatusChip';
import { EmptyState } from '../common/EmptyState';

interface AuditLogTableProps {
  logs: AuditLogRecord[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newPageSize: number) => void;
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({
  logs,
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}) => {
  if (logs.length === 0) {
    return (
      <EmptyState
        title="No Audit Logs Found"
        description="No scanner telemetry or security audit records match your current filter parameters."
      />
    );
  }

  return (
    <Paper variant="outlined" sx={{ borderRadius: 3, overflow: 'hidden' }}>
      <TableContainer>
        <Table sx={{ minWidth: 800 }}>
          <TableHead>
            <TableRow>
              <TableCell>Log ID</TableCell>
              <TableCell>Timestamp</TableCell>
              <TableCell>Scanner Node</TableCell>
              <TableCell>Event Type</TableCell>
              <TableCell>Employee / Target</TableCell>
              <TableCell>Similarity</TableCell>
              <TableCell>Result</TableCell>
              <TableCell>Audit Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.log_id} hover>
                <TableCell>
                  <Typography variant="caption" sx={{ fontFamily: 'monospace', fontWeight: 600, color: 'text.secondary' }}>
                    #{log.log_id}
                  </Typography>
                </TableCell>

                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </Typography>
                </TableCell>

                <TableCell>
                  <Chip
                    size="small"
                    label={log.scanner_type}
                    sx={{
                      backgroundColor: log.scanner_type === 'CHECK_IN' ? '#EFF6FF' : log.scanner_type === 'CHECK_OUT' ? '#F5F3FF' : '#F1F5F9',
                      color: log.scanner_type === 'CHECK_IN' ? '#1E40AF' : log.scanner_type === 'CHECK_OUT' ? '#5B21B6' : '#334155',
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      fontSize: '0.7rem',
                    }}
                  />
                </TableCell>

                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace', fontSize: '0.8125rem' }}>
                    {log.event_type}
                  </Typography>
                </TableCell>

                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: log.employee_id ? 600 : 400, color: log.employee_id ? '#0F172A' : '#94A3B8' }}>
                    {log.employee_id || '—'}
                  </Typography>
                </TableCell>

                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: 'monospace',
                      fontWeight: 600,
                      color: log.similarity && log.similarity >= 0.6 ? '#065F46' : 'text.secondary',
                    }}
                  >
                    {log.similarity !== null && log.similarity !== undefined
                      ? `${(log.similarity * 100).toFixed(1)}%`
                      : '—'}
                  </Typography>
                </TableCell>

                <TableCell>
                  <StatusChip status={log.status} />
                </TableCell>

                <TableCell>
                  <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {log.message}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={total}
        page={page - 1}
        onPageChange={(_, p) => onPageChange(p + 1)}
        rowsPerPage={pageSize}
        onRowsPerPageChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
        rowsPerPageOptions={[10, 20, 50, 100]}
        sx={{ borderTop: '1px solid #E2E8F0' }}
      />
    </Paper>
  );
};
