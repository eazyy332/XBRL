
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Check, Download } from "lucide-react";

interface SuccessCardProps {
  onDownload: () => void;
  onValidate: () => void;
}

export const SuccessCard = ({ onDownload, onValidate }: SuccessCardProps) => {
  return (
    <Card className="shadow-lg border-green-200 bg-green-50">
      <CardContent className="p-6">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2 text-green-700 mb-4">
            <Check className="h-6 w-6" />
            <span className="text-lg font-semibold">XBRL successfully generated</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button
              onClick={onDownload}
              variant="outline"
              className="border-green-600 text-green-700 hover:bg-green-100"
            >
              <Download className="h-4 w-4 mr-2" /> Download XBRL
            </Button>

            <Button
              onClick={onValidate}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              🧾 Valideer direct deze XBRL
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
