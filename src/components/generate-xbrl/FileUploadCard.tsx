
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileUploadZone } from "@/components/FileUploadZone";
import { Upload } from "lucide-react";

interface FileUploadCardProps {
  excelFile: File | null;
  onFileSelect: (file: File | null) => void;
}

export const FileUploadCard = ({ excelFile, onFileSelect }: FileUploadCardProps) => {
  return (
    <Card className="shadow-lg border-blue-200">
      <CardHeader className="bg-blue-50">
        <CardTitle className="flex items-center gap-2 text-blue-900">
          <Upload className="h-5 w-5" />📤 Upload FINREP Excel
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <FileUploadZone
          label="FINREP Excel Bestand"
          description="Upload je .xlsx FINREP rapportage bestand"
          acceptedTypes=".xlsx,.xls"
          file={excelFile}
          onFileSelect={onFileSelect}
          icon={<Upload className="h-8 w-8" />}
        />
      </CardContent>
    </Card>
  );
};
