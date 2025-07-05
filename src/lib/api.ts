import { ValidationResult } from '@/types/validation';

const BACKEND_URL = 'http://127.0.0.1:5000';

// Test backend URLs for availability
const testBackendUrls = async (): Promise<string | null> => {
  const urls = ['http://127.0.0.1:5000', 'http://localhost:5000'];
  
  console.log('🔍 Testing backend URLs...');
  
  for (const url of urls) {
    try {
      console.log(`🌐 Testing: ${url}/health`);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${url}/health`, { 
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        console.log(`✅ Backend ${url} available!`);
        return url;
      }
    } catch (error) {
      console.log(`❌ Backend ${url} not available:`, error);
    }
  }
  
  return null;
};

interface ValidationApiResponse {
  success: boolean;
  result?: {
    isValid: boolean;
    status: string;
    errors: any[];
    dmpResults?: any[];
    timestamp: string;
    filesProcessed: {
      instanceFile: string;
      taxonomyFile: string;
    };
    validationStats?: any;
  };
  error?: string;
  processingTime?: number;
  validationEngine?: string;
}

export const validateFiles = async (
  instanceFile: File, 
  taxonomyFile: File, 
  tableCode?: string
): Promise<ValidationResult> => {
  const availableBackend = await testBackendUrls();
  
  if (!availableBackend) {
    throw new Error('BACKEND_UNAVAILABLE');
  }

  console.log('🚀 Starting validation with enhanced endpoint...');
  
  const formData = new FormData();
  formData.append('instance', instanceFile);
  formData.append('taxonomy', taxonomyFile);
  
  if (tableCode) {
    formData.append('table_code', tableCode);
    console.log(`📋 Using table code: ${tableCode}`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    console.log('⏱️ Validation request timed out after 3 minutes');
    controller.abort();
  }, 180000); // 3 minutes timeout

  try {
    console.log('📤 Sending validation request to enhanced backend...');
    const response = await fetch(`${availableBackend}/validate-enhanced`, {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    console.log('📥 Received response from backend:', response.status, response.ok);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Validation request failed:', response.status, errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const rawData = await response.json();
    console.log('🔍 Raw backend response received successfully');

    // Validate response structure
    if (!rawData || typeof rawData !== 'object') {
      console.error('❌ Invalid response structure:', rawData);
      throw new Error('Invalid response format from backend');
    }

    const data: ValidationApiResponse = rawData;

    if (!data.success) {
      console.error('❌ Backend reported validation failure:', data.error);
      throw new Error(data.error || 'Validation failed');
    }

    if (!data.result) {
      console.error('❌ Backend response missing result field');
      throw new Error('Backend response missing validation result');
    }

    // Transform to match our ValidationResult interface
    const result: ValidationResult = {
      isValid: data.result.isValid ?? false,
      status: data.result.status as "valid" | "invalid" ?? 'invalid',
      errors: data.result.errors ?? [],
      dpmResults: data.result.dmpResults ?? [],
      timestamp: data.result.timestamp ?? new Date().toISOString(),
      filesProcessed: data.result.filesProcessed ?? {
        instanceFile: instanceFile.name,
        taxonomyFile: taxonomyFile.name
      },
      validationStats: data.result.validationStats
    };

    console.log('✅ Validation completed successfully');
    return result;

  } catch (error: any) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      console.log('⏱️ Request aborted due to timeout');
      throw new Error('VALIDATION_TIMEOUT');
    }
    
    console.error('💥 Validation error:', error);
    throw error;
  }
};

// NEW: DMP-direct validation function
export const validateWithDMPDirect = async (
  instanceFile: File,
  options: {
    validationMode?: 'fast' | 'comprehensive';
    tableCode?: string;
  } = {}
): Promise<ValidationResult> => {
  const availableBackend = await testBackendUrls();
  
  if (!availableBackend) {
    throw new Error('BACKEND_UNAVAILABLE');
  }

  console.log('🚀 Starting DMP-direct validation...');
  
  const formData = new FormData();
  formData.append('instance', instanceFile);
  formData.append('validation_mode', options.validationMode || 'fast');
  formData.append('skip_taxonomy', 'true');
  
  if (options.tableCode) {
    formData.append('table_code', options.tableCode);
    console.log(`📋 Using DMP table: ${options.tableCode}`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    console.log('⏱️ DMP validation timed out after 2 minutes');
    controller.abort();
  }, 120000); // 2 minutes timeout for DMP-direct

  try {
    console.log('📤 Sending DMP-direct validation request...');
    const response = await fetch(`${availableBackend}/validate-dmp-direct`, {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ DMP validation failed:', response.status, errorText);
      throw new Error(`DMP validation failed: ${errorText}`);
    }

    const data = await response.json();

    if (!data.success) {
      console.error('❌ DMP validation reported failure:', data.error);
      throw new Error(data.error || 'DMP validation failed');
    }

    console.log('✅ DMP-direct validation completed successfully');
    return data.result;

  } catch (error: any) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      console.log('⏱️ DMP validation aborted due to timeout');
      throw new Error('DMP_VALIDATION_TIMEOUT');
    }
    
    console.error('💥 DMP validation error:', error);
    throw error;
  }
};

// BackendService class for compatibility
export class BackendService {
  private static instance: BackendService;
  private workingUrl: string | null = null;
  private lastError: string | null = null;
  private detailedErrors: Array<{url: string, error: string}> = [];

  private constructor() {}

  static getInstance(): BackendService {
    if (!BackendService.instance) {
      BackendService.instance = new BackendService();
    }
    return BackendService.instance;
  }

  async checkBackendStatus(): Promise<boolean> {
    const workingUrl = await testBackendUrls();
    this.workingUrl = workingUrl;
    return workingUrl !== null;
  }

  async findWorkingBackendUrl(): Promise<string | null> {
    const workingUrl = await testBackendUrls();
    this.workingUrl = workingUrl;
    return workingUrl;
  }

  getWorkingUrl(): string | null {
    return this.workingUrl;
  }

  getLastError(): string | null {
    return this.lastError;
  }

  getDetailedErrors(): Array<{url: string, error: string}> {
    return this.detailedErrors;
  }

  async generateXBRL(excelFile: File): Promise<{
    success: boolean;
    downloadUrl?: string;
    filename?: string;
    error?: string;
  }> {
    const workingUrl = await this.findWorkingBackendUrl();
    
    if (!workingUrl) {
      throw new Error('Backend not available');
    }

    try {
      const formData = new FormData();
      formData.append('excel', excelFile);

      const response = await fetch(`${workingUrl}/generate-xbrl`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(60000)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      return result;

    } catch (error: any) {
      this.lastError = error.message;
      throw error;
    }
  }

  async validateXBRL(instanceFile: File, taxonomyFile: File): Promise<ValidationResult> {
    return await validateFiles(instanceFile, taxonomyFile);
  }

  async validateWithDMP(instanceFile: File, taxonomyFile: File, tableCode: string): Promise<ValidationResult> {
    return await validateFiles(instanceFile, taxonomyFile, tableCode);
  }

  async validateWithDMPDirect(instanceFile: File, tableCode?: string): Promise<ValidationResult> {
    return await validateWithDMPDirect(instanceFile, { 
      validationMode: 'fast',
      tableCode 
    });
  }
}
