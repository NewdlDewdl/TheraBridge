import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { Patient } from '@/lib/types';

// SWR configuration for patient data - prevents duplicate requests
const patientSWRConfig = {
  // Prevent duplicate requests within 5 minutes (patient data doesn't change often)
  dedupingInterval: 300000,
  // Don't revalidate on focus to avoid unnecessary refetches
  revalidateOnFocus: false,
  // Revalidate on reconnect for network resilience
  revalidateOnReconnect: true,
};

export function usePatients() {
  const { data, error, mutate, isLoading } = useSWR<Patient[]>(
    '/api/patients/',
    fetcher,
    patientSWRConfig
  );

  return {
    patients: data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}

export function usePatient(patientId: string | null) {
  const { data, error, mutate, isLoading } = useSWR<Patient>(
    patientId ? `/api/patients/${patientId}` : null,
    fetcher,
    patientSWRConfig
  );

  return {
    patient: data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}
