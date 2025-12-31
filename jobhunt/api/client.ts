/**
 * Base API client with error handling and type safety
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.text();
    let message = errorBody;
    try {
      const json = JSON.parse(errorBody);
      message = json.detail || json.message || errorBody;
    } catch {
      // Keep original text
    }
    throw new ApiError(response.status, response.statusText, message);
  }
  return response.json();
}

/**
 * HTTP GET request
 */
export async function get<T>(endpoint: string, params?: Record<string, unknown>): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
    credentials: 'include',
  });
  
  return handleResponse<T>(response);
}

/**
 * HTTP POST request
 */
export async function post<T>(endpoint: string, data?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    credentials: 'include',
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

/**
 * HTTP POST request with FormData (for file uploads)
 */
export async function postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  
  return handleResponse<T>(response);
}

/**
 * HTTP PATCH request
 */
export async function patch<T>(endpoint: string, data?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    credentials: 'include',
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

/**
 * HTTP DELETE request
 */
export async function del<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'DELETE',
    headers: {
      'Accept': 'application/json',
    },
    credentials: 'include',
  });
  
  return handleResponse<T>(response);
}

