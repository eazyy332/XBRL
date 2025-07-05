
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface GenerateButtonProps {
  onGenerate: () => void;
  disabled: boolean;
  isGenerating: boolean;
}

export const GenerateButton = ({ onGenerate, disabled, isGenerating }: GenerateButtonProps) => {
  return (
    <Card className="shadow-lg border-blue-200">
      <CardContent className="p-6">
        <div className="text-center space-y-4">
          <Button
            onClick={onGenerate}
            disabled={disabled}
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" /> XBRL wordt gegenereerd...
              </>
            ) : (
              <>⚙️ Genereer XBRL</>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
