import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { AuditLogTable } from '../components/audit/AuditLogTable';
import { AuditFilterToolbar } from '../components/audit/AuditFilterToolbar';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { auditLogService } from '../services/auditLogService';
import { AuditLogRecordResponse } from '../types/api';

export const AuditLogsPage: React.FC = () => {
  const [scannerType, setScannerType] = useState('');
  const [eventType, setEventType] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<AuditLogRecordResponse[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await auditLogService.getLogs({
        employee_id: employeeId || undefined,
        event_type: eventType || undefined,
        scanner_type: scannerType || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        page_size: pageSize,
      });
      setLogs(res.items || []);
      setTotalRecords(res.total || 0);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchLogs();
  }, [scannerType, eventType, employeeId, startDate, endDate, page, pageSize]);

  const handleReset = () => {
    setScannerType('');
    setEventType('');
    setEmployeeId('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  if (loading && logs.length === 0) {
    return <LoadingSkeleton />;
  }

  return (
    <Box>
      {error && (
        <Box sx={{ mb: 3 }}>
          <ErrorAlert
            title="Audit Logs Error"
            message={error}
            onRetry={fetchLogs}
            onClose={() => setError(null)}
          />
        </Box>
      )}

      {/* Top Header */}
      <Box sx={{ mb: 3.5 }}>
        <Typography variant="h2" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
          Scanner Forensics & Security Audit Logs
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Immutable forensic audit trail for biometric scanner verifications, quality rejections, and hardware events
        </Typography>
      </Box>

      {/* Multi-Parameter Filter Toolbar */}
      <AuditFilterToolbar
        scannerType={scannerType}
        eventType={eventType}
        employeeId={employeeId}
        startDate={startDate}
        endDate={endDate}
        onScannerTypeChange={setScannerType}
        onEventTypeChange={setEventType}
        onEmployeeIdChange={setEmployeeId}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        onReset={handleReset}
      />

      {/* Audit Log Table */}
      <AuditLogTable
        logs={logs as any}
        total={totalRecords}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </Box>
  );
};
