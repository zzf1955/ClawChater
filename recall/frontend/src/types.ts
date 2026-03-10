export interface ScreenshotItem {
  id: number;
  captured_at: string;
  file_path: string;
  ocr_text: string | null;
  ocr_status: string;
  window_title: string | null;
  process_name: string | null;
}

export interface SummaryItem {
  id: number;
  start_time: string;
  end_time: string;
  summary: string;
  activity_type: string | null;
  created_at: string;
}
