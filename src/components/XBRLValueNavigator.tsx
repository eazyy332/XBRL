
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Search, ExternalLink, Info, TrendingUp, Calendar, DollarSign, Hash } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ValidationResult } from "@/types/validation";

interface XBRLValueNavigatorProps {
  instanceFile: File;
  selectedConcept: string;
  isOpen: boolean;
  onClose: () => void;
  validationResult?: ValidationResult;
}

interface ConceptValue {
  concept: string;
  value: string;
  unitRef?: string;
  contextRef?: string;
  decimals?: string;
  scale?: string;
  period?: string;
  entity?: string;
}

interface ConceptContext {
  id: string;
  entity: string;
  period: string;
  scenario?: string;
}

export const XBRLValueNavigator = ({ 
  instanceFile, 
  selectedConcept, 
  isOpen, 
  onClose,
  validationResult 
}: XBRLValueNavigatorProps) => {
  const [xbrlContent, setXbrlContent] = useState<string>("");
  const [conceptValues, setConceptValues] = useState<ConceptValue[]>([]);
  const [contexts, setContexts] = useState<ConceptContext[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (isOpen && instanceFile) {
      loadXBRLContent();
    }
  }, [isOpen, instanceFile]);

  useEffect(() => {
    if (selectedConcept) {
      setSearchTerm(selectedConcept);
    }
  }, [selectedConcept]);

  const loadXBRLContent = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      const content = await instanceFile.text();
      setXbrlContent(content);
      
      // Parse XBRL content to extract concept values and contexts
      const parsedValues = parseConceptValues(content);
      const parsedContexts = parseContexts(content);
      
      setConceptValues(parsedValues);
      setContexts(parsedContexts);
    } catch (err: any) {
      console.error("Error loading XBRL content:", err);
      setError(err.message || "Failed to load XBRL content");
    } finally {
      setIsLoading(false);
    }
  };

  const parseConceptValues = (content: string): ConceptValue[] => {
    const values: ConceptValue[] = [];
    
    try {
      // Simple regex-based parsing for XBRL elements
      const conceptRegex = /<([^:>\s]+:[^>\s]+)[^>]*(?:contextRef="([^"]*)")?(?:unitRef="([^"]*)")?(?:decimals="([^"]*)")?[^>]*>([^<]+)<\/[^>]+>/g;
      
      let match;
      while ((match = conceptRegex.exec(content)) !== null) {
        const [, concept, contextRef, unitRef, decimals, value] = match;
        
        if (concept && value && !concept.includes('context') && !concept.includes('unit')) {
          values.push({
            concept: concept.trim(),
            value: value.trim(),
            contextRef,
            unitRef,
            decimals
          });
        }
      }
    } catch (err) {
      console.warn("Error parsing concept values:", err);
    }
    
    return values;
  };

  const parseContexts = (content: string): ConceptContext[] => {
    const contexts: ConceptContext[] = [];
    
    try {
      // Parse context elements
      const contextRegex = /<context[^>]*id="([^"]*)"[^>]*>(.*?)<\/context>/gs;
      
      let match;
      while ((match = contextRegex.exec(content)) !== null) {
        const [, id, contextContent] = match;
        
        // Extract entity and period from context content
        const entityMatch = contextContent.match(/<identifier[^>]*>([^<]+)<\/identifier>/);
        const periodMatch = contextContent.match(/<instant>([^<]+)<\/instant>|<startDate>([^<]+)<\/startDate>.*?<endDate>([^<]+)<\/endDate>/s);
        
        contexts.push({
          id,
          entity: entityMatch ? entityMatch[1] : 'Unknown',
          period: periodMatch ? (periodMatch[1] || `${periodMatch[2]} to ${periodMatch[3]}`) : 'Unknown'
        });
      }
    } catch (err) {
      console.warn("Error parsing contexts:", err);
    }
    
    return contexts;
  };

  const filteredValues = conceptValues.filter(cv => 
    searchTerm === "" || 
    cv.concept.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cv.value.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getConceptDetails = (concept: string) => {
    return validationResult?.dpmResults?.find(result => result.concept === concept);
  };

  const formatValue = (value: string, unitRef?: string) => {
    // Try to format numeric values
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(numValue);
    }
    return value;
  };

  const getValueIcon = (concept: string) => {
    const lower = concept.toLowerCase();
    if (lower.includes('asset') || lower.includes('revenue')) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (lower.includes('date') || lower.includes('period')) return <Calendar className="h-4 w-4 text-blue-600" />;
    if (lower.includes('amount') || lower.includes('value')) return <DollarSign className="h-4 w-4 text-yellow-600" />;
    return <Hash className="h-4 w-4 text-gray-600" />;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ExternalLink className="h-5 w-5" />
            XBRL Value Navigator - {instanceFile.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Bar */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search concepts, values, or rules..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <span className="text-sm text-gray-600 min-w-fit">
              {filteredValues.length} value{filteredValues.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* Content Tabs */}
          <Tabs defaultValue="values" className="h-[60vh]">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="values">Concept Values</TabsTrigger>
              <TabsTrigger value="contexts">Contexts</TabsTrigger>
              <TabsTrigger value="raw">Raw XBRL</TabsTrigger>
            </TabsList>

            <TabsContent value="values" className="h-full mt-4">
              <ScrollArea className="h-full">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <span className="ml-3 text-gray-600">Loading XBRL values...</span>
                  </div>
                ) : error ? (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertDescription className="text-red-800">
                      Error: {error}
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="space-y-3">
                    {filteredValues.map((cv, index) => {
                      const conceptDetails = getConceptDetails(cv.concept);
                      const context = contexts.find(c => c.id === cv.contextRef);
                      
                      return (
                        <div
                          key={index}
                          className={`p-4 border rounded-lg transition-colors ${
                            cv.concept === selectedConcept
                              ? 'bg-blue-50 border-blue-300 shadow-md'
                              : 'bg-white border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            {getValueIcon(cv.concept)}
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2 flex-wrap">
                                <Badge variant="outline" className="font-mono text-xs bg-blue-50 text-blue-700 border-blue-200">
                                  {cv.concept}
                                </Badge>
                                {conceptDetails && (
                                  <Badge
                                    className={
                                      conceptDetails.status === 'Passed'
                                        ? 'bg-green-100 text-green-800 border-green-300'
                                        : 'bg-red-100 text-red-800 border-red-300'
                                    }
                                  >
                                    {conceptDetails.status}
                                  </Badge>
                                )}
                              </div>
                              
                              <div className="bg-gray-50 p-3 rounded border">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-sm font-medium text-gray-700">Value:</span>
                                  <span className="text-lg font-bold text-gray-900">
                                    {formatValue(cv.value, cv.unitRef)}
                                  </span>
                                  {cv.unitRef && (
                                    <Badge variant="secondary" className="text-xs">
                                      {cv.unitRef}
                                    </Badge>
                                  )}
                                </div>
                                
                                {context && (
                                  <div className="text-xs text-gray-600 space-y-1">
                                    <div><strong>Entity:</strong> {context.entity}</div>
                                    <div><strong>Period:</strong> {context.period}</div>
                                    {cv.decimals && <div><strong>Decimals:</strong> {cv.decimals}</div>}
                                  </div>
                                )}
                              </div>

                              {conceptDetails && (
                                <div className="bg-blue-50 border border-blue-200 rounded p-2">
                                  <div className="text-xs">
                                    <div><strong>Rule:</strong> {conceptDetails.rule}</div>
                                    <div><strong>Message:</strong> {conceptDetails.message}</div>
                                    {conceptDetails.annotation && (
                                      <div><strong>Annotation:</strong> {conceptDetails.annotation}</div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    
                    {filteredValues.length === 0 && (
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          No concept values found matching your search criteria.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="contexts" className="h-full mt-4">
              <ScrollArea className="h-full">
                <div className="space-y-3">
                  {contexts.map((context, index) => (
                    <div key={index} className="p-4 border rounded-lg bg-white">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="font-mono">
                          {context.id}
                        </Badge>
                      </div>
                      <div className="text-sm space-y-1">
                        <div><strong>Entity:</strong> {context.entity}</div>
                        <div><strong>Period:</strong> {context.period}</div>
                        {context.scenario && <div><strong>Scenario:</strong> {context.scenario}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="raw" className="h-full mt-4">
              <ScrollArea className="h-full">
                <pre className="text-xs font-mono whitespace-pre-wrap break-words text-gray-800 bg-gray-50 p-4 rounded border">
                  {xbrlContent}
                </pre>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
};
