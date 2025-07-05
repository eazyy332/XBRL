
import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DpmResult {
  concept: string;
  ruleId: string;
  status: 'passed' | 'failed';
  message: string;
  annotation?: string;
}

interface DpmResultsTableProps {
  results: DpmResult[];
}

type SortColumn = 'concept' | 'ruleId' | 'status';
type SortDirection = 'asc' | 'desc' | null;

export const DpmResultsTable = ({ results }: DpmResultsTableProps) => {
  const [sortColumn, setSortColumn] = useState<SortColumn | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortColumn(null);
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const sortedResults = useMemo(() => {
    if (!sortColumn || !sortDirection) {
      return results;
    }

    return [...results].sort((a, b) => {
      let aValue: string | number = a[sortColumn];
      let bValue: string | number = b[sortColumn];

      // Voor status sortering, failed eerst bij asc
      if (sortColumn === 'status') {
        aValue = a.status === 'failed' ? 0 : 1;
        bValue = b.status === 'failed' ? 0 : 1;
      }

      if (sortDirection === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
  }, [results, sortColumn, sortDirection]);

  const getSortIcon = (column: SortColumn) => {
    if (sortColumn !== column) {
      return <ArrowUpDown className="h-4 w-4" />;
    }
    if (sortDirection === 'asc') {
      return <ArrowUp className="h-4 w-4" />;
    }
    if (sortDirection === 'desc') {
      return <ArrowDown className="h-4 w-4" />;
    }
    return <ArrowUpDown className="h-4 w-4" />;
  };

  const getStatusIcon = (status: 'passed' | 'failed') => {
    return status === 'passed' ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-red-600" />
    );
  };

  const getRowClassName = (status: 'passed' | 'failed') => {
    return status === 'failed' 
      ? 'bg-red-50 border-red-100 hover:bg-red-100' 
      : 'hover:bg-green-50';
  };

  const failedCount = results.filter(r => r.status === 'failed').length;
  const passedCount = results.filter(r => r.status === 'passed').length;

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-gray-900">
          DPM Validatieregels
        </CardTitle>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-green-700">{passedCount} geslaagd</span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-red-600" />
            <span className="text-red-700">{failedCount} gefaald</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {results.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Geen fouten gevonden
            </h3>
            <p className="text-gray-600">
              Alle DPM validatieregels zijn succesvol gevalideerd.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <Button
                      variant="ghost"
                      className="h-auto p-0 font-semibold hover:bg-transparent"
                      onClick={() => handleSort('concept')}
                    >
                      <span className="flex items-center gap-2">
                        Concept
                        {getSortIcon('concept')}
                      </span>
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      className="h-auto p-0 font-semibold hover:bg-transparent"
                      onClick={() => handleSort('ruleId')}
                    >
                      <span className="flex items-center gap-2">
                        Rule ID
                        {getSortIcon('ruleId')}
                      </span>
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      className="h-auto p-0 font-semibold hover:bg-transparent"
                      onClick={() => handleSort('status')}
                    >
                      <span className="flex items-center gap-2">
                        Status
                        {getSortIcon('status')}
                      </span>
                    </Button>
                  </TableHead>
                  <TableHead className="hidden sm:table-cell">Message</TableHead>
                  <TableHead className="hidden md:table-cell">Annotation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedResults.map((result, index) => (
                  <TableRow key={index} className={getRowClassName(result.status)}>
                    <TableCell className="font-medium">
                      <div className="font-mono text-sm break-all">
                        {result.concept}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">
                        {result.ruleId}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(result.status)}
                        <span className="hidden sm:inline capitalize">
                          {result.status === 'passed' ? 'Geslaagd' : 'Gefaald'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">
                      <div className="max-w-md">
                        <p className="text-sm leading-relaxed break-words">
                          {result.message}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      {result.annotation && (
                        <div className="max-w-sm">
                          <p className="text-xs text-gray-600 leading-relaxed break-words">
                            {result.annotation}
                          </p>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            
            {/* Mobile-friendly details voor kleine schermen */}
            <div className="sm:hidden mt-4 space-y-4">
              {sortedResults.map((result, index) => (
                <div 
                  key={index} 
                  className={`p-4 rounded-lg border ${
                    result.status === 'failed' 
                      ? 'bg-red-50 border-red-200' 
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(result.status)}
                    <span className="font-semibold capitalize">
                      {result.status === 'passed' ? 'Geslaagd' : 'Gefaald'}
                    </span>
                    <Badge variant="outline" className="ml-auto font-mono text-xs">
                      {result.ruleId}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Concept:</p>
                      <p className="font-mono text-sm break-all">{result.concept}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Message:</p>
                      <p className="text-sm">{result.message}</p>
                    </div>
                    {result.annotation && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Annotation:</p>
                        <p className="text-xs text-gray-600">{result.annotation}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
