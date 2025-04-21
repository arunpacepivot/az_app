import { useState, useRef } from 'react';
import { useProcessCerebro } from '@/lib/hooks/queries/use-cerebro';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Upload, Download } from 'lucide-react';
import { CerebroResponse } from '@/lib/api/types';
import { cerebroService } from '@/lib/api/services/cerebro.service';
import { useToast } from '@/components/ui/use-toast';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Card,
  CardContent,
  CardDescription,
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

export function CerebroForm() {
  const [file, setFile] = useState<File | null>(null);
  const [minSearchVolume, setMinSearchVolume] = useState<number>(100);
  const [processedData, setProcessedData] = useState<CerebroResponse | null>(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const { mutate, isPending: isLoading, isError, error } = useProcessCerebro();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleProcessCerebro = () => {
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

    // Initialize progress bar
    setProgress(0);
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 20) return prev + 0.2 // Slow down initial progress
        if (prev < 40) return prev + 0.1
        if (prev < 60) return prev + 0.05
        if (prev < 80) return prev + 0.02
        if (prev < 90) return prev + 0.01
        return prev < 95 ? prev + 0.005 : prev // Cap at 95% until we get a response
      });
    }, 1000);

    mutate(
      { file, min_search_volume: minSearchVolume },
      {
        onSuccess: (data) => {
          clearInterval(progressInterval);
          setProgress(100);
          setProcessedData(data);
          toast({
            title: "Success",
            description: "Cerebro analysis completed successfully",
          });
        },
        onError: (error) => {
          clearInterval(progressInterval);
          setProgress(0);
          
          // Check if the error is a timeout or network error
          if (error?.message?.includes('timeout') || error?.message?.includes('network error')) {
            toast({
              title: "Processing",
              description: "The file is still being processed on the server. Please wait or refresh the page in a few minutes.",
              variant: "default",
            });
          } else {
            toast({
              title: "Error",
              description: error.message || "Failed to process cerebro analysis",
              variant: "destructive",
            });
          }
        },
      }
    );
  };

  const handleDownload = () => {
    if (processedData?.data?.file) {
      const downloadUrl = cerebroService.downloadCerebroFile(processedData.data.file.file_id);
      window.open(downloadUrl, '_blank');
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Cerebro Analysis</CardTitle>
        <CardDescription>
          Advanced keyword research and analysis for your products
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
          onClick={handleProcessCerebro}
          disabled={isLoading || !file}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            "Process Cerebro Analysis"
          )}
        </Button>

        {isLoading && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm text-gray-500">
              <span>Processing your file...</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} />
            <p className="text-xs text-gray-500 mt-2">
              This may take several minutes for large files. Please keep this page open.
            </p>
          </div>
        )}

        {isError && !isLoading && progress === 0 && (
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
                  <TableCell>Keyword Count</TableCell>
                  <TableCell>{processedData.data.keyword_count}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Average Search Volume</TableCell>
                  <TableCell>{processedData.data.search_volume_avg}</TableCell>
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