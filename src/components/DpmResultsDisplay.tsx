
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle, XCircle, FileText, AlertTriangle, Info } from "lucide-react";
import { DpmResult } from "@/types/validation";

interface DpmResultsDisplayProps {
  dpmResults: DpmResult[];
}

export const DpmResultsDisplay = ({ dpmResults }: DpmResultsDisplayProps) => {
  const failedResults = dpmResults.filter(result => result.status === 'Failed');
  const passedResults = dpmResults.filter(result => result.status === 'Passed');

  const getStatusIcon = (status: string) => {
    return status === 'Passed' 
      ? <CheckCircle className="h-4 w-4 text-green-500" />
      : <XCircle className="h-4 w-4 text-red-500" />;
  };

  const getStatusBadge = (status: string) => {
    return status === 'Passed' 
      ? <Badge className="bg-green-100 text-green-800 border-green-300">Passed</Badge>
      : <Badge className="bg-red-100 text-red-800 border-red-300">Failed</Badge>;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          📋 DPM Validation Results
        </CardTitle>
        <div className="flex gap-4 text-sm">
          <span className="flex items-center gap-1">
            <XCircle className="h-4 w-4 text-red-500" />
            Failed: {failedResults.length}
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle className="h-4 w-4 text-green-500" />
            Passed: {passedResults.length}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96">
          <div className="space-y-3">
            {dpmResults.map((result, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 ${
                  result.status === 'Failed' 
                    ? 'bg-red-50 border-red-200' 
                    : 'bg-green-50 border-green-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  {getStatusIcon(result.status)}
                  <div className="flex-1 space-y-3">
                    {/* Header with concept and status */}
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs bg-blue-50 text-blue-700 border-blue-200">
                          {result.concept}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {result.rule}
                        </Badge>
                      </div>
                      {getStatusBadge(result.status)}
                    </div>
                    
                    {/* Message */}
                    <div>
                      <p className="text-sm font-medium text-gray-900 leading-relaxed">
                        {result.message}
                      </p>
                    </div>

                    {/* Annotation */}
                    {result.annotation && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Info className="h-3 w-3 text-blue-600" />
                          <span className="text-xs font-semibold text-blue-800">Annotation</span>
                        </div>
                        <p className="text-xs text-blue-700 leading-relaxed">
                          {result.annotation}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
