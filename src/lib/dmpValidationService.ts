
import type { ValidationResult } from '@/types/validation';

export interface DMPValidationOptions {
  tableCode?: string;
  skipTaxonomy?: boolean;
  validationMode: 'fast' | 'comprehensive';
}

export interface DMPValidationRule {
  ruleId: string;
  ruleType: 'formula' | 'dimensional' | 'completeness' | 'consistency';
  expression: string;
  severity: 'error' | 'warning' | 'info';
  description: string;
  tableCode?: string;
}

export class DMPValidationService {
  private static instance: DMPValidationService;
  private backendUrl: string | null = null;

  private constructor() {}

  static getInstance(): DMPValidationService {
    if (!DMPValidationService.instance) {
      DMPValidationService.instance = new DMPValidationService();
    }
    return DMPValidationService.instance;
  }

  async setBackendUrl(url: string) {
    this.backendUrl = url;
  }

  async validateDirectFromDMP(
    instanceFile: File, 
    options: DMPValidationOptions
  ): Promise<ValidationResult> {
    if (!this.backendUrl) {
      throw new Error('Backend URL not set');
    }

    console.log('🚀 Starting DMP-direct validation...');
    
    const formData = new FormData();
    formData.append('instance', instanceFile);
    formData.append('validation_mode', options.validationMode);
    formData.append('skip_taxonomy', options.skipTaxonomy ? 'true' : 'false');
    
    if (options.tableCode) {
      formData.append('table_code', options.tableCode);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes for DMP-only

    try {
      const response = await fetch(`${this.backendUrl}/validate-dmp-direct`, {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`DMP validation failed: ${errorText}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'DMP validation failed');
      }

      console.log('✅ DMP-direct validation completed');
      return this.transformDMPResult(result.result, instanceFile.name);

    } catch (error: any) {
      clearTimeout(timeoutId);
      console.error('💥 DMP validation error:', error);
      throw error;
    }
  }

  private transformDMPResult(dmpResult: any, instanceFileName: string): ValidationResult {
    return {
      isValid: dmpResult.isValid ?? false,
      status: dmpResult.status as "valid" | "invalid" ?? 'invalid',
      errors: dmpResult.errors ?? [],
      dpmResults: dmpResult.dmpResults ?? [],
      timestamp: dmpResult.timestamp ?? new Date().toISOString(),
      filesProcessed: {
        instanceFile: instanceFileName,
        taxonomyFile: 'DMP Database (Direct)'
      },
      validationStats: dmpResult.validationStats ?? {
        totalRules: 0,
        passedRules: 0,
        failedRules: 0,
        formulasChecked: 0,
        dimensionsValidated: 0
      }
    };
  }

  async getAvailableValidationModes(): Promise<Array<{
    mode: string;
    description: string;
    requiresTaxonomy: boolean;
    estimatedTime: string;
  }>> {
    return [
      {
        mode: 'fast',
        description: 'Snelle DMP validatie zonder taxonomy bestand',
        requiresTaxonomy: false,
        estimatedTime: '30-60 seconden'
      },
      {
        mode: 'comprehensive',
        description: 'Volledige Arelle + DMP validatie met taxonomy',
        requiresTaxonomy: true,
        estimatedTime: '2-3 minuten'
      }
    ];
  }
}
