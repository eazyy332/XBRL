
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileUploadZone } from "@/components/FileUploadZone";
import { EnhancedXBRLPreview } from "@/components/EnhancedXBRLPreview";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { FileText, Download, RotateCcw, Loader2, AlertTriangle } from "lucide-react";
import { BackendService } from "@/lib/api";

export const XBRLAnnotationSection = () => {
  const [xbrlFile, setXbrlFile] = useState<File | null>(null);
  const [isAnnotating, setIsAnnotating] = useState(false);
  const [annotationResult, setAnnotationResult] = useState<{
    success: boolean;
    downloadUrl?: string;
    filename?: string;
    error?: string;
  } | null>(null);
  const [fileValidation, setFileValidation] = useState<{
    isValidXBRL: boolean;
    message: string;
  } | null>(null);
  const { toast } = useToast();
  const backendService = BackendService.getInstance();

  const validateXBRLFile = async (file: File) => {
    console.log("🔍 Validating XBRL file format...", file.name);
    
    try {
      const content = await file.text();
      
      // Check if it's XML format
      const isXML = content.trim().startsWith('<?xml') || content.includes('<xbrl') || content.includes('<XBRL');
      
      // Check for XBRL-specific elements
      const hasXBRLElements = content.includes('xbrl') || content.includes('XBRL') || 
                             content.includes('xsi:schemaLocation') || 
                             content.includes('xmlns:');
      
      // Check if it's JSON (common mistake)
      const isJSON = content.trim().startsWith('{') || content.trim().startsWith('[');
      
      if (isJSON) {
        setFileValidation({
          isValidXBRL: false,
          message: "❌ Dit bestand is JSON-formaat. Voor DPM annotaties heeft u een XBRL XML-bestand nodig (.xbrl of .xml)."
        });
        return false;
      }
      
      if (!isXML || !hasXBRLElements) {
        setFileValidation({
          isValidXBRL: false,
          message: "⚠️ Dit bestand lijkt geen geldig XBRL XML-bestand te zijn. DPM annotaties werken alleen met XBRL XML-bestanden."
        });
        return false;
      }
      
      setFileValidation({
        isValidXBRL: true,
        message: "✅ Geldig XBRL XML-bestand gedetecteerd - geschikt voor DPM annotaties."
      });
      return true;
      
    } catch (error) {
      setFileValidation({
        isValidXBRL: false,
        message: "❌ Kan bestandsinhoud niet lezen voor validatie."
      });
      return false;
    }
  };

  const handleFileSelect = async (file: File | null) => {
    setXbrlFile(file);
    setAnnotationResult(null);
    setFileValidation(null);
    
    if (file) {
      await validateXBRLFile(file);
    }
  };

  const handleAnnotation = async () => {
    if (!xbrlFile) {
      toast({
        title: "Geen bestand",
        description: "Upload eerst een XBRL-bestand voor annotatie.",
        variant: "destructive",
      });
      return;
    }

    // Check file validation before proceeding
    if (fileValidation && !fileValidation.isValidXBRL) {
      toast({
        title: "Ongeldig bestandsformaat",
        description: "Upload een geldig XBRL XML-bestand voor DPM annotaties.",
        variant: "destructive",
      });
      return;
    }

    setIsAnnotating(true);
    setAnnotationResult(null);

    try {
      const backendUrl = await backendService.findWorkingBackendUrl();
      if (!backendUrl) {
        throw new Error("Backend niet beschikbaar");
      }

      // Debug logging
      console.log("🔍 Starting XBRL annotation with file:", {
        name: xbrlFile.name,
        size: xbrlFile.size,
        type: xbrlFile.type,
        isValidXBRL: fileValidation?.isValidXBRL
      });

      const formData = new FormData();
      formData.append("instance", xbrlFile);
      
      console.log("📤 Sending FormData to:", `${backendUrl}/annotate`);

      const response = await fetch(`${backendUrl}/annotate`, {
        method: "POST",
        body: formData,
        signal: AbortSignal.timeout(60000),
      });

      console.log("📡 Response status:", response.status, response.statusText);

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          console.log("❌ Backend error details:", errorData);
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (parseError) {
          try {
            const errorText = await response.text();
            console.log("❌ Backend error text:", errorText);
            if (errorText) errorMessage = errorText;
          } catch (textError) {
            console.log("❌ Could not parse error response");
          }
        }
        throw new Error(`Annotatie mislukt: ${errorMessage}`);
      }

      const result = await response.json();
      console.log("✅ Annotation result:", result);
      
      if (result.success) {
        // Validate the annotation result by checking if content actually has DPM comments
        if (result.downloadUrl) {
          try {
            const annotatedResponse = await fetch(result.downloadUrl);
            if (annotatedResponse.ok) {
              const annotatedContent = await annotatedResponse.text();
              const dmpCommentCount = (annotatedContent.match(/<!--\s*Datapoint[^>]*-->/g) || []).length;
              
              console.log("🔍 DPM annotation validation:", {
                hasDownloadUrl: !!result.downloadUrl,
                contentLength: annotatedContent.length,
                dmpCommentCount
              });
              
              if (dmpCommentCount > 0) {
                toast({
                  title: "Annotatie voltooid",
                  description: `✅ ${dmpCommentCount} DPM annotaties toegevoegd aan XBRL-bestand`,
                  variant: "default",
                });
              } else {
                toast({
                  title: "Annotatie uitgevoerd",
                  description: "⚠️ Backend heeft bestand verwerkt, maar geen DPM annotaties gedetecteerd",
                  variant: "default",
                });
              }
            }
          } catch (validationError) {
            console.warn("⚠️ Could not validate annotation result:", validationError);
            toast({
              title: "Annotatie voltooid",
              description: "✅ XBRL-bestand is verwerkt door de backend",
              variant: "default",
            });
          }
        }
        
        setAnnotationResult(result);
      } else {
        throw new Error(result.error || "Onbekende fout");
      }
    } catch (error: any) {
      console.error("❌ Annotatie fout:", error);
      const errorMessage = error.message || "Onbekende fout bij annotatie";
      
      setAnnotationResult({
        success: false,
        error: errorMessage
      });
      
      toast({
        title: "Annotatie mislukt",
        description: `❌ ${errorMessage}`,
        variant: "destructive",
      });
    } finally {
      setIsAnnotating(false);
    }
  };

  const resetAnnotation = () => {
    setXbrlFile(null);
    setAnnotationResult(null);
    setFileValidation(null);
  };

  return (
    <Card className="border-blue-200">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardTitle className="flex items-center gap-2 text-blue-800">
          <FileText className="h-5 w-5" />
          🔍 Annoteren van XBRL-bestand
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        {!annotationResult?.success && (
          <>
            <div className="space-y-4">
              <FileUploadZone
                label="Upload XBRL Instance"
                description="Upload uw .xbrl bestand voor annotatie"
                acceptedTypes=".xbrl,.xml"
                file={xbrlFile}
                onFileSelect={handleFileSelect}
                icon={<FileText className="h-8 w-8" />}
              />

              {/* File Validation Alert */}
              {fileValidation && (
                <Alert className={fileValidation.isValidXBRL ? "border-green-200 bg-green-50" : "border-yellow-200 bg-yellow-50"}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription className={fileValidation.isValidXBRL ? "text-green-800" : "text-yellow-800"}>
                    {fileValidation.message}
                  </AlertDescription>
                </Alert>
              )}

              {/* Preview Button for uploaded file */}
              {xbrlFile && (
                <div className="flex justify-center">
                  <EnhancedXBRLPreview 
                    file={xbrlFile} 
                    annotationResult={annotationResult || undefined}
                  />
                </div>
              )}
            </div>

            <div className="flex justify-center gap-4">
              <Button 
                onClick={handleAnnotation}
                disabled={!xbrlFile || isAnnotating || (fileValidation && !fileValidation.isValidXBRL)}
                className="px-8 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isAnnotating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Annoteren...
                  </>
                ) : (
                  "Voeg annotaties toe"
                )}
              </Button>
            </div>
          </>
        )}

        {/* Success Result */}
        {annotationResult?.success && (
          <div className="space-y-4">
            <Alert className="border-green-200 bg-green-50">
              <AlertDescription className="text-green-800">
                <strong>✅ Annotatie voltooid</strong>
                <br />
                Uw XBRL-bestand is succesvol geannoteerd en klaar voor download.
              </AlertDescription>
            </Alert>

            {/* Enhanced Preview for annotated file */}
            {xbrlFile && (
              <div className="flex justify-center mb-4">
                <EnhancedXBRLPreview 
                  file={xbrlFile} 
                  annotationResult={annotationResult}
                />
              </div>
            )}

            <div className="flex justify-center gap-4">
              {annotationResult.downloadUrl && (
                <Button asChild className="bg-green-600 hover:bg-green-700 text-white">
                  <a 
                    href={annotationResult.downloadUrl} 
                    download={annotationResult.filename || "annotated.xbrl"}
                    className="flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    📎 Download Annotated XBRL
                  </a>
                </Button>
              )}
              
              <Button 
                onClick={resetAnnotation}
                variant="outline"
                className="gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                Bestand opnieuw kiezen
              </Button>
            </div>
          </div>
        )}

        {/* Error Result */}
        {annotationResult && !annotationResult.success && (
          <div className="space-y-4">
            <Alert className="border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">
                <strong>❌ Annotatie mislukt</strong>
                <br />
                {annotationResult.error}
              </AlertDescription>
            </Alert>

            <div className="flex justify-center">
              <Button 
                onClick={resetAnnotation}
                variant="outline"
                className="gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                🔁 Bestand opnieuw kiezen
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
