import { apiClient, ApiClientError } from './apiClient';
import type { ProblemPreview, ProblemPreviewResponse } from '../types';

export async function fetchProblemPreview(slug: string): Promise<ProblemPreview> {
  try {
    const response = await apiClient.get<ProblemPreviewResponse>(`/api/v1/problems/${slug}/preview`);
    return response.data.preview;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }

    throw new ApiClientError(
      'NETWORK_ERROR',
      error instanceof Error ? error.message : 'Failed to fetch problem preview'
    );
  }
}
