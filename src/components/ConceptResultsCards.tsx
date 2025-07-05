
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp, CheckCircle, XCircle, Search, FileText, Folder, BookOpen, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ConceptResult {
  concept: string;
  rule: string;
  description: string;
  template_code: string;
  note?: string;
  severity: 'Blocking' | 'Non-blocking' | 'passed';
  status: 'passed' | 'failed';
}

interface ConceptResultsCardsProps {
  results: ConceptResult[];
}

export const ConceptResultsCards = ({ results }: ConceptResultsCardsProps) => {
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());

  const toggleCard = (index: number) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedCards(newExpanded);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Blocking':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'Non-blocking':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'passed':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: 'passed' | 'failed') => {
    return status === 'passed' ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-red-600" />
    );
  };

  const getCardBorderColor = (severity: string, status: string) => {
    if (status === 'failed') {
      return severity === 'Blocking' 
        ? 'border-red-300 shadow-red-100' 
        : 'border-orange-300 shadow-orange-100';
    }
    return 'border-green-300 shadow-green-100';
  };

  const passedCount = results.filter(r => r.status === 'passed').length;
  const failedCount = results.filter(r => r.status === 'failed').length;
  const blockingCount = results.filter(r => r.severity === 'Blocking' && r.status === 'failed').length;

  if (results.length === 0) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-gray-900">
            Concept Validatieresultaten
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Geen concept validaties uitgevoerd
            </h3>
            <p className="text-gray-600">
              Er zijn geen concept validatieresultaten gevonden.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-gray-900">
            Concept Validatieresultaten
          </CardTitle>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-green-700">{passedCount} geslaagd</span>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-600" />
              <span className="text-red-700">{failedCount} gefaald</span>
            </div>
            {blockingCount > 0 && (
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <span className="text-red-700">{blockingCount} blocking</span>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {results.map((result, index) => {
          const isExpanded = expandedCards.has(index);
          
          return (
            <Card 
              key={index} 
              className={`shadow-sm transition-all duration-200 ${getCardBorderColor(result.severity, result.status)}`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    {getStatusIcon(result.status)}
                    <Badge 
                      variant="outline" 
                      className={`text-xs font-medium ${getSeverityColor(result.severity)}`}
                    >
                      {result.severity}
                    </Badge>
                  </div>
                  <Badge variant="secondary" className="font-mono text-xs shrink-0">
                    {result.rule}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <Search className="h-4 w-4 text-gray-500 mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs text-gray-500 mb-1">Concept:</p>
                      <p className="font-mono text-sm break-all text-gray-900">
                        {result.concept}
                      </p>
                    </div>
                  </div>
                  
                  {result.template_code && (
                    <div className="flex items-center gap-2">
                      <Folder className="h-4 w-4 text-gray-500 shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">Template:</p>
                        <p className="font-medium text-sm text-gray-900">
                          {result.template_code}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                <Collapsible open={isExpanded} onOpenChange={() => toggleCard(index)}>
                  <CollapsibleTrigger asChild>
                    <Button 
                      variant="ghost" 
                      className="w-full justify-between h-auto p-2 text-sm font-medium hover:bg-gray-50"
                    >
                      <span className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Toon details
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </CollapsibleTrigger>

                  <CollapsibleContent className="mt-3 space-y-3">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-start gap-2 mb-2">
                        <BookOpen className="h-4 w-4 text-gray-500 mt-0.5 shrink-0" />
                        <p className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                          Beschrijving
                        </p>
                      </div>
                      <p className="text-sm text-gray-900 leading-relaxed">
                        {result.description}
                      </p>
                    </div>

                    {result.note && (
                      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="flex items-start gap-2 mb-2">
                          <BookOpen className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                          <p className="text-xs font-medium text-blue-700 uppercase tracking-wide">
                            Notitie
                          </p>
                        </div>
                        <p className="text-sm text-blue-900 leading-relaxed">
                          {result.note}
                        </p>
                      </div>
                    )}
                  </CollapsibleContent>
                </Collapsible>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
