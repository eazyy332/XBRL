import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Eye } from "lucide-react";

interface XBRLPreviewModalProps {
  file: File;
}

export const XBRLPreviewModal = ({ file }: XBRLPreviewModalProps) => {
  const [content, setContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const loadFileContent = async () => {
    console.log("📄 Loading XBRL file content...", file.name, file.type, file.size);
    
    if (!content && !isLoading) {
      setIsLoading(true);
      setError("");
      
      try {
        // Validate file object
        if (!file || !(file instanceof File)) {
          throw new Error("Invalid file object");
        }

        // Check file type
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.xbrl') && !fileName.endsWith('.xml')) {
          throw new Error("File is not an XBRL/XML file");
        }

        console.log("📖 Reading file content...");
        const text = await file.text();
        console.log("✅ File content loaded successfully, length:", text.length);
        
        if (!text || text.trim().length === 0) {
          throw new Error("File appears to be empty");
        }

        setContent(text);
      } catch (error: any) {
        console.error("❌ Error reading file:", error);
        const errorMessage = error.message || "Could not read file content";
        setError(errorMessage);
        setContent("");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleOpenChange = (open: boolean) => {
    console.log("🔄 Modal open state changed:", open);
    if (open) {
      loadFileContent();
    }
  };

  const formatXML = (xml: string) => {
    try {
      // Simple XML formatting with proper indentation
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xml, "application/xml");
      
      // Check for parsing errors
      const parseError = xmlDoc.querySelector('parsererror');
      if (parseError) {
        console.warn("⚠️ XML parsing warning, using fallback formatting");
        return xml.replace(/></g, '>\n<').replace(/\n\s*\n/g, '\n').trim();
      }

      const serializer = new XMLSerializer();
      const formatted = serializer.serializeToString(xmlDoc);
      
      // Add line breaks and indentation for better readability
      return formatted
        .replace(/></g, '>\n<')
        .replace(/(<[^>]+>)([^<]*)/g, (match, tag, content) => {
          if (content.trim()) {
            return tag + content;
          }
          return tag;
        })
        .split('\n')
        .map((line, index) => {
          const depth = (line.match(/</g) || []).length - (line.match(/\//g) || []).length;
          const indent = '  '.repeat(Math.max(0, depth));
          return indent + line.trim();
        })
        .join('\n');
    } catch (error) {
      console.warn("⚠️ XML formatting failed, using fallback:", error);
      // Fallback to simple formatting if XML parsing fails
      return xml
        .replace(/></g, '>\n<')
        .replace(/\n\s*\n/g, '\n')
        .trim();
    }
  };

  return (
    <Dialog onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="text-blue-600 border-blue-300 hover:bg-blue-50"
        >
          <Eye className="h-4 w-4 mr-2" />
          Preview
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            XBRL Instance Preview: {file.name}
          </DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-[70vh] w-full border rounded-md p-4 bg-gray-50">
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
          ) : content ? (
            <pre className="text-xs font-mono whitespace-pre-wrap break-words text-gray-800 leading-relaxed">
              {formatXML(content)}
            </pre>
          ) : (
            <div className="flex items-center justify-center h-32 text-gray-500">
              Opening XBRL preview...
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
