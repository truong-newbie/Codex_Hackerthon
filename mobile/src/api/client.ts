import { 
  TokenResponse, SOPDetailResponse, TrainingSessionResponse, 
  TrainingTurnResponse, FinalResultResponse, HealthResponse,
  SessionSummaryItem, TrainingSessionDetailResponse
} from './types';

class ApiClient {
  private baseUrl: string = 'http://10.0.2.2:8000';
  private token: string | null = null;

  setBaseUrl(url: string) {
    this.baseUrl = url.trim().replace(/\/+$/, '');
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    // NFR-09: Network timeout controller (25s for live LLM requests)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = `Lỗi máy chủ (HTTP ${response.status})`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errorDetail = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        throw new Error(errorDetail);
      }

      return await response.json() as T;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('Yêu cầu quá thời gian chờ (Timeout 25s). Vui lòng thử lại.');
      }
      if (error.message.includes('Network request failed') || error.message.includes('Failed to fetch')) {
        throw new Error(`Không thể kết nối tới máy chủ tại ${this.baseUrl}. Vui lòng kiểm tra cấu hình IP/URL.`);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/v1/health');
  }

  async login(usernameOrEmail: string, password: string): Promise<TokenResponse> {
    return this.request<TokenResponse>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        username_or_email: usernameOrEmail,
        password,
      }),
    });
  }

  async getSops(): Promise<SOPDetailResponse[]> {
    return this.request<SOPDetailResponse[]>('/v1/sops');
  }

  async getSessions(): Promise<SessionSummaryItem[]> {
    return this.request<SessionSummaryItem[]>('/v1/training/sessions');
  }

  async getSessionDetail(sessionId: string): Promise<TrainingSessionDetailResponse> {
    return this.request<TrainingSessionDetailResponse>(`/v1/training/${sessionId}`);
  }

  async startTraining(sopId: string): Promise<TrainingSessionResponse> {
    return this.request<TrainingSessionResponse>('/v1/training/start', {
      method: 'POST',
      body: JSON.stringify({ sop_id: sopId }),
    });
  }

  async sendTurn(sessionId: string, message: string): Promise<TrainingTurnResponse> {
    return this.request<TrainingTurnResponse>(`/v1/training/${sessionId}/turn`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  async evaluateSession(sessionId: string): Promise<FinalResultResponse> {
    return this.request<FinalResultResponse>(`/v1/training/${sessionId}/evaluate`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
