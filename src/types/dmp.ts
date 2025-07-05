
import type { ValidationResult } from './validation';

export interface DMPTable {
  OriginalTableCode: string;
  TableVersion: string;
  TableLabel: string;
}

export interface DMPConcept {
  CellPosition: string;
  CellID: string;
  DataPointCode: string;
  DataPointLabel: string;
  MetricCode: string;
  MetricLabel: string;
  TableLabel: string;
}

export interface DMPDimension {
  DomainCode: string;
  DomainLabel: string;
  MemberCode: string;
  MemberLabel: string;
}

export interface DMPValidationRule {
  RuleID: string;
  RuleCode: string;
  RuleLabel: string;
  RuleFormula: string;
  ErrorMessage: string;
  Severity?: 'error' | 'warning' | 'info';
}

export interface DMPDatabaseStatus {
  status: 'connected' | 'error' | 'limited' | 'permission_error';
  message: string;
  dmp_tables?: number;
  database_path?: string;
  sample_tables?: Array<{table: string; rows: number}>;
  troubleshooting?: string;
}

export interface DMPStatus {
  status: 'active' | 'error' | 'limited';
  message: string;
  timestamp?: string;
  backend_version?: string;
  features?: {
    dmp_direct_validation?: boolean;
    taxonomy_optional?: boolean;
    fast_mode?: boolean;
    comprehensive_mode?: boolean;
  };
  dmp_database?: DMPDatabaseStatus;
}

export interface DMPContext {
  table_code: string;
  concepts: DMPConcept[];
  validation_rules: DMPValidationRule[];
}

export interface EnhancedValidationResult extends ValidationResult {
  dmpContext?: DMPContext;
  dmpDatabaseStatus?: string;
}
