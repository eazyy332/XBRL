import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, RotateCcw, Download, FileText } from "lucide-react";
import { ValidationResult } from "@/types/validation";
import { DpmResultsDisplay } from "./DpmResultsDisplay";

interface ValidationResultsCardProps {
  result: ValidationResult;
  onReset: () => void;
}

export const ValidationResultsCard = ({ result, onReset }: ValidationResultsCardProps) => {
  // FIXED: Use correct property names
  const dmpResults = result.dmpResults || result.dpmResults || [];
  const isValid = result.status === "valid" && dmpResults.filter(r => r.status === 'Failed').length === 0;
  const failedCount = dmpResults.filter(r => r.status === 'Failed').length || 0;
  const passedCount = dmpResults.filter(r => r.status === 'Passed').length || 0;
  const totalRules = dmpResults.length;

  console.log('🔍 ValidationResultsCard Debug:', {
    totalDmpResults: totalRules,
    failedCount,
    passedCount,
    isValid,
    hasResults: totalRules > 0,
    resultKeys: Object.keys(result)
  });

  const downloadReport = () => {
    const reportData = {
      validationResult: result,
      generatedAt: new Date().toISOString(),
      summary: {
        valid: isValid,
        totalRules: totalRules,
        passed: passedCount,
        failed: failedCount,
        dmpEnhanced: true
      }
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

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card>
        <CardContent className="p-8">
          <div className="text-center">
            {isValid ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <div className="bg-green-100 p-4 rounded-full">
                    <CheckCircle className="h-12 w-12 text-green-600" />
                  </div>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-green-800">✅ XBRL is valid!</h2>
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
                  <h2 className="text-2xl font-bold text-red-800">❌ Validation failed</h2>
                  <p className="text-red-600 mt-2">
                    Your XBRL instance document contains {failedCount} validation issue{failedCount !== 1 ? 's' : ''}.
                  </p>
                </div>
              </div>
            )}

            {/* Enhanced Summary badges with DMP 4.0 info */}
            <div className="flex items-center justify-center gap-4 mt-4 flex-wrap">
              {totalRules > 0 && (
                <Badge className="bg-blue-100 text-blue-800 border-blue-300">
                  📊 {totalRules} Rules Checked
                </Badge>
              )}
              {passedCount > 0 && (
                <Badge className="bg-green-100 text-green-800 border-green-300">
                  ✅ {passedCount} Passed
                </Badge>
              )}
              {failedCount > 0 && (
                <Badge className="bg-red-100 text-red-800 border-red-300">
                  ❌ {failedCount} Failed
                </Badge>
              )}
              <Badge className="bg-purple-100 text-purple-800 border-purple-300">
                🗄️ DMP 4.0 Enhanced
              </Badge>
            </div>

            <div className="flex items-center justify-center gap-4 mt-6 text-sm text-gray-600 flex-wrap">
              <span>Instance: {result.filesProcessed.instanceFile}</span>
              <span>•</span>
              <span>Engine: {result.filesProcessed.taxonomyFile}</span>
              <span>•</span>
              <span>Validated: {new Date(result.timestamp).toLocaleString()}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DMP Results Display - FIXED to show results with correct prop name */}
      {totalRules > 0 ? (
        <DpmResultsDisplay dpmResults={dmpResults} />
      ) : (
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4" />
              <p>No DMP validation results to display</p>
              <p className="text-sm mt-2">This may indicate a backend communication issue</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-4">
        <Button onClick={onReset} variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Reset and Upload New Files
        </Button>
        <Button onClick={downloadReport} className="gap-2">
          <Download className="h-4 w-4" />
          Download Validation Report
        </Button>
      </div>
    </div>
  );
};
