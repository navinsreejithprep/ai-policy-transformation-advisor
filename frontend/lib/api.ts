import type {
  AnalysisJobStatus,
  AnalysisStartResponse,
  DocumentCategory,
  DocumentListResponse,
  FinalReport,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(
      "Could not reach the backend. Make sure FastAPI is running on http://localhost:8000.",
      0
    );
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export function getDocuments(): Promise<DocumentListResponse> {
  return request<DocumentListResponse>("/documents");
}

export async function uploadDocument(
  file: File,
  category?: DocumentCategory
): Promise<{ document: string; chunks_added: number; category: DocumentCategory }> {
  const formData = new FormData();
  formData.append("file", file);
  if (category) formData.append("category", category);
  return request("/documents/upload", { method: "POST", body: formData });
}

export function deleteDocument(documentName: string): Promise<{ document: string; chunks_removed: number }> {
  return request(`/documents/${encodeURIComponent(documentName)}`, { method: "DELETE" });
}

export function getDocumentText(documentName: string): Promise<{ document_name: string; text: string }> {
  return request(`/documents/${encodeURIComponent(documentName)}/text`);
}

export function reindexDocuments(): Promise<{ documents: number; chunks: number; errors: string[] }> {
  return request("/documents/index", { method: "POST" });
}

export function startAnalysis(policyText: string): Promise<AnalysisStartResponse> {
  return request("/analysis/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ policy_text: policyText }),
  });
}

export function getAnalysisStatus(jobId: string): Promise<AnalysisJobStatus> {
  return request(`/analysis/${jobId}`);
}

export function getAnalysisReport(jobId: string): Promise<FinalReport> {
  return request(`/analysis/${jobId}/report`);
}
