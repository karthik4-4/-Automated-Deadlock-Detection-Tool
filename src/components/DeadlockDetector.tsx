
import React, { useState } from 'react';
import ResourceTable from './ResourceTable';
import AllocationGraph from './AllocationGraph';
import DetectionPanel from './DetectionPanel';
import { AllocationMatrix, DetectionResult } from '@/utils/deadlockAlgorithm';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { HelpCircle } from 'lucide-react';
import { ModeToggle } from '@/components/mode-toggle';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const DeadlockDetector: React.FC = () => {
  const [matrix, setMatrix] = useState<AllocationMatrix>({
    processes: [],
    resources: []
  });

  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [activeTab, setActiveTab] = useState<"graph" | "detection">("graph");
  const [showGraph, setShowGraph] = useState(false);
  const [showDetection, setShowDetection] = useState(false);
  
  const deadlockedProcesses = detectionResult?.deadlocked || [];

  const handleTabChange = (value: string) => {
    setActiveTab(value as "graph" | "detection");
    // Don't automatically show content when tab is selected
  };

  return (
    <div className="space-y-6 w-full max-w-[1200px] mx-auto px-4">
      <div className="flex justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Deadlock Detective</h1>
          <p className="text-muted-foreground">
            Visualize and detect deadlocks in operating systems
          </p>
        </div>

        <div className="flex items-center gap-3">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm">
                <HelpCircle className="mr-2 h-4 w-4" />
                How to Use
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Using the Deadlock Detective</AlertDialogTitle>
                <AlertDialogDescription>
                  <div className="space-y-4 text-left">
                    <p><strong>What is a deadlock?</strong> A deadlock occurs when processes are waiting for resources held by other processes, creating a circular wait condition.</p>
                    
                    <div className="space-y-1">
                      <p><strong>Steps to use this tool:</strong></p>
                      <ol className="list-decimal list-inside ml-2 space-y-1">
                        <li>Add processes and resources in the Resource Allocation Table</li>
                        <li>Set allocation values (resources already assigned to processes)</li>
                        <li>Set request values (resources processes are waiting for)</li>
                        <li>Click "Detect Deadlock" to run the analysis</li>
                        <li>View the results and explore the allocation graph</li>
                      </ol>
                    </div>
                    
                    <p><strong>Single vs. Multi-Instance Resources:</strong> Single-instance resources can only be used by one process at a time. Multi-instance resources can be shared among multiple processes.</p>
                    
                    <p>You can use the example buttons to load pre-configured scenarios.</p>
                  </div>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogAction>Close</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <ModeToggle />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ResourceTable matrix={matrix} setMatrix={setMatrix} />
        
        <Tabs
          value={activeTab}
          onValueChange={handleTabChange}
          defaultValue="graph"
          className="w-full"
        >
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="graph">Allocation Graph</TabsTrigger>
            <TabsTrigger value="detection">Detection Results</TabsTrigger>
          </TabsList>
          <TabsContent value="graph" className="mt-4">
            {activeTab === "graph" && (
              <div>
                {!showGraph ? (
                  <div className="flex justify-center my-8">
                    <Button onClick={() => setShowGraph(true)}>Show Allocation Graph</Button>
                  </div>
                ) : (
                  <AllocationGraph matrix={matrix} deadlockedProcesses={deadlockedProcesses} />
                )}
              </div>
            )}
          </TabsContent>
          <TabsContent value="detection" className="mt-4">
            {activeTab === "detection" && (
              <div>
                {!showDetection ? (
                  <div className="flex justify-center my-8">
                    <Button onClick={() => setShowDetection(true)}>Show Detection Panel</Button>
                  </div>
                ) : (
                  <DetectionPanel matrix={matrix} onDetect={setDetectionResult} />
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default DeadlockDetector;
