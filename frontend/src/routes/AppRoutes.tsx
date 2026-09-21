import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { AuthLayout } from '../layouts/AuthLayout';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { EmployeesPage } from '../pages/EmployeesPage';
import { EmployeeDetailPage } from '../pages/EmployeeDetailPage';
import { FaceEnrollmentPage } from '../pages/FaceEnrollmentPage';
import { AttendancePage } from '../pages/AttendancePage';
import { AuditLogsPage } from '../pages/AuditLogsPage';
import { OrganizationPage } from '../pages/OrganizationPage';
import { LiveAttendanceKioskPage } from '../pages/LiveAttendanceKioskPage';
import { NotFoundPage } from '../pages/NotFoundPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Auth Route */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Main Enterprise Application Shell Routes */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/employees/:employeeId" element={<EmployeeDetailPage />} />
        <Route path="/employees/:employeeId/enroll" element={<FaceEnrollmentPage />} />
        <Route path="/enroll/:employeeId" element={<FaceEnrollmentPage />} />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route path="/kiosk" element={<LiveAttendanceKioskPage />} />
        <Route path="/attendance/kiosk" element={<Navigate to="/kiosk" replace />} />
        <Route path="/audit-logs" element={<AuditLogsPage />} />
        <Route path="/organization" element={<OrganizationPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};
