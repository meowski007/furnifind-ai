import {
  Product,
  SearchResponse,
  ImageSearchResponse,
  RecommendationResponse,
  AssistantAskResponse,
  EvaluationResponse,
  ActiveFilters,
  StatedPreferences
} from '../types';

const API_BASE = 'http://localhost:8000';

export async function fetchProducts(params: {
  category?: string;
  min_price?: number;
  max_price?: number;
  material?: string;
  colour?: string;
  style?: string;
  availability?: boolean;
  search?: string;
  sort_by?: string;
  page?: number;
  page_size?: number;
}): Promise<{ total: number; page: number; page_size: number; items: Product[] }> {
  const query = new URLSearchParams();
  if (params.category) query.append('category', params.category);
  if (params.min_price !== undefined) query.append('min_price', params.min_price.toString());
  if (params.max_price !== undefined) query.append('max_price', params.max_price.toString());
  if (params.material) query.append('material', params.material);
  if (params.colour) query.append('colour', params.colour);
  if (params.style) query.append('style', params.style);
  if (params.availability !== undefined) query.append('availability', params.availability.toString());
  if (params.search) query.append('search', params.search);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.page) query.append('page', params.page.toString());
  if (params.page_size) query.append('page_size', params.page_size.toString());

  const res = await fetch(`${API_BASE}/api/v1/products?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch products: ${res.statusText}`);
  return res.json();
}

export async function fetchProductById(productId: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/api/v1/products/${productId}`);
  if (!res.ok) throw new Error(`Product not found: ${res.statusText}`);
  return res.json();
}

export async function searchProducts(payload: {
  query: string;
  search_mode?: string;
  filters?: ActiveFilters;
  top_k?: number;
  alpha?: number;
}): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/v1/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Search request failed');
  }
  return res.json();
}

export async function searchByImage(file: File): Promise<ImageSearchResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/v1/search/image`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Image search failed');
  }
  return res.json();
}

export async function fetchRecommendations(payload: {
  user_id?: string;
  preferences?: StatedPreferences;
  viewed_product_ids?: string[];
  saved_product_ids?: string[];
  top_k?: number;
  include_diversity?: boolean;
}): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE}/api/v1/recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to fetch recommendations: ${res.statusText}`);
  return res.json();
}

export async function askAssistant(question: string): Promise<AssistantAskResponse> {
  const res = await fetch(`${API_BASE}/api/v1/assistant/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Assistant query failed');
  }
  return res.json();
}

export async function fetchEvaluationAnalytics(): Promise<EvaluationResponse> {
  const res = await fetch(`${API_BASE}/api/v1/analytics/search-evaluation`);
  if (!res.ok) throw new Error(`Failed to fetch evaluation analytics: ${res.statusText}`);
  return res.json();
}

export function getProductImageUrl(product: Product): string {
  if (product.image_path) {
    const filename = product.image_path.split(/[/\\]/).pop();
    return `${API_BASE}/static/images/${filename}`;
  }
  return product.image_url || 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600';
}
