import { useAppContext } from './useAppContext';

// Helper hooks for specific state slices
export function useApiHealth() {
  const { state } = useAppContext();
  return state.apiHealth;
}

export function useLoading(key: string) {
  const { state } = useAppContext();
  return state.loading[key] || false;
}

export function useError(key: string) {
  const { state } = useAppContext();
  return state.errors[key] || null;
}