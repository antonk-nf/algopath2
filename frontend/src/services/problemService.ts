import { apiClient, ApiClientError } from './apiClient';
import { staticDataService } from './staticDataService';
import type { ProblemPreview, ProblemPreviewResponse } from '../types';

// Check if running in static mode (no API server)
const isStaticMode = (): boolean => {
  if (import.meta.env.VITE_STATIC_MODE === 'true') {
    return true;
  }
  if (import.meta.env.PROD) {
    return true;
  }
  return false;
};

export async function fetchProblemPreview(slug: string, problemData?: { acceptanceRate?: number; topics?: string[] }): Promise<ProblemPreview> {
  // In static mode, load from static preview data
  if (isStaticMode()) {
    try {
      const preview = await staticDataService.loadProblemPreview(slug);
      if (preview) {
        return preview as unknown as ProblemPreview;
      }
    } catch (error) {
      console.warn('Failed to load static preview for', slug, error);
    }

    // Fallback: return placeholder with available data
    const topic_tags = problemData?.topics?.map(t => ({ name: t, slug: t.toLowerCase().replace(/\s+/g, '-') })) || [];
    return {
      title: slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      titleSlug: slug,
      difficulty: 'UNKNOWN',
      content_html: null,
      content_text: null,
      topic_tags,
      ac_rate: problemData?.acceptanceRate ? problemData.acceptanceRate * 100 : undefined,
      likes: undefined,
      dislikes: undefined,
      is_paid_only: false,
      has_solution: false,
      has_video_solution: false,
    } as unknown as ProblemPreview;
  }

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
