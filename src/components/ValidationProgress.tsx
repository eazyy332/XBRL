
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Loader2, FileText, Package, CheckCircle, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";

interface ValidationProgressProps {
  instanceFileName: string;
  taxonomyFileName: string;
  selectedTable?: string;
}

export const ValidationProgress = ({ 
  instanceFileName, 
  taxonomyFileName, 
  selectedTable 
}: ValidationProgressProps) => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Uploading files...");
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  useEffect(() => {
    const steps = [
      "Uploading files...",
      "Starting validation engine...",
      "Processing XBRL structure...",
      "Running validation rules...",
      "Generating validation report..."
    ];

    let currentStepIndex = 0;
    const interval = setInterval(() => {
      if (currentStepIndex < steps.length) {
        setCurrentStep(steps[currentStepIndex]);
        setProgress((currentStepIndex + 1) * (100 / steps.length));
        
        if (currentStepIndex > 0) {
          setCompletedSteps(prev => [...prev, steps[currentStepIndex - 1]]);
        }
        
        currentStepIndex++;
      } else {
        clearInterval(interval);
      }
    }, 1500); // Faster updates for better UX

    return () => clearInterval(interval);
  }, [selectedTable]);

  return (
    <Card className="max-w-2xl mx-auto border-orange-200">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50">
        <CardTitle className="flex items-center gap-2 text-orange-800">
          <Loader2 className="h-5 w-5 animate-spin" />
          Fast XBRL Validation in Progress
        </CardTitle>
        <CardDescription className="text-orange-600">
          Processing your XBRL files with optimized validation engine
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6 space-y-6">
        {/* File Information */}
        <div className="grid md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <FileText className="h-5 w-5 text-blue-600" />
            <div>
              <p className="font-medium text-blue-800">Instance File</p>
              <p className="text-sm text-blue-600 truncate">{instanceFileName}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
            <Package className="h-5 w-5 text-purple-600" />
            <div>
              <p className="font-medium text-purple-800">Taxonomy</p>
              <p className="text-sm text-purple-600 truncate">{taxonomyFileName}</p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Validation Progress</span>
            <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-3" />
        </div>

        {/* Current Step */}
        <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-lg border border-orange-200">
          <Loader2 className="h-5 w-5 text-orange-600 animate-spin" />
          <div>
            <p className="font-medium text-orange-800">Current Step</p>
            <p className="text-sm text-orange-600">{currentStep}</p>
          </div>
        </div>

        {/* Completed Steps */}
        {completedSteps.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Completed Steps:</p>
            {completedSteps.map((step, index) => (
              <div key={index} className="flex items-center gap-2 text-sm text-green-700">
                <CheckCircle className="h-4 w-4" />
                <span>{step}</span>
              </div>
            ))}
          </div>
        )}

        {/* Processing Notice */}
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-green-800">Fast Mode Enabled</p>
              <p className="text-xs text-green-600 mt-1">
                Validation optimized for speed - should complete within 3 minutes
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
