
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, CheckCircle, Loader } from "lucide-react";
import { BackendService } from "@/lib/api";

export const BackendStatus = () => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const backendService = BackendService.getInstance();

  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    setStatus('checking');
    const isAvailable = await backendService.checkBackendStatus();
    setStatus(isAvailable ? 'connected' : 'disconnected');
  };

  if (status === 'checking') {
    return (
      <Card className="max-w-4xl mx-auto mb-6 border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-blue-800">
            <Loader className="h-5 w-5 animate-spin" />
            <div>
              <p className="font-medium">Checking Backend Connection</p>
              <p className="text-sm text-blue-700">
                Connecting to Python validation server...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (status === 'connected') {
    return (
      <Card className="max-w-4xl mx-auto mb-6 border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-green-800">
            <CheckCircle className="h-5 w-5" />
            <div>
              <p className="font-medium">Backend Connected</p>
              <p className="text-sm text-green-700">
                Python validation server is running at localhost:5000
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-4xl mx-auto mb-6 border-red-200 bg-red-50">
      <CardContent className="pt-6">
        <div className="flex items-center gap-3 text-red-800">
          <AlertTriangle className="h-5 w-5" />
          <div>
            <p className="font-medium">⚠️ Backend not reachable. Running in demo mode.</p>
            <p className="text-sm text-red-700">
              Unable to connect to Python validation server at localhost:5000. 
              Please ensure your backend is running and try again.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
