export interface Product {
  product_id: string;
  title: string;
  description: string;
  category: string;
  price: number;
  currency: string;
  material?: string | null;
  colour?: string | null;
  style?: string | null;
  width?: number | null;
  height?: number | null;
  depth?: number | null;
  image_path?: string | null;
  image_url?: string | null;
  availability: boolean;
  source: string;
  created_at?: string | null;
}

export interface ExtractedFilters {
  category?: string | null;
  min_price?: number | null;
  max_price?: number | null;
  colour?: string | null;
  material?: string | null;
  style?: string | null;
  max_width_cm?: number | null;
  min_width_cm?: number | null;
  availability?: boolean | null;
}

export interface SearchResultItem {
  product: Product;
  score: number;
  keyword_score?: number | null;
  semantic_score?: number | null;
  match_explanation: string;
}

export interface SearchResponse {
  query: string;
  search_mode: string;
  extracted_filters: ExtractedFilters;
  applied_filters: Record<string, any>;
  total_matches: number;
  results: SearchResultItem[];
  latency_ms: number;
  suggestions: string[];
}

export interface ImageSearchResultItem {
  product: Product;
  similarity_score: number;
  visual_match_explanation: string;
}

export interface ImageSearchResponse {
  total_matches: number;
  results: ImageSearchResultItem[];
  latency_ms: number;
  encoder_used: string;
}

export interface StatedPreferences {
  category?: string | null;
  budget_max?: number | null;
  preferred_styles: string[];
  preferred_materials: string[];
  preferred_colours: string[];
}

export interface RecommendationItem {
  product: Product;
  recommendation_score: number;
  recommendation_reasons: string[];
  explanation: string;
}

export interface RecommendationResponse {
  user_id: string;
  is_cold_start: boolean;
  total_recommendations: number;
  recommendations: RecommendationItem[];
  strategy_summary: string;
}

export interface AssistantFactItem {
  product_id: string;
  title: string;
  attribute: string;
  value: any;
}

export interface AssistantAskResponse {
  question: string;
  answer: string;
  grounded: boolean;
  structured_evidence: AssistantFactItem[];
  referenced_products: Product[];
  missing_data_notes?: string | null;
  used_llm: boolean;
}

export interface MetricSet {
  precision_at_5: number;
  recall_at_5: number;
  ndcg_at_5: number;
  mrr: number;
  empty_result_rate: number;
}

export interface QueryEvaluationResult {
  query_id: string;
  query: string;
  query_type: string;
  ground_truth_count: number;
  retrieved_count: number;
  precision_at_5: number;
  recall_at_5: number;
  ndcg_at_5: number;
}

export interface EvaluationResponse {
  total_queries: number;
  comparison: {
    keyword: MetricSet;
    semantic: MetricSet;
    hybrid: MetricSet;
  };
  query_details: QueryEvaluationResult[];
  analysis_notes: string;
  timestamp: string;
}

export interface ActiveFilters {
  category?: string;
  min_price?: number;
  max_price?: number;
  material?: string;
  colour?: string;
  style?: string;
  max_width?: number;
  availability?: boolean;
}
