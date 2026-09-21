import { useState, useEffect, useCallback } from 'react';
import { healthService } from '../services/healthService';
import { ReadinessResponse } from '../types/api';

export function useReadiness(pollIntervalMs: number = 30000) {
  const [readiness, setReadiness] = useState<ReadinessResponse>({
    status: 'ready',
    ready: true,
    dependencies: {
      database: { status: 'healthy', critical: true },
      milvus: { status: 'healthy', critical: false },
    },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkReadiness = useCallback(async () => {
    try {
      const data = await healthService.getReadiness();
      setReadiness(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Health check failed');
      setReadiness((prev) => ({
        ...prev,
        status: 'not_ready',
        ready: false,
        dependencies: {
          ...prev.dependencies,
          database: { status: 'unavailable', critical: true },
        },
      }));
    }
  }, []);

  useEffect(() => {
    checkReadiness();
    const interval = setInterval(checkReadiness, pollIntervalMs);
    return () => clearInterval(interval);
  }, [checkReadiness, pollIntervalMs]);

  return {
    readiness,
    loading,
    error,
    refetch: checkReadiness,
  };
}
