
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, Check, Loader2, RefreshCw } from "lucide-react";
import { BackendService } from "@/lib/api";
import { Button } from "@/components/ui/button";

export const BackendStatusCard = () => {
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const [debugInfo, setDebugInfo] = useState<{
    workingUrl?: string | null;
    lastError?: string | null;
    detailedErrors?: Array<{url: string, error: string}>;
  }>({});
  
  const backendService = BackendService.getInstance();

  const checkStatus = async () => {
    setIsChecking(true);
    const available = await backendService.checkBackendStatus();
    setBackendAvailable(available);
    setDebugInfo({
      workingUrl: backendService.getWorkingUrl(),
      lastError: backendService.getLastError(),
      detailedErrors: backendService.getDetailedErrors(),
    });
    setIsChecking(false);
  };

  useEffect(() => {
    checkStatus();
  }, [backendService]);

  if (isChecking) {
    return (
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-blue-700">
            <Loader2 className="h-5 w-5 animate-spin" />
            <div>
              <p className="font-medium">🔍 Backend verbinding controleren...</p>
              <p className="text-sm">Zoeken naar Python server...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (backendAvailable === false) {
    return (
      <Card className="mb-6 border-red-200 bg-red-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-2 text-red-700">
            <AlertCircle className="h-5 w-5 mt-0.5" />
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <p className="font-medium">⚠️ Backend niet bereikbaar - Demo modus actief</p>
                <Button
                  onClick={checkStatus}
                  variant="outline"
                  size="sm"
                  className="text-red-700 border-red-300 hover:bg-red-100"
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Opnieuw testen
                </Button>
              </div>
              
              <p className="text-sm mb-3">
                Kan geen verbinding maken met Python server. Je server draait wel, maar CORS is waarschijnlijk niet correct geconfigureerd.
              </p>

              {debugInfo.detailedErrors && debugInfo.detailedErrors.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold">🔍 Geteste URLs:</p>
                  {debugInfo.detailedErrors.map((error, index) => (
                    <div key={index} className="text-xs bg-red-100 px-2 py-1 rounded font-mono">
                      <span className="font-semibold">{error.url}:</span> {error.error}
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-3 p-2 bg-red-100 rounded text-xs">
                <p className="font-semibold">💡 Oplossing:</p>
                <p>Voeg CORS headers toe aan je Flask server:</p>
                <code className="block mt-1 text-xs">
                  pip install flask-cors<br/>
                  from flask_cors import CORS<br/>
                  CORS(app)
                </code>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-6 border-green-200 bg-green-50">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-green-700">
          <Check className="h-5 w-5" />
          <div>
            <p className="font-medium">✅ Backend verbonden</p>
            <p className="text-sm">
              Python backend actief op {debugInfo.workingUrl}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
