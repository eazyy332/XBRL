
export interface ValidationError {
  line?: number;
  column?: number;
  message: string;
  severity: 'error' | 'warning' | 'info';
  code?: string;
  concept?: string;
  label?: string;
  documentation?: string;
  lang?: string;
}

export interface DpmResult {
  concept: string;
  rule: string;
  message: string;
  annotation: string;
  status: 'Failed' | 'Passed';
  ruleType?: 'consistency' | 'completeness' | 'formula' | 'dimensional' | 'structural' | 'business' | 'schema' | 'loading' | 'system';
  severity?: 'error' | 'warning' | 'info';
  formula?: string;
  expectedValue?: string | number;
  actualValue?: string | number;
}

export interface ValidationStats {
  totalRules: number;
  passedRules: number;
  failedRules: number;
  formulasChecked: number;
  dimensionsValidated: number;
  dmpEnhanced?: boolean;
  // Add missing properties that the backend sends
  totalErrorsDetected?: number;
  missingConcepts?: number;
  businessRuleErrors?: number;
  loadingErrors?: number;
}

export interface ValidationResult {
  isValid: boolean;
  status: "valid" | "invalid";
  errors: ValidationError[];
  dpmResults?: DpmResult[];
  // Add dmpResults for backend compatibility
  dmpResults?: DpmResult[];
  timestamp: string;
  filesProcessed: {
    instanceFile: string;
    taxonomyFile: string;
  };
  validationStats?: ValidationStats;
}
