
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Database, Table, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { DMPTable, DMPConcept } from "@/types/dmp";

interface DMPTableBrowserProps {
  onTableSelect?: (tableCode: string) => void;
  selectedTable?: string;
}

export const DMPTableBrowser = ({ onTableSelect, selectedTable }: DMPTableBrowserProps) => {
  const [tables, setTables] = useState<DMPTable[]>([]);
  const [concepts, setConcepts] = useState<DMPConcept[]>([]);
  const [loading, setLoading] = useState(false);
  const [conceptsLoading, setConceptsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDMPTables();
  }, []);

  useEffect(() => {
    if (selectedTable) {
      loadTableConcepts(selectedTable);
    }
  }, [selectedTable]);

  const loadDMPTables = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5000/dmp/tables');
      const data = await response.json();
      
      if (data.success) {
        setTables(data.tables);
      } else {
        setError(data.error || 'Failed to load DMP tables');
      }
    } catch (err) {
      setError('Cannot connect to DMP database. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const loadTableConcepts = async (tableCode: string) => {
    setConceptsLoading(true);
    
    try {
      const response = await fetch(`http://localhost:5000/dmp/tables/${tableCode}/concepts`);
      const data = await response.json();
      
      if (data.success) {
        setConcepts(data.concepts);
      } else {
        setError(data.error || 'Failed to load table concepts');
      }
    } catch (err) {
      setError('Cannot load table concepts');
    } finally {
      setConceptsLoading(false);
    }
  };

  const handleTableSelect = (tableCode: string) => {
    onTableSelect?.(tableCode);
  };

  // Fixed filtering logic with proper null checks
  const filteredTables = tables.filter(table =>
    (table.OriginalTableCode?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (table.TableLabel?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  const filteredConcepts = concepts.filter(concept =>
    (concept.DataPointCode?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (concept.DataPointLabel?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (concept.MetricCode?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Card className="border-blue-200">
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Loading DMP tables...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardHeader className="bg-red-50">
          <CardTitle className="text-red-800 flex items-center gap-2">
            <Database className="h-5 w-5" />
            DMP Database Error
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <p className="text-red-700 mb-4">{error}</p>
          <Button onClick={loadDMPTables} variant="outline" size="sm">
            Retry Connection
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-blue-200">
      <CardHeader className="bg-blue-50">
        <CardTitle className="text-blue-800 flex items-center gap-2">
          <Database className="h-5 w-5" />
          EBA DMP Table Browser
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {/* Search */}
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search tables or concepts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Tables List */}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Table className="h-4 w-4" />
              DMP Tables ({filteredTables.length})
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {filteredTables.map((table) => (
                <Button
                  key={table.OriginalTableCode}
                  variant={selectedTable === table.OriginalTableCode ? "default" : "outline"}
                  size="sm"
                  className="w-full text-left justify-start"
                  onClick={() => handleTableSelect(table.OriginalTableCode)}
                >
                  <div className="flex flex-col items-start">
                    <span className="font-mono text-xs">{table.OriginalTableCode}</span>
                    <span className="text-xs text-gray-600 truncate">{table.TableLabel}</span>
                  </div>
                </Button>
              ))}
            </div>
          </div>

          {/* Concepts for Selected Table */}
          {selectedTable && (
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Search className="h-4 w-4" />
                Concepts for {selectedTable} ({filteredConcepts.length})
              </h3>
              {conceptsLoading ? (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <span>Loading concepts...</span>
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {filteredConcepts.map((concept) => (
                    <div
                      key={concept.CellID}
                      className="p-2 border rounded-md bg-gray-50 hover:bg-gray-100"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-mono text-xs text-blue-600">
                            {concept.DataPointCode || concept.MetricCode}
                          </div>
                          <div className="text-xs text-gray-700 truncate">
                            {concept.DataPointLabel || concept.MetricLabel}
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {concept.CellPosition}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
