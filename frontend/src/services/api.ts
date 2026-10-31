/**
 * API client communicating with the QuestionTrail FastAPI backend.
 */

import type {
  AssessmentCategory,
  ResearchProject,
  ProjectDetailResponse,
  AnalyzeProjectResponse,
  ReportResponse,
} from '../types/api';

const BASE_URL = '/api';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore JSON parse errors on non-JSON failure bodies
    }
    throw new ApiError(res.status, errorDetail);
  }

  return res.json() as Promise<T>;
}

export const api = {
  proposeCategories: async (objective: string): Promise<AssessmentCategory[]> => {
    const res = await request<{ objective: string; categories: AssessmentCategory[] }>(
      '/categories/propose',
      {
        method: 'POST',
        body: JSON.stringify({ objective }),
      }
    );
    return res.categories;
  },

  createProject: async (
    objective: string,
    categories: AssessmentCategory[] = []
  ): Promise<ResearchProject> => {
    return request<ResearchProject>('/projects', {
      method: 'POST',
      body: JSON.stringify({ objective, categories }),
    });
  },

  getProject: async (projectId: string): Promise<ProjectDetailResponse> => {
    return request<ProjectDetailResponse>(`/projects/${projectId}`);
  },

  loadCuratedDemo: async (projectId: string): Promise<ProjectDetailResponse> => {
    return request<ProjectDetailResponse>(`/projects/${projectId}/load-demo`, {
      method: 'POST',
    });
  },

  analyzeProject: async (projectId: string): Promise<AnalyzeProjectResponse> => {
    return request<AnalyzeProjectResponse>(`/projects/${projectId}/analyze`, {
      method: 'POST',
    });
  },

  getReport: async (projectId: string): Promise<ReportResponse> => {
    return request<ReportResponse>(`/projects/${projectId}/report`);
  },
};
