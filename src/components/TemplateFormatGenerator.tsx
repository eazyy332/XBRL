import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Download, FileText, AlertTriangle, CheckCircle } from "lucide-react";
import { ValidationResult } from "@/types/validation";
import { useState } from "react";

interface TemplateFormatGeneratorProps {
  validationResult: ValidationResult;
}

export const TemplateFormatGenerator = ({ validationResult }: TemplateFormatGeneratorProps) => {
  const [selectedFormat, setSelectedFormat] = useState<string>("");
  
  // FIXED: Use the correct property names from ValidationResult type
  const dmpResults = validationResult.dmpResults || validationResult.dpmResults || [];
  const hasResults = dmpResults.length > 0;
  const failedRules = dmpResults.filter(r => r.status === 'Failed');
  const passedRules = dmpResults.filter(r => r.status === 'Passed');

  console.log('🔍 TemplateGenerator Debug:', {
    totalResults: dmpResults.length,
    failed: failedRules.length,
    passed: passedRules.length,
    hasResults
  });

  const templateFormats = [
    {
      id: "eba-regulatory-pdf",
      name: "EBA Regulatory Template (PDF)",
      description: "Professional PDF report with charts and regulatory compliance",
      format: "pdf",
      new: true
    },
    {
      id: "excel-detailed",
      name: "Excel Detailed Analysis",
      description: "Comprehensive Excel workbook with validation results and formulas",
      format: "xlsx"
    },
    {
      id: "json-technical",
      name: "JSON Technical Report",
      description: "Machine-readable technical report for system integration",
      format: "json"
    },
    {
      id: "csv-summary",
      name: "CSV Summary Report",
      description: "Simple CSV format for data analysis and reporting",
      format: "csv"
    }
  ];

  const generateTemplate = async () => {
    if (!selectedFormat || !hasResults) {
      return;
    }

    const selectedTemplate = templateFormats.find(t => t.id === selectedFormat);
    if (!selectedTemplate) return;

    // Generate comprehensive template data
    const templateData = {
      metadata: {
        generatedAt: new Date().toISOString(),
        validationEngine: "DMP 4.0 Enhanced",
        instanceFile: validationResult.filesProcessed.instanceFile,
        totalRules: dmpResults.length,
        passedRules: passedRules.length,
        failedRules: failedRules.length,
        validationStatus: failedRules.length === 0 ? 'VALID' : 'INVALID'
      },
      validationSummary: {
        // FIXED: Use optional chaining for potentially missing properties
        totalErrorsDetected: validationResult.validationStats?.totalErrorsDetected || 0,
        missingConcepts: validationResult.validationStats?.missingConcepts || 0,
        businessRuleErrors: validationResult.validationStats?.businessRuleErrors || 0,
        loadingErrors: validationResult.validationStats?.loadingErrors || 0
      },
      dmpResults: dmpResults.map(result => ({
        concept: result.concept,
        rule: result.rule,
        status: result.status,
        message: result.message,
        annotation: result.annotation,
        ruleType: result.ruleType,
        severity: result.severity
      })),
      errorsByCategory: {
        structural: dmpResults.filter(r => r.ruleType === 'structural').length,
        business: dmpResults.filter(r => r.ruleType === 'business').length,
        schema: dmpResults.filter(r => r.ruleType === 'schema').length,
        loading: dmpResults.filter(r => r.ruleType === 'loading').length,
        system: dmpResults.filter(r => r.ruleType === 'system').length
      },
      recommendations: generateRecommendations(failedRules)
    };

    // Create and download the file
    let blob: Blob;
    let filename: string;

    switch (selectedTemplate.format) {
      case 'pdf':
        // For PDF, we'll create a structured HTML that can be converted to PDF
        const htmlContent = generatePDFTemplate(templateData);
        blob = new Blob([htmlContent], { type: 'text/html' });
        filename = `EBA-Regulatory-Report-${Date.now()}.html`;
        break;
      
      case 'xlsx':
        // For Excel, create a structured CSV that can be imported
        const csvContent = generateExcelTemplate(templateData);
        blob = new Blob([csvContent], { type: 'text/csv' });
        filename = `XBRL-Detailed-Analysis-${Date.now()}.csv`;
        break;
      
      case 'json':
        blob = new Blob([JSON.stringify(templateData, null, 2)], { type: 'application/json' });
        filename = `XBRL-Technical-Report-${Date.now()}.json`;
        break;
      
      case 'csv':
        const simpleCsv = generateCSVTemplate(templateData);
        blob = new Blob([simpleCsv], { type: 'text/csv' });
        filename = `XBRL-Summary-Report-${Date.now()}.csv`;
        break;
      
      default:
        return;
    }

    // Download the file
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const generateRecommendations = (failedRules: any[]) => {
    const recommendations = [];
    
    if (failedRules.some(r => r.ruleType === 'schema')) {
      recommendations.push("Update taxonomy files to include missing schema definitions");
    }
    
    if (failedRules.some(r => r.ruleType === 'loading')) {
      recommendations.push("Check file paths and network connectivity for taxonomy loading");
    }
    
    if (failedRules.some(r => r.ruleType === 'business')) {
      recommendations.push("Review business rule calculations and data consistency");
    }
    
    if (failedRules.length > 50) {
      recommendations.push("Consider using comprehensive validation mode for detailed analysis");
    }
    
    return recommendations;
  };

  const generatePDFTemplate = (data: any) => {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>EBA Regulatory Validation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .summary { background: #f5f5f5; padding: 15px; margin: 20px 0; }
        .error { color: #d32f2f; }
        .success { color: #388e3c; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>EBA Regulatory Validation Report</h1>
        <p>Generated: ${new Date(data.metadata.generatedAt).toLocaleString()}</p>
        <p>Instance: ${data.metadata.instanceFile}</p>
        <p>Status: <span class="${data.metadata.validationStatus === 'VALID' ? 'success' : 'error'}">${data.metadata.validationStatus}</span></p>
    </div>
    
    <div class="summary">
        <h2>Validation Summary</h2>
        <p>Total Rules Processed: ${data.metadata.totalRules}</p>
        <p>Passed Rules: ${data.metadata.passedRules}</p>
        <p>Failed Rules: ${data.metadata.failedRules}</p>
        <p>Missing Concepts: ${data.validationSummary.missingConcepts}</p>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr><th>Concept</th><th>Rule</th><th>Status</th><th>Message</th></tr>
        ${data.dmpResults.map((r: any) => `
            <tr>
                <td>${r.concept}</td>
                <td>${r.rule}</td>
                <td class="${r.status === 'Passed' ? 'success' : 'error'}">${r.status}</td>
                <td>${r.message}</td>
            </tr>
        `).join('')}
    </table>
    
    <h2>Recommendations</h2>
    <ul>
        ${data.recommendations.map((rec: string) => `<li>${rec}</li>`).join('')}
    </ul>
</body>
</html>`;
  };

  const generateExcelTemplate = (data: any) => {
    let csv = "Concept,Rule,Status,Message,RuleType,Severity\n";
    data.dmpResults.forEach((r: any) => {
      csv += `"${r.concept}","${r.rule}","${r.status}","${r.message}","${r.ruleType}","${r.severity}"\n`;
    });
    return csv;
  };

  const generateCSVTemplate = (data: any) => {
    let csv = "Summary,Value\n";
    csv += `Total Rules,${data.metadata.totalRules}\n`;
    csv += `Passed Rules,${data.metadata.passedRules}\n`;
    csv += `Failed Rules,${data.metadata.failedRules}\n`;
    csv += `Status,${data.metadata.validationStatus}\n`;
    csv += `Generated,${data.metadata.generatedAt}\n`;
    return csv;
  };

  if (!hasResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Professional Template Generation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              <strong>No DMP validation results available.</strong> Run validation first to generate professional templates.
              <br />
              <span className="text-sm mt-1 block">
                Debug info: Found {dmpResults.length} DMP results in validation result
              </span>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5" />
          Professional Template Generation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <strong>✅ DMP validation results available!</strong> {dmpResults.length} results ready for template generation.
          </AlertDescription>
        </Alert>

        <div>
          <label className="text-sm font-medium mb-2 block">Select Professional Template Format</label>
          <Select value={selectedFormat} onValueChange={setSelectedFormat}>
            <SelectTrigger>
              <SelectValue placeholder="Choose template format..." />
            </SelectTrigger>
            <SelectContent>
              {templateFormats.map((format) => (
                <SelectItem key={format.id} value={format.id}>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <span>{format.name}</span>
                    {format.new && <Badge className="bg-blue-100 text-blue-800 text-xs">NEW</Badge>}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {selectedFormat && (
            <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
              <p className="text-sm text-blue-800">
                {templateFormats.find(f => f.id === selectedFormat)?.description}
              </p>
            </div>
          )}
        </div>

        <Button 
          onClick={generateTemplate}
          disabled={!selectedFormat}
          className="w-full bg-green-600 hover:bg-green-700"
        >
          <Download className="h-4 w-4 mr-2" />
          Generate Professional Template
        </Button>
      </CardContent>
    </Card>
  );
};
