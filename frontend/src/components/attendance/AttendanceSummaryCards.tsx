import React from 'react';
import { Grid } from '@mui/material';
import {
  EventAvailable as EventAvailableIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  HourglassEmpty as HourglassEmptyIcon,
  HighlightOff as HighlightOffIcon,
  Percent as PercentIcon,
} from '@mui/icons-material';
import { AttendanceSummary } from '../../services/types';
import { MetricCard } from '../common/MetricCard';

interface AttendanceSummaryCardsProps {
  summary: AttendanceSummary;
}

export const AttendanceSummaryCards: React.FC<AttendanceSummaryCardsProps> = ({ summary }) => {
  return (
    <Grid container spacing={2.5}>
      <Grid item xs={12} sm={6} md={2.4}>
        <MetricCard
          title="Total Days"
          value={summary.total_working_days}
          subtitle="Monitored cycle"
          icon={<EventAvailableIcon />}
          accentColor="#4338CA"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={2.4}>
        <MetricCard
          title="Present Days"
          value={summary.present_days}
          subtitle="Full day verified"
          icon={<CheckCircleOutlineIcon />}
          accentColor="#10B981"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={2.4}>
        <MetricCard
          title="Half Days"
          value={summary.half_days}
          subtitle="Partial duration"
          icon={<HourglassEmptyIcon />}
          accentColor="#F59E0B"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={2.4}>
        <MetricCard
          title="Absent Days"
          value={summary.absent_days}
          subtitle="Unaccounted"
          icon={<HighlightOffIcon />}
          accentColor="#EF4444"
        />
      </Grid>

      <Grid item xs={12} sm={6} md={2.4}>
        <MetricCard
          title="Attendance Score"
          value={`${summary.attendance_percentage.toFixed(1)}%`}
          subtitle={`${summary.total_working_hours.toFixed(1)} total hrs`}
          icon={<PercentIcon />}
          accentColor="#6366F1"
        />
      </Grid>
    </Grid>
  );
};
