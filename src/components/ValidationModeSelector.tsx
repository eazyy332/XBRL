import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Clock, Database, FileText, Zap, CheckCircle2 } from "lucide-react";

export interface ValidationMode {
  mode: string;
  name: string;
  description: string;
  requiresTaxonomy: boolean;
  estimatedTime: string;
  features: string[];
}

interface ValidationModeSelectorProps {
  onModeSelect: (mode: ValidationMode) => void;
  selectedMode: ValidationMode | null;
  backendAvailable: boolean;
}

export const ValidationModeSelector = ({ 
  onModeSelect, 
  selectedMode, 
  backendAvailable 
}: ValidationModeSelectorProps) => {
  const [availableModes, setAvailableModes] = useState<ValidationMode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadValidationModes();
  }, [backendAvailable]);

  const loadValidationModes = async () => {
    if (!backendAvailable) {
      // Fallback modes when backend is not available
      setAvailableModes([
        {
          mode: "javascript",
          name: "JavaScript Validatie",
          description: "Basis client-side validatie zonder server",
          requiresTaxonomy: true,
          estimatedTime: "5-10 seconden",
          features: ["Basic checks", "No server required", "Limited validation"]
        }
      ]);
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/validation-modes');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAvailableModes(data.modes);
        }
      } else {
        // Fallback to default modes
        setAvailableModes(getDefaultModes());
      }
    } catch (error) {
      console.error('Failed to load validation modes:', error);
      setAvailableModes(getDefaultModes());
    } finally {
      setLoading(false);
    }
  };

  const getDefaultModes = (): ValidationMode[] => [
    {
      mode: "fast",
      name: "Snelle DMP Validatie",
      description: "Validatie direct vanuit DMP database zonder taxonomy bestand",
      requiresTaxonomy: false,
      estimatedTime: "30-60 seconden",
      features: ["DMP rules", "No taxonomy needed", "Fast processing"]
    },
    {
      mode: "enhanced",
      name: "DMP + Taxonomy Validatie", 
      description: "Arelle validatie gecombineerd met DMP enhancement",
      requiresTaxonomy: true,
      estimatedTime: "2-3 minuten",
      features: ["Full Arelle validation", "DMP enhancement", "Complete rule set"]
    }
  ];

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'fast':
        return <Zap className="h-5 w-5 text-green-600" />;
      case 'enhanced':
        return <Database className="h-5 w-5 text-blue-600" />;
      case 'comprehensive':
        return <CheckCircle2 className="h-5 w-5 text-purple-600" />;
      default:
        return <FileText className="h-5 w-5 text-gray-600" />;
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'fast':
        return 'border-green-200 hover:border-green-300 bg-green-50';
      case 'enhanced':
        return 'border-blue-200 hover:border-blue-300 bg-blue-50';
      case 'comprehensive':
        return 'border-purple-200 hover:border-purple-300 bg-purple-50';
      default:
        return 'border-gray-200 hover:border-gray-300 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>⚙️ Validatie Modus Laden...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-orange-200">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50">
        <CardTitle className="flex items-center gap-2 text-orange-800">
          <Database className="h-5 w-5" />
          🎯 Kies Validatie Modus
        </CardTitle>
        <p className="text-sm text-orange-600">
          {backendAvailable 
            ? "DMP Database beschikbaar - kies je gewenste validatie niveau"
            : "Backend niet beschikbaar - beperkte validatie opties"
          }
        </p>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="grid gap-4">
          {availableModes.map((mode) => (
            <div
              key={mode.mode}
              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                selectedMode?.mode === mode.mode
                  ? 'ring-2 ring-orange-500 bg-orange-50'
                  : getModeColor(mode.mode)
              }`}
              onClick={() => onModeSelect(mode)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getModeIcon(mode.mode)}
                  <div>
                    <h3 className="font-medium text-gray-900">{mode.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{mode.description}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Clock className="h-4 w-4" />
                    {mode.estimatedTime}
                  </div>
                  {!mode.requiresTaxonomy && (
                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
                      Geen taxonomy nodig
                    </Badge>
                  )}
                </div>
              </div>
              
              <div className="mt-3 flex flex-wrap gap-2">
                {mode.features.map((feature, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {feature}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        {selectedMode && (
          <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <p className="text-sm text-orange-800">
              <strong>Geselecteerd:</strong> {selectedMode.name}
              {!selectedMode.requiresTaxonomy && (
                <span className="ml-2 text-green-700">
                  ✅ Taxonomy bestand niet vereist
                </span>
              )}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
