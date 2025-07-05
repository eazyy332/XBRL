
import { useNavigate } from "react-router-dom";
import { XBRLGenerationHeader } from "@/components/generate-xbrl/XBRLGenerationHeader";
import { BackendStatusCard } from "@/components/generate-xbrl/BackendStatusCard";
import { FileUploadCard } from "@/components/generate-xbrl/FileUploadCard";
import { GenerateButton } from "@/components/generate-xbrl/GenerateButton";
import { SuccessCard } from "@/components/generate-xbrl/SuccessCard";
import { useXBRLGeneration } from "@/hooks/useXBRLGeneration";

export default function GenerateXBRL() {
  const navigate = useNavigate();
  const {
    excelFile,
    setExcelFile,
    isGenerating,
    generatedXBRL,
    handleGenerate,
    handleDownload,
  } = useXBRLGeneration();

  const handleValidateGenerated = () => {
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        <XBRLGenerationHeader />
        <BackendStatusCard />

        <div className="grid gap-6">
          <FileUploadCard 
            excelFile={excelFile} 
            onFileSelect={setExcelFile} 
          />

          <GenerateButton
            onGenerate={handleGenerate}
            disabled={!excelFile || isGenerating}
            isGenerating={isGenerating}
          />

          {generatedXBRL && (
            <SuccessCard
              onDownload={handleDownload}
              onValidate={handleValidateGenerated}
            />
          )}
        </div>
      </div>
    </div>
  );
}
