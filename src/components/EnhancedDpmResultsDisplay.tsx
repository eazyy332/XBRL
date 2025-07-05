
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CheckCircle, XCircle, Search, ExternalLink, Eye } from "lucide-react";

interface DmpResult {
  concept: string;
  rule: string;
  message: string;
  annotation: string;
  status: 'Passed' | 'Failed';
}

interface EnhancedDmpResultsDisplayProps {
  dmpResults: DmpResult[];
  onViewDatapoint?: (concept: string) => void;
  onViewInXBRL?: (concept: string) => void;
}

export const EnhancedDmpResultsDisplay = ({ 
  dmpResults, 
  onViewDatapoint,
  onViewInXBRL 
}: EnhancedDmpResultsDisplayProps) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<'all' | 'Passed' | 'Failed'>('all');

  const filteredResults = dmpResults.filter(result => {
    const matchesSearch = searchTerm === "" || 
      result.concept.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.rule.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.message.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || result.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const failedCount = dmpResults.filter(r => r.status === 'Failed').length;
  const passedCount = dmpResults.filter(r => r.status === 'Passed').length;

  const handleViewDatapoint = (concept: string) => {
    if (onViewDatapoint) {
      onViewDatapoint(concept);
    } else {
      // Fallback to console log if no handler provided
      console.log(`Viewing datapoint: ${concept}`);
    }
  };

  const handleViewInXBRL = (concept: string) => {
    if (onViewInXBRL) {
      onViewInXBRL(concept);
    } else {
      // Fallback to console log if no handler provided
      console.log(`Viewing in XBRL: ${concept}`);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>DPM Validation Results</span>
          <div className="flex gap-2">
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
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search and Filter Controls */}
        <div className="flex gap-4 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search concepts, rules, or messages..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('all')}
            >
              All
            </Button>
            <Button
              variant={statusFilter === 'Passed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('Passed')}
              className={statusFilter === 'Passed' ? 'bg-green-600 hover:bg-green-700' : ''}
            >
              Passed
            </Button>
            <Button
              variant={statusFilter === 'Failed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('Failed')}
              className={statusFilter === 'Failed' ? 'bg-red-600 hover:bg-red-700' : ''}
            >
              Failed
            </Button>
          </div>
        </div>

        {/* Results List */}
        <div className="space-y-3">
          {filteredResults.map((result, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border transition-colors ${
                result.status === 'Passed'
                  ? 'bg-green-50 border-green-200 hover:bg-green-100'
                  : 'bg-red-50 border-red-200 hover:bg-red-100'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {result.status === 'Passed' ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-600" />
                    )}
                    <Badge
                      className={
                        result.status === 'Passed'
                          ? 'bg-green-100 text-green-800 border-green-300'
                          : 'bg-red-100 text-red-800 border-red-300'
                      }
                    >
                      {result.status}
                    </Badge>
                    <span className="text-sm font-medium text-gray-600">{result.rule}</span>
                  </div>
                  
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Concept: </span>
                      <button
                        onClick={() => handleViewDatapoint(result.concept)}
                        className="text-blue-600 hover:text-blue-800 hover:underline font-mono text-sm"
                      >
                        {result.concept}
                        <ExternalLink className="inline h-3 w-3 ml-1" />
                      </button>
                    </div>
                    
                    <div>
                      <span className="text-sm font-medium text-gray-700">Message: </span>
                      <span className="text-sm text-gray-600">{result.message}</span>
                    </div>
                    
                    {result.annotation && (
                      <div>
                        <span className="text-sm font-medium text-gray-700">Annotation: </span>
                        <span className="text-sm text-gray-600 italic">{result.annotation}</span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2 ml-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleViewDatapoint(result.concept)}
                    className="text-blue-600 border-blue-300 hover:bg-blue-50"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    View Value
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleViewInXBRL(result.concept)}
                    className="text-purple-600 border-purple-300 hover:bg-purple-50"
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    View in XBRL
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredResults.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No results match your search criteria.</p>
            {searchTerm && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSearchTerm("")}
                className="mt-2"
              >
                Clear Search
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
