
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";
import type { DMPStatus } from "@/types/dmp";

export const DMPStatusCard = () => {
  const [status, setStatus] = useState<DMPStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkDMPStatus();
  }, []);

  const checkDMPStatus = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:5000/dmp/status');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      setStatus({
        status: 'error',
        message: 'Cannot connect to DMP database service',
        dmp_database: {
          status: 'error',
          message: 'Backend connection failed'
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Check if database is connected by looking at the nested structure
  const databaseStatus = status?.dmp_database?.status;
  const isConnected = databaseStatus === 'connected';
  const hasError = databaseStatus === 'error' || databaseStatus === 'permission_error';

  return (
    <Card className={`border-2 ${isConnected ? 'border-green-200' : hasError ? 'border-red-200' : 'border-yellow-200'}`}>
      <CardHeader className={`${isConnected ? 'bg-green-50' : hasError ? 'bg-red-50' : 'bg-yellow-50'}`}>
        <CardTitle className={`flex items-center gap-2 ${isConnected ? 'text-green-800' : hasError ? 'text-red-800' : 'text-yellow-800'}`}>
          <Database className="h-5 w-5" />
          EBA DMP Database Status
          <Badge variant={isConnected ? "default" : "destructive"} className="ml-auto">
            {loading ? (
              <RefreshCw className="h-3 w-3 animate-spin mr-1" />
            ) : isConnected ? (
              <CheckCircle2 className="h-3 w-3 mr-1" />
            ) : (
              <AlertCircle className="h-3 w-3 mr-1" />
            )}
            {loading ? 'Checking...' : databaseStatus || 'Unknown'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Backend Status */}
          <div className="text-sm">
            <strong>Backend Status:</strong> 
            <span className={`ml-2 ${status?.status === 'active' ? 'text-green-700' : 'text-red-700'}`}>
              {status?.status || 'Unknown'}
            </span>
          </div>

          {/* Backend Message */}
          {status?.message && (
            <p className="text-sm text-gray-600">
              <strong>Backend:</strong> {status.message}
            </p>
          )}

          {/* Database Message */}
          <p className={`text-sm ${isConnected ? 'text-green-700' : hasError ? 'text-red-700' : 'text-yellow-700'}`}>
            <strong>Database:</strong> {status?.dmp_database?.message || 'Checking database connection...'}
          </p>
          
          {/* Database Details */}
          {status?.dmp_database?.dmp_tables && (
            <div className="text-sm text-gray-600">
              <strong>Tables available:</strong> {status.dmp_database.dmp_tables}
            </div>
          )}
          
          {status?.dmp_database?.database_path && (
            <div className="text-sm text-gray-600">
              <strong>Database path:</strong> 
              <code className="ml-1 bg-gray-100 px-1 rounded text-xs">
                {status.dmp_database.database_path}
              </code>
            </div>
          )}
          
          {status?.dmp_database?.sample_tables && status.dmp_database.sample_tables.length > 0 && (
            <div className="text-sm text-gray-600">
              <strong>Sample tables:</strong>
              <div className="mt-1 space-y-1">
                {status.dmp_database.sample_tables.map((table, idx) => (
                  <div key={idx} className="text-xs bg-gray-50 p-1 rounded">
                    {table.table}: {table.rows} rows
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Backend Features */}
          {status?.features && (
            <div className="text-sm text-gray-600">
              <strong>Available features:</strong>
              <div className="mt-1 flex flex-wrap gap-1">
                {Object.entries(status.features).map(([feature, enabled]) => (
                  enabled && (
                    <span key={feature} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {feature.replace(/_/g, ' ')}
                    </span>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Troubleshooting */}
          {status?.dmp_database?.troubleshooting && (
            <div className="text-sm text-orange-600 bg-orange-50 p-2 rounded">
              <strong>Troubleshooting:</strong> {status.dmp_database.troubleshooting}
            </div>
          )}
          
          <div className="flex gap-2 pt-2">
            <Button 
              onClick={checkDMPStatus} 
              size="sm" 
              variant="outline"
              disabled={loading}
            >
              {loading ? (
                <RefreshCw className="h-3 w-3 animate-spin mr-1" />
              ) : (
                <RefreshCw className="h-3 w-3 mr-1" />
              )}
              Refresh Status
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
