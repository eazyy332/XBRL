import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileUploadZone } from "@/components/FileUploadZone";
import { ValidationProgress } from "@/components/ValidationProgress";
import { ValidationResultsCard } from "@/components/ValidationResultsCard";
import { ConceptResultsCards } from "@/components/ConceptResultsCards";
import { DpmResultsTable } from "@/components/DpmResultsTable";
import { BackendStatus } from "@/components/BackendStatus";
import { XBRLAnnotationSection } from "@/components/XBRLAnnotationSection";
import { useToast } from "@/hooks/use-toast";
import { Upload, Play, CheckCircle2, AlertCircle, FileText, Package, Database } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { BackendService } from "@/lib/api";
import type { ValidationResult } from "@/types/validation";
import { TemplateFormatGenerator } from "@/components/TemplateFormatGenerator";
import { EnhancedDmpResultsDisplay } from "@/components/EnhancedDpmResultsDisplay";
import { XBRLValueNavigator } from "@/components/XBRLValueNavigator";
import { DMPTableBrowser } from "@/components/dmp/DMPTableBrowser";
import { DMPStatusCard } from "@/components/dmp/DMPStatusCard";
import { ValidationMode, ValidationModeSelector } from "@/components/ValidationModeSelector";
import { TaxonomyRecommendationCard } from "@/components/TaxonomyRecommendationCard";

const Index = () => {
  const [instanceFile, setInstanceFile] = useState<File | null>(null);
  const [taxonomyFile, setTaxonomyFile] = useState<File | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [validationMethod, setValidationMethod] = useState<'java' | 'javascript'>('java');
  const [showDatapointViewer, setShowDatapointViewer] = useState(false);
  const [selectedConcept, setSelectedConcept] = useState<string>("");
  const [selectedDMPTable, setSelectedDMPTable] = useState<string>("");
  const [showDMPBrowser, setShowDMPBrowser] = useState(false);
  const [selectedValidationMode, setSelectedValidationMode] = useState<ValidationMode | null>(null);
  const [backendAvailable, setBackendAvailable] = useState<boolean>(false);
  const { toast } = useToast();
  const backendService = BackendService.getInstance();
  const navigate = useNavigate();

  // Check backend availability on component mount
  useEffect(() => {
    checkBackendAvailability();
  }, []);

  const checkBackendAvailability = async () => {
    const available = await backendService.checkBackendStatus();
    setBackendAvailable(available);
  };

  const handleValidation = async () => {
    if (!instanceFile) {
      toast({
        title: "Missing Files",
        description: "Please upload an XBRL instance file.",
        variant: "destructive",
      });
      return;
    }

    // Check if taxonomy is required for selected mode
    if (selectedValidationMode?.requiresTaxonomy && !taxonomyFile) {
      toast({
        title: "Taxonomy Required",
        description: `${selectedValidationMode.name} requires a taxonomy file.`,
        variant: "destructive",
      });
      return;
    }

    console.log('🎯 Starting validation process...');
    console.log('📁 Files to validate:', {
      instance: instanceFile.name,
      taxonomy: taxonomyFile?.name || 'Not required',
      mode: selectedValidationMode?.mode || 'default',
      selectedTable: selectedDMPTable
    });

    setIsValidating(true);
    setValidationResult(null);

    try {
      if (selectedValidationMode?.mode === 'fast') {
        await validateWithDMPDirect();
      } else if (validationMethod === 'java') {
        await validateWithPythonBackend();
      } else {
        await validateWithJavaScript();
      }
    } catch (error) {
      console.error('🚨 Validation process failed:', error);
      handleValidationError(error);
    } finally {
      setIsValidating(false);
    }
  };

  const validateWithDMPDirect = async () => {
    try {
      console.log('🚀 Starting DMP-direct validation...');
      
      const workingUrl = await backendService.findWorkingBackendUrl();
      if (!workingUrl) {
        throw new Error('BACKEND_UNAVAILABLE');
      }

      const formData = new FormData();
      formData.append('instance', instanceFile!);
      formData.append('validation_mode', 'fast');
      formData.append('skip_taxonomy', 'true');
      
      if (selectedDMPTable) {
        formData.append('table_code', selectedDMPTable);
      }

      const response = await fetch(`${workingUrl}/validate-dmp-direct`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(120000) // 2 minutes for DMP-direct
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`DMP validation failed: ${errorText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'DMP validation failed');
      }

      console.log('✅ DMP-direct validation completed');
      setValidationResult(data.result);
      
      toast({
        title: "🚀 DMP-Direct Validatie Voltooid",
        description: `Snelle validatie zonder taxonomy bestand in ${Math.round(data.processingTime)}s`,
        variant: "default",
      });

    } catch (error) {
      console.error('🚨 DMP-direct validation failed:', error);
      throw error;
    }
  };

  const validateWithPythonBackend = async () => {
    try {
      console.log('🐍 Starting Python backend validation...');
      
      // Use DMP-enhanced validation if table is selected
      const result = selectedDMPTable 
        ? await backendService.validateWithDMP(instanceFile!, taxonomyFile!, selectedDMPTable)
        : await backendService.validateXBRL(instanceFile!, taxonomyFile!);
      
      console.log('✅ Received validation result from backend:', result);
      
      // Validate the result before setting state
      if (!result || typeof result !== 'object') {
        console.error('❌ Invalid validation result:', result);
        throw new Error('Invalid validation result received from backend');
      }

      if (typeof result.isValid !== 'boolean') {
        console.error('❌ Missing or invalid isValid field:', result.isValid);
        throw new Error('Invalid validation result format');
      }

      console.log('🎯 Setting validation result state...');
      setValidationResult(result);
      
      const stats = result.validationStats;
      const statsMessage = stats 
        ? `Validated ${stats.totalRules} rules (${stats.passedRules} passed, ${stats.failedRules} failed)${stats.dmpEnhanced ? ' with DMP enhancement' : ''}`
        : `Status: ${result.status}`;
        
      toast({
        title: selectedDMPTable ? "DMP-Enhanced Validation Complete" : "Professional Validation Complete",
        description: `XBRL validation completed using Python backend. ${statsMessage}`,
        variant: result.status === "valid" ? "default" : "destructive",
      });

      console.log('🎉 Validation process completed successfully');
      
    } catch (error) {
      console.error('🚨 Python backend validation failed:', error);
      
      if (error instanceof Error && (
        error.message === 'BACKEND_UNAVAILABLE' || 
        error.message === 'BACKEND_NETWORK_ERROR' ||
        error.message === 'VALIDATION_TIMEOUT'
      )) {
        console.log('❌ Backend connectivity issue:', error.message);
        throw error;
      } else {
        console.error('❌ Unexpected validation error:', error);
        throw error;
      }
    }
  };

  const validateWithJavaScript = async () => {
    // Simplified JavaScript validation with disclaimer
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const basicResult: ValidationResult = {
      isValid: false,
      status: "invalid",
      errors: [{
        message: "JavaScript validation provides basic structure checks only",
        severity: 'info' as const,
        code: 'JS-001',
        concept: 'validation-notice',
        documentation: 'For comprehensive EBA DPM validation, use the Python backend with Arelle engine'
      }],
      dpmResults: [
        {
          concept: 'validation:notice',
          rule: 'JS-LIMITATION',
          message: 'JavaScript validation is limited - use Python backend for full EBA validation',
          annotation: 'This is a basic client-side validation. Professional validation requires the backend service.',
          status: 'Failed',
          ruleType: 'completeness',
          severity: 'warning'
        }
      ],
      timestamp: new Date().toISOString(),
      filesProcessed: {
        instanceFile: instanceFile!.name,
        taxonomyFile: taxonomyFile!.name
      },
      validationStats: {
        totalRules: 1,
        passedRules: 0,
        failedRules: 1,
        formulasChecked: 0,
        dimensionsValidated: 0
      }
    };

    setValidationResult(basicResult);
    toast({
      title: "Basic Validation Complete",
      description: "JavaScript validation completed with limitations. Use Python backend for comprehensive validation.",
      variant: "default",
    });
  };

  const handleValidationError = (error: any) => {
    if (validationMethod === 'java') {
      if (error instanceof Error) {
        if (error.message === 'BACKEND_NETWORK_ERROR') {
          toast({
            title: "Network Connection Issue",
            description: "Cannot connect to Python backend. Please check if your validation server is running on port 5000.",
            variant: "destructive",
          });
        } else if (error.message === 'BACKEND_UNAVAILABLE') {
          toast({
            title: "Backend Unavailable",
            description: "Python backend not reachable. Please start your XBRL validation server.",
            variant: "destructive",
          });
        } else if (error.message === 'VALIDATION_TIMEOUT') {
          toast({
            title: "Validation Timeout",
            description: "Validation took too long to complete. Please try with smaller files or check your backend.",
            variant: "destructive",
          });
        } else {
          toast({
            title: "Validation Error",
            description: `Backend error: ${error.message}`,
            variant: "destructive",
          });
        }
      }
      
      // Don't fallback to JavaScript mock - require proper backend
      toast({
        title: "Validation Unavailable",
        description: "Professional XBRL validation requires the Python backend. Please start your validation server.",
        variant: "destructive",
      });
    } else {
      console.error('JavaScript validation error:', error);
      toast({
        title: "Validation Error",
        description: "JavaScript validation failed. Please try again later.",
        variant: "destructive",
      });
    }
  };

  const resetValidation = () => {
    setInstanceFile(null);
    setTaxonomyFile(null);
    setValidationResult(null);
    setSelectedConcept("");
    setShowDatapointViewer(false);
  };

  const handleViewDatapoint = (concept: string) => {
    setSelectedConcept(concept);
    setShowDatapointViewer(true);
    console.log(`Viewing datapoint details for: ${concept}`);
  };

  const handleViewInXBRL = (concept: string) => {
    setSelectedConcept(concept);
    // This would open the XBRL preview and navigate to the specific concept
    console.log(`Navigating to concept in XBRL: ${concept}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-orange-900 mb-2">🧾 XBRL Validatie Tool</h1>
          <p className="text-orange-700">Upload en valideer je XBRL bestanden conform EBA/DNB regelgeving</p>
          
          {/* Navigation buttons */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
            <Button
              onClick={() => navigate('/generate-xbrl')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <FileText className="h-4 w-4 mr-2" />
              📤 Genereer XBRL uit Excel
            </Button>
            <Button
              onClick={() => setShowDMPBrowser(!showDMPBrowser)}
              variant="outline"
              className="border-purple-300 text-purple-700 hover:bg-purple-50"
            >
              <Package className="h-4 w-4 mr-2" />
              📊 Browse DMP Tables
            </Button>
          </div>
          
          {/* DMP Direct Mode Notice */}
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              <strong>🚀 Nieuw:</strong> DMP-Direct validatie beschikbaar! Valideer zonder taxonomy bestand via directe database toegang.
            </p>
          </div>
        </div>

        <BackendStatus />
        <DMPStatusCard />

        {/* Validation Mode Selector */}
        <div className="mb-6">
          <ValidationModeSelector
            onModeSelect={setSelectedValidationMode}
            selectedMode={selectedValidationMode}
            backendAvailable={backendAvailable}
          />
        </div>

        {/* DMP Table Browser */}
        {showDMPBrowser && (
          <div className="mb-6">
            <DMPTableBrowser 
              onTableSelect={setSelectedDMPTable}
              selectedTable={selectedDMPTable}
            />
          </div>
        )}

        {/* Main Content */}
        <div className="max-w-4xl mx-auto space-y-6">
          {!validationResult && (
            <Card className="border-orange-200">
              <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50">
                <CardTitle className="text-orange-800">Upload XBRL Files</CardTitle>
                <CardDescription className="text-orange-600">
                  Upload your XBRL instance document
                  {selectedValidationMode?.requiresTaxonomy 
                    ? " en taxonomie bestand voor validatie" 
                    : " - taxonomy bestand niet vereist voor geselecteerde modus"
                  }
                  {selectedDMPTable && (
                    <span className="block mt-1 text-purple-700 font-medium">
                      🎯 DMP Table: {selectedDMPTable} selected for enhanced validation
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <FileUploadZone
                    label="XBRL Instance File"
                    description="Upload your .xbrl or .xml instance document"
                    acceptedTypes=".xbrl,.xml"
                    file={instanceFile}
                    onFileSelect={setInstanceFile}
                    icon={<FileText className="h-8 w-8" />}
                  />
                  
                  {selectedValidationMode?.requiresTaxonomy && (
                    <FileUploadZone
                      label="Taxonomy ZIP File"
                      description="Upload your taxonomy package (.zip containing DPM version)"
                      acceptedTypes=".zip"
                      file={taxonomyFile}
                      onFileSelect={setTaxonomyFile}
                      icon={<Package className="h-8 w-8" />}
                    />
                  )}

                  {!selectedValidationMode?.requiresTaxonomy && (
                    <div className="flex items-center justify-center p-8 border-2 border-dashed border-green-300 rounded-lg bg-green-50">
                      <div className="text-center">
                        <Database className="h-12 w-12 text-green-600 mx-auto mb-2" />
                        <p className="text-green-800 font-medium">Taxonomy niet vereist</p>
                        <p className="text-sm text-green-600">Validatie via DMP database</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Taxonomy Recommendation Card */}
                {instanceFile && selectedValidationMode?.requiresTaxonomy && (
                  <TaxonomyRecommendationCard 
                    instanceFile={instanceFile}
                    onRecommendationSelect={(taxonomyFileName) => {
                      toast({
                        title: "Taxonomy Aanbeveling",
                        description: `Aanbevolen taxonomy bestand: ${taxonomyFileName}`,
                        variant: "default",
                      });
                    }}
                  />
                )}

                <div className="flex justify-center pt-4">
                  <Button 
                    onClick={handleValidation}
                    disabled={!instanceFile || !selectedValidationMode || isValidating}
                    size="lg"
                    className="px-8 bg-orange-600 hover:bg-orange-700 text-white"
                  >
                    {isValidating 
                      ? `Validating (${selectedValidationMode?.name})...` 
                      : `Start ${selectedValidationMode?.name || 'Validation'}`
                    }
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {isValidating && (
            <ValidationProgress 
              instanceFileName={instanceFile?.name || ''}
              taxonomyFileName={taxonomyFile?.name || ''}
            />
          )}

          {validationResult && (
            <>
              <ValidationResultsCard 
                result={validationResult}
                onReset={resetValidation}
              />

              {/* Enhanced DPM Results with Hyperlinks */}
              {validationResult.dpmResults && validationResult.dpmResults.length > 0 && (
                <EnhancedDmpResultsDisplay 
                  dmpResults={validationResult.dpmResults}
                  onViewDatapoint={handleViewDatapoint}
                  onViewInXBRL={handleViewInXBRL}
                />
              )}

              {/* Template Format Generation */}
              <TemplateFormatGenerator validationResult={validationResult} />

              {/* XBRL Value Navigator Modal */}
              {showDatapointViewer && instanceFile && (
                <XBRLValueNavigator
                  instanceFile={instanceFile}
                  selectedConcept={selectedConcept}
                  isOpen={showDatapointViewer}
                  onClose={() => setShowDatapointViewer(false)}
                  validationResult={validationResult}
                />
              )}
            </>
          )}

          {/* XBRL Annotation Section - Always visible */}
          <XBRLAnnotationSection />
        </div>

        {/* Footer */}
        <div className="text-center mt-12 pt-8 border-t border-orange-200">
          <p className="text-orange-600 text-sm">
            © 2024 M4 Solutions - Professional XBRL Validation Services
          </p>
        </div>
      </div>
    </div>
  );
};

export default Index;
