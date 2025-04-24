
import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from '@/components/ui/scroll-area';
import { AllocationMatrix, DetectionResult, detectDeadlock } from '@/utils/deadlockAlgorithm';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

type DetectionPanelProps = {
  matrix: AllocationMatrix;
  onDetect: (result: DetectionResult) => void;
};

const DetectionPanel: React.FC<DetectionPanelProps> = ({ matrix, onDetect }) => {
  const [result, setResult] = React.useState<DetectionResult | null>(null);
  const [hasRun, setHasRun] = React.useState<boolean>(false);
  
  const runDetection = () => {
    if (matrix.processes.length === 0 || matrix.resources.length === 0) {
      return;
    }

    const detectionResult = detectDeadlock(matrix);
    setResult(detectionResult);
    onDetect(detectionResult);
    setHasRun(true);
  };

  const hasDeadlock = result?.deadlocked.length ? true : false;

  const renderAllocationTable = () => {
    if (matrix.processes.length === 0 || matrix.resources.length === 0 || !hasRun) {
      return null;
    }

    return (
      <div className="border rounded-md overflow-hidden mt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-1/6 border-r text-green-500 font-medium">Process</TableHead>
              <TableHead className="w-2/5 text-center border-r text-green-500 font-medium" colSpan={matrix.resources.length}>
                Allocation
              </TableHead>
              <TableHead className="w-2/5 text-center text-green-500 font-medium" colSpan={matrix.resources.length}>
                Request
              </TableHead>
            </TableRow>
            <TableRow>
              <TableHead className="border-r"></TableHead>
              <TableHead className="text-center border-r text-green-500 font-medium" colSpan={matrix.resources.length}>
                Resource
              </TableHead>
              <TableHead className="text-center text-green-500 font-medium" colSpan={matrix.resources.length}>
                Resource
              </TableHead>
            </TableRow>
            <TableRow>
              <TableHead className="border-r"></TableHead>
              {matrix.resources.map((resource) => (
                <TableHead key={`alloc-${resource.id}`} className="text-center text-green-500 font-medium">
                  {resource.id}
                </TableHead>
              ))}
              {matrix.resources.map((resource) => (
                <TableHead key={`req-${resource.id}`} className="text-center text-green-500 font-medium">
                  {resource.id}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {matrix.processes.map((process) => (
              <TableRow key={process.id}>
                <TableCell className="border-r text-green-500 font-medium">{process.id}</TableCell>
                {matrix.resources.map((resource) => (
                  <TableCell key={`alloc-${process.id}-${resource.id}`} className="text-center">
                    {process.allocation[resource.id] || 0}
                  </TableCell>
                ))}
                {matrix.resources.map((resource) => (
                  <TableCell key={`req-${process.id}-${resource.id}`} className="text-center">
                    {process.request[resource.id] || 0}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };

  return (
    <Card className="w-full shadow-lg">
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span>Deadlock Detection</span>
          <Button onClick={runDetection}>Detect Deadlock</Button>
        </CardTitle>
        <CardDescription>
          Run deadlock detection algorithm to identify potential deadlocks
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!result || !hasRun ? (
          <div className="text-center py-6 text-muted-foreground">
            <p>Configure the resource allocation table and run the detection algorithm</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col items-center p-4 rounded-lg border bg-muted/50">
              {hasDeadlock ? (
                <>
                  <AlertCircle className="text-red-500 h-12 w-12 mb-2" />
                  <h3 className="text-lg font-semibold mb-1">Deadlock Detected!</h3>
                  <p className="text-sm text-center">
                    The following processes are in a deadlock state:
                    <span className="font-semibold block mt-1">
                      {result.deadlocked.join(", ")}
                    </span>
                  </p>
                </>
              ) : (
                <>
                  <CheckCircle className="text-green-600 h-12 w-12 mb-2" />
                  <h3 className="text-lg font-semibold mb-1">No Deadlock Detected</h3>
                  <p className="text-sm text-center">
                    System is in a safe state
                  </p>
                </>
              )}
            </div>
            
            {renderAllocationTable()}
            
            <ScrollArea className="h-[400px] rounded-md border p-4">
              <div className="space-y-6">
                <p className="font-mono text-green-600">
                  Available = {result.steps[0]?.availableResources && 
                    Object.entries(result.steps[0].availableResources).map(([id, val]) => `${id}=${val}`).join(" ")}
                </p>
                
                <Table className="border-collapse border">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="border">Process</TableHead>
                      <TableHead className="border">Request</TableHead>
                      <TableHead className="border">Explanation</TableHead>
                      <TableHead className="border">New Available</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.steps.filter(step => step.processedThisRound.length > 0).map((step, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="border font-mono">
                          {step.processedThisRound.join(", ")}
                        </TableCell>
                        <TableCell className="border font-mono">
                          {step.processedThisRound.map(processId => {
                            const process = matrix.processes.find(p => p.id === processId);
                            return process ? Object.values(process.request).join(" ") : "";
                          }).join(", ")}
                        </TableCell>
                        <TableCell className="border text-sm text-left">
                          {step.description}
                        </TableCell>
                        <TableCell className="border font-mono">
                          {Object.entries(step.availableResources).map(([id, val]) => val).join(" ")}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                
                {hasDeadlock && (
                  <div className="mt-4 p-3 border rounded bg-red-50 dark:bg-red-900/20">
                    <p className="text-red-600 dark:text-red-400">
                      <strong>Deadlock Explanation:</strong> The system is in deadlock because processes 
                      {result.deadlocked.join(", ")} are waiting for resources that will never be released.
                      Each process is holding resources needed by others in a circular wait condition.
                    </p>
                  </div>
                )}
                
                {!hasDeadlock && result.safeSequence && (
                  <div className="mt-4 p-3 border rounded bg-green-50 dark:bg-green-900/20">
                    <p className="text-green-600 dark:text-green-400">
                      <strong>Safe Sequence:</strong> {result.safeSequence.join(" → ")}
                    </p>
                    <p className="text-green-600 dark:text-green-400 mt-2">
                      <strong>Explanation:</strong> The system is in a safe state because all processes can 
                      complete their execution without deadlock by following the safe sequence.
                    </p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DetectionPanel;
