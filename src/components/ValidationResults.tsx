import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, XCircle, AlertTriangle, Info, RotateCcw, Download, FileText } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ValidationResult } from "@/types/validation";

interface ValidationResultsProps {
  result: ValidationResult;
  onReset: () => void;
}

export const ValidationResults = ({ result, onReset }: ValidationResultsProps) => {
  // FIXED: Use correct property names
  const dmpResults = result.dmpResults || result.dpmResults || [];
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';  
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  // Count errors by severity from both errors array and dmpResults
  const allIssues = [
    ...(result.errors || []),
    ...dmpResults.filter(r => r.status === 'Failed').map(r => ({
      message: r.message,
      severity: r.severity || 'error',
      code: r.rule,
      concept: r.concept,
      documentation: r.annotation
    }))
  ];

  const errorCount = allIssues.filter(e => e.severity === 'error').length;
  const warningCount = allIssues.filter(e => e.severity === 'warning').length;
  const infoCount = allIssues.filter(e => e.severity === 'info').length;

  const downloadReport = () => {
    const reportData = {
      validationResult: result,
      generatedAt: new Date().toISOString(),
      summary: {
        valid: result.isValid,
        totalIssues: allIssues.length,
        errors: errorCount,
        warnings: warningCount,
        info: infoCount,
        dmpResultsCount: dmpResults.length
      },
      detailedIssues: allIssues,
      dmpResults: dmpResults
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `xbrl-validation-report-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Enhanced validation status determination
  const hasFailures = errorCount > 0 || dmpResults.some(r => r.status === 'Failed');
  const isValidationSuccess = result.isValid && !hasFailures && result.status !== "invalid";

  console.log('🔍 ValidationResults Debug:', {
    totalDmpResults: dmpResults.length,
    totalIssues: allIssues.length,
    hasFailures,
    isValidationSuccess
  });

  return (
    <div className="space-y-6">
      {/* Success/Failure Header */}
      <Card>
        <CardContent className="p-8">
          <div className="text-center">
            {isValidationSuccess ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <div className="bg-green-100 p-4 rounded-full">
                    <CheckCircle className="h-12 w-12 text-green-600" />
                  </div>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-green-800">✅ XBRL Validation Successful!</h2>
                  <p className="text-green-600 mt-2">
                    Your XBRL instance document passed all validation rules.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <div className="bg-red-100 p-4 rounded-full">
                    <XCircle className="h-12 w-12 text-red-600" />
                  </div>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-red-800">❌ XBRL Validation Failed</h2>
                  <p className="text-red-600 mt-2">
                    {allIssues.length > 0 
                      ? `Found ${allIssues.length} validation issue${allIssues.length !== 1 ? 's' : ''} in your XBRL document.`
                      : "Your XBRL instance document failed validation."
                    }
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center justify-center gap-4 mt-6 text-sm text-gray-600">
              <span>Instance: {result.filesProcessed.instanceFile}</span>
              <span>•</span>
              <span>Engine: {result.filesProcessed.taxonomyFile}</span>
              <span>•</span>
              <span>Validated: {new Date(result.timestamp).toLocaleString()}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Validation Statistics */}
      {(result.validationStats || dmpResults.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Validation Statistics</CardTitle>
            <CardDescription>
              Overview of validation rules processed and results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-blue-500" />
                  <span className="font-semibold text-blue-800">Total Rules</span>
                </div>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {result.validationStats?.totalRules || dmpResults.length || 0}
                </p>
              </div>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-semibold text-green-800">Passed</span>
                </div>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {result.validationStats?.passedRules || dmpResults.filter(r => r.status === 'Passed').length || 0}
                </p>
              </div>
              
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="font-semibold text-red-800">Failed</span>
                </div>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {result.validationStats?.failedRules || dmpResults.filter(r => r.status === 'Failed').length || 0}
                </p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <span className="font-semibold text-yellow-800">Issues</span>
                </div>
                <p className="text-2xl font-bold text-yellow-600 mt-1">{allIssues.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* DMP Results Table - FIXED to use correct field */}
      {dmpResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>EBA DPM Validation Results</CardTitle>
            <CardDescription>
              Detailed validation results from EBA Data Point Model rules ({dmpResults.length} results)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {dmpResults.map((dmpResult, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${
                      dmpResult.status === 'Passed'
                        ? 'bg-green-50 border-green-200'
                        : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {dmpResult.status === 'Passed' ? (
                        <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge 
                            className={
                              dmpResult.status === 'Passed'
                                ? 'bg-green-100 text-green-800 border-green-300'
                                : 'bg-red-100 text-red-800 border-red-300'
                            }
                          >
                            {dmpResult.status}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {dmpResult.rule}
                          </Badge>
                          {dmpResult.ruleType && (
                            <Badge variant="secondary" className="text-xs">
                              {dmpResult.ruleType}
                            </Badge>
                          )}
                        </div>
                        
                        <div className="space-y-2">
                          <div>
                            <span className="text-sm font-medium text-gray-700">Concept: </span>
                            <span className="text-sm font-mono text-gray-900">{dmpResult.concept}</span>
                          </div>
                          
                          <div>
                            <span className="text-sm font-medium text-gray-700">Message: </span>
                            <span className="text-sm text-gray-600">{dmpResult.message}</span>
                          </div>
                          
                          {dmpResult.annotation && (
                            <div className="bg-blue-50 border border-blue-200 rounded p-2 mt-2">
                              <span className="text-xs font-medium text-blue-700">Rule Description: </span>
                              <span className="text-xs text-blue-600">{dmpResult.annotation}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* No Issues Found */}
      {allIssues.length === 0 && dmpResults.length === 0 && (
        <Alert className="border-blue-200 bg-blue-50">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <strong>No validation issues found.</strong> Your XBRL document appears to be structurally valid.
          </AlertDescription>
        </Alert>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-4">
        <Button onClick={onReset} variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Validate Another Document
        </Button>
        <Button onClick={downloadReport} className="gap-2">
          <Download className="h-4 w-4" />
          Download Validation Report
        </Button>
      </div>
    </div>
  );
};
