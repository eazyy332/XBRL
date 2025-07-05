
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Eye, Search, Download, Info } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BackendService } from "@/lib/api";

interface EnhancedXBRLPreviewProps {
  file: File;
  annotationResult?: {
    success: boolean;
    downloadUrl?: string;
    filename?: string;
  };
}

export const EnhancedXBRLPreview = ({ file, annotationResult }: EnhancedXBRLPreviewProps) => {
  const [rawContent, setRawContent] = useState<string>("");
  const [annotatedContent, setAnnotatedContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [activeTab, setActiveTab] = useState<string>("raw");
  const [contentComparison, setContentComparison] = useState<{
    hasAnnotations: boolean;
    annotationCount: number;
    isIdentical: boolean;
  } | null>(null);
  const backendService = BackendService.getInstance();

  const loadFileContent = async () => {
    console.log("📄 Loading XBRL file content...", file.name);
    
    if (!rawContent && !isLoading) {
      setIsLoading(true);
      setError("");
      
      try {
        // Load original file content
        const originalText = await file.text();
        setRawContent(originalText);
        
        // Check if this is actually an XBRL file
        const isXBRLFile = originalText.includes('<?xml') && 
                          (originalText.includes('xbrl') || originalText.includes('XBRL'));
        
        if (!isXBRLFile) {
          console.warn("⚠️ File doesn't appear to be XBRL XML format");
        }
        
        // If we have annotation results, try to fetch annotated content
        if (annotationResult?.success && annotationResult.downloadUrl) {
          console.log("📥 Fetching annotated XBRL content...");
          try {
            const annotatedResponse = await fetch(annotationResult.downloadUrl);
            if (annotatedResponse.ok) {
              const annotatedText = await annotatedResponse.text();
              setAnnotatedContent(annotatedText);
              
              // Compare content to detect actual annotations
              const comparison = compareContent(originalText, annotatedText);
              setContentComparison(comparison);
              
              if (comparison.hasAnnotations) {
                setActiveTab("annotated"); // Switch to annotated view by default
                console.log("✅ Annotated content loaded with", comparison.annotationCount, "DPM comments");
              } else {
                console.warn("⚠️ No DPM annotations found in the response");
              }
            } else {
              console.warn("⚠️ Could not fetch annotated content, using original");
              setAnnotatedContent(originalText);
              setContentComparison({ hasAnnotations: false, annotationCount: 0, isIdentical: true });
            }
          } catch (annotatedError) {
            console.warn("⚠️ Error fetching annotated content:", annotatedError);
            setAnnotatedContent(originalText);
            setContentComparison({ hasAnnotations: false, annotationCount: 0, isIdentical: true });
          }
        } else {
          setAnnotatedContent(originalText);
          setContentComparison({ hasAnnotations: false, annotationCount: 0, isIdentical: true });
        }
        
      } catch (error: any) {
        console.error("❌ Error reading file:", error);
        setError(error.message || "Could not read file content");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const compareContent = (original: string, annotated: string) => {
    // Check if content is identical
    const isIdentical = original === annotated;
    
    // Count DPM annotation comments
    const dmpCommentRegex = /<!--\s*Datapoint[^>]*-->/g;
    const annotationMatches = annotated.match(dmpCommentRegex) || [];
    const annotationCount = annotationMatches.length;
    
    // Check if there are any DPM annotations
    const hasAnnotations = annotationCount > 0;
    
    return {
      hasAnnotations,
      annotationCount,
      isIdentical
    };
  };

  const handleOpenChange = (open: boolean) => {
    if (open) {
      loadFileContent();
    }
  };

  const highlightAnnotations = (content: string) => {
    // Highlight DPM annotation comments with special styling
    return content.replace(
      /(<!--\s*Datapoint[^>]*-->)/g,
      '<span style="background-color: #f3f4f6; color: #6b7280; font-style: italic; padding: 2px 4px; border-left: 3px solid #3b82f6; margin: 2px 0; display: inline-block; border-radius: 3px;">$1</span>'
    );
  };

  const highlightSearchTerm = (content: string, term: string) => {
    if (!term.trim()) return content;
    
    const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return content.replace(regex, '<mark style="background-color: #fef08a; color: #92400e; font-weight: bold; padding: 1px 2px; border-radius: 2px;">$1</mark>');
  };

  const processContent = (content: string) => {
    let processed = highlightAnnotations(content);
    if (searchTerm) {
      processed = highlightSearchTerm(processed, searchTerm);
    }
    return processed;
  };

  const formatXML = (content: string) => {
    try {
      // Simple XML formatting with proper indentation
      return content
        .replace(/></g, '>\n<')
        .replace(/\n\s*\n/g, '\n')
        .trim();
    } catch (error) {
      return content;
    }
  };

  const getCurrentContent = () => {
    const content = activeTab === "annotated" ? annotatedContent : rawContent;
    return formatXML(content);
  };

  const searchMatches = searchTerm ? 
    (getCurrentContent().match(new RegExp(searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')) || []).length : 0;

  return (
    <Dialog onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="text-blue-600 border-blue-300 hover:bg-blue-50"
        >
          <Eye className="h-4 w-4 mr-2" />
          {annotationResult?.success ? "Preview Annotated XBRL" : "Preview XBRL"}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-7xl max-h-[95vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>XBRL Preview: {file.name}</span>
            {annotationResult?.success && annotationResult.downloadUrl && (
              <Button asChild size="sm" className="bg-green-600 hover:bg-green-700 text-white">
                <a 
                  href={annotationResult.downloadUrl} 
                  download={annotationResult.filename || "annotated.xbrl"}
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download
                </a>
              </Button>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Content Status Alert */}
          {contentComparison && annotationResult?.success && (
            <Alert className={contentComparison.hasAnnotations ? "border-green-200 bg-green-50" : "border-yellow-200 bg-yellow-50"}>
              <Info className="h-4 w-4" />
              <AlertDescription>
                {contentComparison.hasAnnotations ? (
                  <span className="text-green-800">
                    ✅ <strong>{contentComparison.annotationCount} DPM annotations</strong> added successfully
                  </span>
                ) : contentComparison.isIdentical ? (
                  <span className="text-yellow-800">
                    ⚠️ <strong>No annotations added</strong> - This might be because the file is not in XBRL XML format or the backend couldn't process it for DPM annotations
                  </span>
                ) : (
                  <span className="text-yellow-800">
                    ℹ️ Content modified but no DPM annotations detected
                  </span>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Search Bar */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search in XBRL content (tables, rows, concepts, values)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            {searchTerm && (
              <span className="text-sm text-gray-600 min-w-fit">
                {searchMatches} match{searchMatches !== 1 ? 'es' : ''}
              </span>
            )}
          </div>

          {/* Content Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-[70vh]">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="raw">Raw XBRL</TabsTrigger>
              <TabsTrigger value="annotated" className="relative">
                Annotated XBRL
                {contentComparison?.hasAnnotations && (
                  <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                    {contentComparison.annotationCount} DPM Comments
                  </span>
                )}
                {contentComparison?.isIdentical && annotationResult?.success && (
                  <span className="ml-2 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                    No Changes
                  </span>
                )}
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="raw" className="h-full mt-4">
              <ScrollArea className="h-full w-full border rounded-md p-4 bg-gray-50">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <span className="ml-3 text-gray-600">Loading XBRL content...</span>
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center justify-center h-32 text-red-600">
                    <p className="font-medium">Error loading XBRL file:</p>
                    <p className="text-sm mt-1">{error}</p>
                  </div>
                ) : rawContent ? (
                  <pre 
                    className="text-xs font-mono whitespace-pre-wrap break-words text-gray-800 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: processContent(rawContent) 
                    }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-32 text-gray-500">
                    Opening XBRL preview...
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="annotated" className="h-full mt-4">
              <ScrollArea className="h-full w-full border rounded-md p-4 bg-gray-50">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <span className="ml-3 text-gray-600">Loading annotated XBRL content...</span>
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center justify-center h-32 text-red-600">
                    <p className="font-medium">Error loading XBRL file:</p>
                    <p className="text-sm mt-1">{error}</p>
                  </div>
                ) : annotatedContent ? (
                  <pre 
                    className="text-xs font-mono whitespace-pre-wrap break-words text-gray-800 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: processContent(annotatedContent) 
                    }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-32 text-gray-500">
                    Loading annotated XBRL preview...
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
};
