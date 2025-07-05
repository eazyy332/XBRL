
import { useCallback, useState, useEffect } from "react";
import { Upload, File, X, CheckCircle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { validateTaxonomyZip, TaxonomyValidationResult } from "@/lib/taxonomyValidator";
import { XBRLPreviewModal } from "./XBRLPreviewModal";

interface FileUploadZoneProps {
  label: string;
  description: string;
  acceptedTypes: string;
  file: File | null;
  onFileSelect: (file: File | null) => void;
  icon: React.ReactNode;
}

export const FileUploadZone = ({
  label,
  description,
  acceptedTypes,
  file,
  onFileSelect,
  icon
}: FileUploadZoneProps) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationResult, setValidationResult] = useState<TaxonomyValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Validate taxonomy ZIP files
  useEffect(() => {
    const validateFile = async () => {
      if (!file || !acceptedTypes.includes('.zip')) {
        setValidationResult(null);
        return;
      }

      setIsValidating(true);
      try {
        const result = await validateTaxonomyZip(file);
        setValidationResult(result);
      } catch (error) {
        setValidationResult({
          isValid: false,
          message: "❌ Validation failed",
          missingFiles: [],
          foundFiles: []
        });
      } finally {
        setIsValidating(false);
      }
    };

    validateFile();
  }, [file, acceptedTypes]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const isXBRLInstance = file && (file.name.toLowerCase().endsWith('.xbrl') || file.name.toLowerCase().endsWith('.xml'));

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-orange-800">{label}</label>
      <div className="space-y-3">
        {/* Main drop zone area */}
        <div
          className={cn(
            "relative border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer",
            isDragOver
              ? "border-orange-400 bg-orange-50"
              : file
              ? validationResult?.isValid
                ? "border-green-400 bg-green-50"
                : validationResult?.isValid === false
                ? "border-red-400 bg-red-50"
                : "border-yellow-400 bg-yellow-50"
              : "border-orange-300 hover:border-orange-400 bg-orange-50 hover:bg-orange-100"
          )}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <input
            type="file"
            accept={acceptedTypes}
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="text-center">
            {file ? (
              <div className="space-y-3">
                <div className="flex items-center justify-center">
                  {isValidating ? (
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                  ) : validationResult?.isValid ? (
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  ) : validationResult?.isValid === false ? (
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                  ) : (
                    <CheckCircle className="h-8 w-8 text-gray-500" />
                  )}
                </div>
                
                <div>
                  <p className="font-medium text-gray-700">{file.name}</p>
                  <p className="text-sm text-gray-600">{formatFileSize(file.size)}</p>
                </div>

                {/* Validation Results */}
                {validationResult && !isValidating && (
                  <div className={cn(
                    "p-3 rounded-lg text-sm",
                    validationResult.isValid 
                      ? "bg-green-100 border border-green-300" 
                      : "bg-red-100 border border-red-300"
                  )}>
                    <p className={cn(
                      "font-medium mb-2",
                      validationResult.isValid ? "text-green-800" : "text-red-800"
                    )}>
                      {validationResult.message}
                    </p>
                    
                    {validationResult.foundFiles.length > 0 && (
                      <div className="mb-2">
                        <p className="text-green-700 font-medium">Found:</p>
                        <ul className="text-green-600 text-xs ml-2">
                          {validationResult.foundFiles.map((file, i) => (
                            <li key={i}>• {file}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {validationResult.missingFiles.length > 0 && (
                      <div>
                        <p className="text-red-700 font-medium">Missing:</p>
                        <ul className="text-red-600 text-xs ml-2">
                          {validationResult.missingFiles.map((file, i) => (
                            <li key={i}>• {file}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-center text-orange-400">
                  {isDragOver ? <Upload className="h-8 w-8" /> : icon}
                </div>
                <div>
                  <p className="font-medium text-orange-700">
                    {isDragOver ? "Drop file here" : "Click to upload or drag and drop"}
                  </p>
                  <p className="text-sm text-orange-600">{description}</p>
                  <p className="text-xs text-orange-500 mt-1">
                    Accepted formats: {acceptedTypes}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action buttons - Outside the file input area */}
        {file && (
          <div className="flex items-center justify-center gap-3 px-4">
            {isXBRLInstance && (
              <XBRLPreviewModal file={file} />
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onFileSelect(null);
                setValidationResult(null);
              }}
              className="inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-700"
            >
              <X className="h-4 w-4" />
              Remove
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
