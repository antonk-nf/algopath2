export interface ProblemPreviewTopicTag {
  id?: string;
  name: string;
  slug?: string;
}

export interface ProblemPreview {
  title?: string | null;
  title_slug?: string | null;
  question_id?: string | null;
  difficulty?: string | null;
  likes?: number | null;
  dislikes?: number | null;
  ac_rate?: number | null;
  is_paid_only?: boolean | null;
  has_solution?: boolean | null;
  has_video_solution?: boolean | null;
  freq_bar?: string | null;
  topic_tags?: ProblemPreviewTopicTag[] | null;
  content_html?: string | null;
  content_text?: string | null;
  metadata_fetched_at?: string | null;
}

export interface ProblemPreviewResponse {
  preview: ProblemPreview;
}
