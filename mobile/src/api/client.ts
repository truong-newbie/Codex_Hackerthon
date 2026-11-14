import { 
  TokenResponse, SOPDetailResponse, TrainingSessionResponse, 
  TrainingTurnResponse, FinalResultResponse, HealthResponse 
} from './types';

class ApiClient {
  private baseUrl: string = 'http://10.0.2.2:8000';
  private token: string | null = null;

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
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

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorDetail = `Lỗi hệ thống (${response.status})`;
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
      if (error.message.includes('Network request failed') || error.message.includes('Failed to fetch')) {
        throw new Error(`Không thể kết nối máy chủ tại ${this.baseUrl}. Vui lòng kiểm tra lại cấu hình IP/URL.`);
      }
      throw error;
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
