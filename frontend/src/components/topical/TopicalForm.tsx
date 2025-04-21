import { useState, useRef } from 'react';
import { useProcessTopical } from '@/lib/hooks/queries/use-topical';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Upload, Download } from 'lucide-react';
import { TopicalResponse } from '@/lib/api/types';
import { topicalService } from '@/lib/api/services/topical.service';
import { useToast } from '@/components/ui/use-toast';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function TopicalForm() {
  const [file, setFile] = useState<File | null>(null);
  const [minSearchVolume, setMinSearchVolume] = useState<number>(100);
  const [processedData, setProcessedData] = useState<TopicalResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const { mutate, isPending: isLoading, isError, error } = useProcessTopical();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleProcessTopical = () => {
    if (!file) {
      toast({
        title: "Error",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    if (minSearchVolume < 1) {
      toast({
        title: "Error", 
        description: "Minimum search volume must be greater than 0",
        variant: "destructive",
      });
      return;
    }

    mutate(
      { file, min_search_volume: minSearchVolume },
      {
        onSuccess: (data) => {
          setProcessedData(data);
          toast({
            title: "Success",
            description: "Topical analysis completed successfully",
          });
        },
        onError: (error) => {
          toast({
            title: "Error",
            description: error.message || "Failed to process topical analysis",
            variant: "destructive",
          });
        },
      }
    );
  };

  const handleDownload = () => {
    if (processedData?.data?.file) {
      const downloadUrl = topicalService.downloadTopicalFile(processedData.data.file.file_id);
      window.open(downloadUrl, '_blank');
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Topical Analysis</CardTitle>
        <CardDescription>
          Analyze and identify topical trends from your data
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="file-upload">Upload Excel File</Label>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="w-full"
            >
              <Upload className="mr-2 h-4 w-4" />
              {file ? file.name : "Select File"}
            </Button>
            <input
              id="file-upload"
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="min-search-volume">Minimum Search Volume</Label>
          <Input
            id="min-search-volume"
            type="number"
            min="1"
            value={minSearchVolume}
            onChange={(e) => setMinSearchVolume(Number(e.target.value))}
          />
        </div>

        <Button 
          className="w-full" 
          onClick={handleProcessTopical}
          disabled={isLoading || !file}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            "Process Topical Analysis"
          )}
        </Button>

        {isError && (
          <div className="text-red-500 text-sm">
            {error?.message || "An error occurred during processing"}
          </div>
        )}

        {processedData && (
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold">Analysis Results</h3>
            
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell>B0 ASIN Count</TableCell>
                  <TableCell>{processedData.data.b0_asin_count}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Non-B0 ASIN Count</TableCell>
                  <TableCell>{processedData.data.non_b0_asin_count}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>{processedData.data.status}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
            
            {processedData.data.file && (
              <Button 
                variant="outline" 
                className="w-full"
                onClick={handleDownload}
              >
                <Download className="mr-2 h-4 w-4" />
                Download Results
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
} 