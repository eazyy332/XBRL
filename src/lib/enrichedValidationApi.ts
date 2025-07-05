

interface ValidationResponse {
  success: boolean;
  result?: any;
  error?: string;
}

const API_BASE_URL = 'http://127.0.0.1:5000';
const VALIDATION_TIMEOUT = 300000; // 5 minutes timeout

export const validateXBRL = async (instanceFile: File, taxonomyFile: File, tableCode?: string): Promise<ValidationResponse> => {
  console.log('🚀 Starting validation with enhanced endpoint...');
  
  const formData = new FormData();
  formData.append('instance', instanceFile);
  formData.append('taxonomy', taxonomyFile);
  
  if (tableCode) {
    formData.append('table_code', tableCode);
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), VALIDATION_TIMEOUT);

    const response = await fetch(`${API_BASE_URL}/validate-enhanced`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      headers: {
        // Don't set Content-Type, let browser handle it for FormData
      }
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend validation failed:', response.status, errorText);
      throw new Error(`Backend validation failed: ${response.status} ${errorText}`);
    }

    const result = await response.json();
    console.log('✅ Validation completed:', result);
    
    return {
      success: true,
      result: result.result || result
    };

  } catch (error: any) {
    console.error('❌ Backend validation request failed:', error.message);
    
    if (error.name === 'AbortError') {
      console.log('⏱️ Validation request timed out after 5 minutes');
      throw new Error('VALIDATION_TIMEOUT');
    }
    
    throw new Error('BACKEND_UNAVAILABLE');
  }
};

export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
};

export const getDMPStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/dmp/status`);
    if (!response.ok) throw new Error('DMP status check failed');
    return await response.json();
  } catch (error) {
    console.error('Failed to get DMP status:', error);
    throw error;
  }
};
