import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Info, FileText, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Alert, AlertDescription } from "./ui/alert";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

interface TaxonomyAnalysis {
  file_info: {
    filename: string;
    analysis_timestamp: string;
  };
  detected_version: string;
  confidence: string;
  recommendations: Array<{
    type: string;
    title: string;
    message: string;
    taxonomy_file?: string;
    action?: string;
    confidence?: string;
  }>;
  namespace_analysis: {
    total_namespaces: number;
    eba_namespaces: Record<string, string>;
    version_indicators: string[];
  };
  schema_references: string[];
  reporting_period: string | null;
  entity_info: Record<string, string>;
}

interface TaxonomyRecommendationCardProps {
  instanceFile: File | null;
  onRecommendationSelect?: (taxonomyFile: string) => void;
}

export const TaxonomyRecommendationCard = ({ 
  instanceFile, 
  onRecommendationSelect 
}: TaxonomyRecommendationCardProps) => {
  const [analysis, setAnalysis] = useState<TaxonomyAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!instanceFile) {
      setAnalysis(null);
      setError(null);
      return;
    }

    analyzeInstanceFile();
  }, [instanceFile]);

  const analyzeInstanceFile = async () => {
    if (!instanceFile) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('instance', instanceFile);

      console.log('🔍 Sending request to /api/analyze-taxonomy-requirements...');
      
      const response = await fetch('/api/analyze-taxonomy-requirements', {
        method: 'POST',
        body: formData
      });

      console.log('📡 Response received:', response.status, response.statusText);

      if (!response.ok) {
        // Handle different error types
        if (response.status === 404) {
          throw new Error('Backend niet beschikbaar. Start eerst de Flask backend server.');
        } else if (response.status === 500) {
          const errorText = await response.text();
          throw new Error(`Server fout: ${errorText}`);
        } else {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
      }

      const result = await response.json();

      if (result.success) {
        setAnalysis(result.taxonomy_analysis);
        console.log('✅ Taxonomy analysis completed:', result.taxonomy_analysis);
      } else {
        setError(result.error || 'Analyse van taxonomy requirements mislukt');
      }
    } catch (err: any) {
      console.error('❌ Taxonomy analysis error:', err);
      
      // Provide specific error messages based on error type
      if (err.message.includes('fetch')) {
        setError('Kan geen verbinding maken met backend. Controleer of de Flask server actief is op poort 5000.');
      } else if (err.message.includes('Backend niet beschikbaar')) {
        setError('Backend server niet beschikbaar. Start de Flask backend server met: python src/python/enhanced_backend_with_dmp.py');
      } else {
        setError(err.message || 'Verbinding met backend mislukt');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-success';
      case 'medium': return 'text-warning';
      case 'low': return 'text-muted-foreground';
      default: return 'text-muted-foreground';
    }
  };

  const getRecommendationIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="h-4 w-4 text-success" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-warning" />;
      case 'info': return <Info className="h-4 w-4 text-info" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  if (!instanceFile) {
    return (
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Taxonomy Versie Analyse
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Upload eerst een XBRL bestand om de vereiste taxonomy versie te detecteren.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isAnalyzing) {
    return (
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Taxonomy Versie Analyse
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Analyzing {instanceFile.name}...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Taxonomy Analyse Fout
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button 
            variant="outline" 
            onClick={analyzeInstanceFile}
            className="mt-3"
            size="sm"
          >
            Opnieuw proberen
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!analysis) return null;

  return (
    <Card className="bg-muted/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Taxonomy Versie Aanbeveling
        </CardTitle>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Gedetecteerd:</span>
          <Badge variant="secondary">
            {analysis.detected_version !== 'unknown' 
              ? analysis.detected_version 
              : 'Onbekend'
            }
          </Badge>
          {analysis.confidence && (
            <span className={getConfidenceColor(analysis.confidence)}>
              ({analysis.confidence} confidence)
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* File Analysis Summary */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Namespaces gevonden:</span>
            <span className="ml-2 text-muted-foreground">
              {analysis.namespace_analysis.total_namespaces}
            </span>
          </div>
          <div>
            <span className="font-medium">EBA namespaces:</span>
            <span className="ml-2 text-muted-foreground">
              {Object.keys(analysis.namespace_analysis.eba_namespaces).length}
            </span>
          </div>
          <div>
            <span className="font-medium">Schema referenties:</span>
            <span className="ml-2 text-muted-foreground">
              {analysis.schema_references.length}
            </span>
          </div>
          <div>
            <span className="font-medium">Rapportage periode:</span>
            <span className="ml-2 text-muted-foreground">
              {analysis.reporting_period || 'Niet gevonden'}
            </span>
          </div>
        </div>

        {/* Version Indicators */}
        {analysis.namespace_analysis.version_indicators.length > 0 && (
          <div>
            <span className="text-sm font-medium">Versie indicatoren:</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {analysis.namespace_analysis.version_indicators.map((indicator, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {indicator}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Aanbevelingen:</h4>
          {analysis.recommendations.map((rec, index) => (
            <Alert key={index}>
              <div className="flex items-start gap-3">
                {getRecommendationIcon(rec.type)}
                <div className="flex-1">
                  <div className="font-medium text-sm">{rec.title}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {rec.message}
                  </div>
                  {rec.taxonomy_file && (
                    <div className="mt-2 flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onRecommendationSelect?.(rec.taxonomy_file!)}
                        className="text-xs"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Gebruik {rec.taxonomy_file}
                      </Button>
                      {rec.confidence && (
                        <Badge variant="secondary" className="text-xs">
                          {rec.confidence} confidence
                        </Badge>
                      )}
                    </div>
                  )}
                  {rec.action && (
                    <div className="mt-1 text-xs text-muted-foreground">
                      💡 {rec.action}
                    </div>
                  )}
                </div>
              </div>
            </Alert>
          ))}
        </div>

        {/* EBA Namespaces Detail */}
        {Object.keys(analysis.namespace_analysis.eba_namespaces).length > 0 && (
          <details className="text-sm">
            <summary className="font-medium cursor-pointer">
              EBA Namespaces ({Object.keys(analysis.namespace_analysis.eba_namespaces).length})
            </summary>
            <div className="mt-2 space-y-1 pl-4">
              {Object.entries(analysis.namespace_analysis.eba_namespaces).map(([prefix, uri]) => (
                <div key={prefix} className="text-xs">
                  <span className="font-mono text-muted-foreground">{prefix}:</span>
                  <span className="ml-2 break-all">{uri}</span>
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Schema References Detail */}
        {analysis.schema_references.length > 0 && (
          <details className="text-sm">
            <summary className="font-medium cursor-pointer">
              Schema Referenties ({analysis.schema_references.length})
            </summary>
            <div className="mt-2 space-y-1 pl-4">
              {analysis.schema_references.slice(0, 5).map((ref, index) => (
                <div key={index} className="text-xs break-all text-muted-foreground">
                  {ref}
                </div>
              ))}
              {analysis.schema_references.length > 5 && (
                <div className="text-xs text-muted-foreground">
                  ... en {analysis.schema_references.length - 5} meer
                </div>
              )}
            </div>
          </details>
        )}
      </CardContent>
    </Card>
  );
};