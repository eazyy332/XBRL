
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { BackendService } from "@/lib/api";

export const useXBRLGeneration = () => {
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedXBRL, setGeneratedXBRL] = useState<{
    downloadUrl: string;
    filename: string;
  } | null>(null);
  const { toast } = useToast();
  const backendService = BackendService.getInstance();

  const handleGenerate = async () => {
    if (!excelFile) {
      toast({
        title: "Geen bestand geselecteerd",
        description: "Upload eerst een FINREP Excel bestand",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);

    try {
      await generateWithBackend();
    } catch (error) {
      console.log("Backend generation failed:", error);

      if (error instanceof Error) {
        toast({
          title: "Backend Fout",
          description: `Backend fout: ${error.message}`,
          variant: "destructive",
        });
      }

      await generateWithMockService();
    } finally {
      setIsGenerating(false);
    }
  };

  const generateWithBackend = async () => {
    try {
      const result = await backendService.generateXBRL(excelFile!);

      if (result.success && result.downloadUrl) {
        setGeneratedXBRL({
          downloadUrl: result.downloadUrl,
          filename: result.filename || "generated.xbrl",
        });

        toast({
          title: "XBRL Succesvol Gegenereerd",
          description: "Je XBRL bestand is klaar voor download via Python backend",
        });
      } else {
        throw new Error(result.error || "Onbekende fout bij generatie");
      }
    } catch (error) {
      throw error;
    }
  };

  const generateWithMockService = async () => {
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const mockXBRLContent = `<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance">
  <context id="duration_2023">
    <entity><identifier scheme="http://www.example.com">DEMO123</identifier></entity>
    <period><startDate>2023-01-01</startDate><endDate>2023-12-31</endDate></period>
  </context>
  <unit id="EUR"><measure>iso4217:EUR</measure></unit>
  <Assets contextRef="duration_2023" unitRef="EUR">1000000</Assets>
</xbrl>`;

    const blob = new Blob([mockXBRLContent], { type: "application/xml" });
    const downloadUrl = URL.createObjectURL(blob);

    setGeneratedXBRL({
      downloadUrl: downloadUrl,
      filename: `${excelFile!.name.replace(/\.[^/.]+$/, "")}_generated.xbrl`,
    });

    toast({
      title: "XBRL Demo Gegenereerd",
      description: "Demo XBRL bestand gegenereerd (backend niet beschikbaar)",
    });
  };

  const handleDownload = () => {
    if (generatedXBRL) {
      const link = document.createElement("a");
      link.href = generatedXBRL.downloadUrl;
      link.download = generatedXBRL.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return {
    excelFile,
    setExcelFile,
    isGenerating,
    generatedXBRL,
    handleGenerate,
    handleDownload,
  };
};
