import React, { useState, KeyboardEvent } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Plus, Trash2 } from "lucide-react";
import { Process, Resource, AllocationMatrix } from '@/utils/deadlockAlgorithm';
import { toast } from 'sonner';

type ResourceTableProps = {
  matrix: AllocationMatrix;
  setMatrix: React.Dispatch<React.SetStateAction<AllocationMatrix>>;
};

const ResourceTable: React.FC<ResourceTableProps> = ({ matrix, setMatrix }) => {
  const [newProcessId, setNewProcessId] = useState<string>('');
  const [newResourceId, setNewResourceId] = useState<string>('');
  const [newResourceInstances, setNewResourceInstances] = useState<number>(1);
  const [newResourceMultiInstance, setNewResourceMultiInstance] = useState<boolean>(true);

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>, action: 'process' | 'resource') => {
    if (e.key === 'Enter') {
      if (action === 'process') {
        addProcess();
      } else {
        addResource();
      }
    }
  };

  const loadSampleExample = () => {
    const sampleData: AllocationMatrix = {
      processes: [
        { id: 'P1', allocation: { 'R1': 1, 'R2': 0 }, request: { 'R1': 0, 'R2': 1 } },
        { id: 'P2', allocation: { 'R1': 0, 'R2': 1 }, request: { 'R1': 1, 'R2': 0 } },
        { id: 'P3', allocation: { 'R1': 0, 'R2': 1 }, request: { 'R1': 0, 'R2': 0 } },
      ],
      resources: [
        { id: 'R1', total: 1, available: 0, isMultiInstance: false },
        { id: 'R2', total: 2, available: 0, isMultiInstance: true }
      ]
    };
    setMatrix(sampleData);
    toast.success("Loaded sample example");
  };

  const handleProcessIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    setNewProcessId(value);
  };

  const handleResourceIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    setNewResourceId(value);
  };

  const addProcess = () => {
    if (!newProcessId.trim()) {
      toast.error("Process ID cannot be empty");
      return;
    }

    if (matrix.processes.some(p => p.id === newProcessId)) {
      toast.error("Process ID already exists");
      return;
    }

    const newProcess: Process = {
      id: newProcessId,
      allocation: {},
      request: {}
    };

    matrix.resources.forEach(resource => {
      newProcess.allocation[resource.id] = 0;
      newProcess.request[resource.id] = 0;
    });

    setMatrix(prev => ({
      ...prev,
      processes: [...prev.processes, newProcess]
    }));
    setNewProcessId('');
    toast.success(`Process ${newProcessId} added`);
  };

  const addResource = () => {
    if (!newResourceId.trim()) {
      toast.error("Resource ID cannot be empty");
      return;
    }

    if (matrix.resources.some(r => r.id === newResourceId)) {
      toast.error("Resource ID already exists");
      return;
    }

    const instances = newResourceMultiInstance ? newResourceInstances : 1;

    const newResource: Resource = {
      id: newResourceId,
      total: instances,
      available: instances,
      isMultiInstance: newResourceMultiInstance
    };

    const updatedProcesses = matrix.processes.map(process => {
      return {
        ...process,
        allocation: { ...process.allocation, [newResourceId]: 0 },
        request: { ...process.request, [newResourceId]: 0 }
      };
    });

    setMatrix(prev => ({
      ...prev,
      resources: [...prev.resources, newResource],
      processes: updatedProcesses
    }));
    
    setNewResourceId('');
    setNewResourceInstances(1);
    toast.success(`Added resource ${newResourceId}`);
  };

  const removeProcess = (processId: string) => {
    setMatrix(prev => ({
      ...prev,
      processes: prev.processes.filter(p => p.id !== processId)
    }));
    toast.success(`Removed process ${processId}`);
  };

  const removeResource = (resourceId: string) => {
    setMatrix(prev => ({
      ...prev,
      resources: prev.resources.filter(r => r.id !== resourceId),
      processes: prev.processes.map(process => {
        const { [resourceId]: allocRemoved, ...restAlloc } = process.allocation;
        const { [resourceId]: reqRemoved, ...restReq } = process.request;
        return {
          ...process,
          allocation: restAlloc,
          request: restReq
        };
      })
    }));
    toast.success(`Removed resource ${resourceId}`);
  };

  const updateAllocation = (processId: string, resourceId: string, value: number) => {
    if (value < 0) value = 0;
    
    const resource = matrix.resources.find(r => r.id === resourceId);
    if (resource) {
      const currentAllocationForResource = matrix.processes.reduce((sum, p) => {
        if (p.id !== processId) sum += (p.allocation[resourceId] || 0);
        return sum;
      }, 0);
      
      const maxAllowable = resource.total - currentAllocationForResource;
      if (value > maxAllowable) value = maxAllowable;
    }
    
    setMatrix(prev => ({
      ...prev,
      processes: prev.processes.map(process => {
        if (process.id === processId) {
          return {
            ...process,
            allocation: {
              ...process.allocation,
              [resourceId]: value
            }
          };
        }
        return process;
      })
    }));
  };

  const updateRequest = (processId: string, resourceId: string, value: number) => {
    if (value < 0) value = 0;
    
    setMatrix(prev => ({
      ...prev,
      processes: prev.processes.map(process => {
        if (process.id === processId) {
          return {
            ...process,
            request: {
              ...process.request,
              [resourceId]: value
            }
          };
        }
        return process;
      })
    }));
  };

  const clearTable = () => {
    setMatrix({ processes: [], resources: [] });
    toast.success("Cleared all data");
  };

  return (
    <Card className="w-full shadow-lg bg-card">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Resource Allocation Table</CardTitle>
            <CardDescription>
              Configure processes, resources, allocation, and requests
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={loadSampleExample}
              className="text-xs"
            >
              Sample Example
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col space-y-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label htmlFor="process-id" className="text-xs">Add Process</Label>
              <div className="flex items-center gap-2 mt-1">
                <Input
                  id="process-id"
                  placeholder="P1"
                  value={newProcessId}
                  onChange={handleProcessIdChange}
                  onKeyPress={(e) => handleKeyPress(e, 'process')}
                  className="w-16 h-8 text-sm"
                />
                <Button onClick={addProcess} size="icon" className="h-8 w-8">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex-1">
              <Label htmlFor="resource-id" className="text-xs">Add Resource</Label>
              <div className="flex items-center gap-2 mt-1">
                <Input
                  id="resource-id"
                  placeholder="R1"
                  value={newResourceId}
                  onChange={handleResourceIdChange}
                  onKeyPress={(e) => handleKeyPress(e, 'resource')}
                  className="w-16 h-8 text-sm"
                />
                {newResourceMultiInstance && (
                  <Input
                    type="number"
                    min="1"
                    placeholder="Qty"
                    value={newResourceInstances}
                    onChange={(e) => setNewResourceInstances(parseInt(e.target.value) || 1)}
                    className="w-16 h-8 text-sm"
                  />
                )}
                <div className="flex items-center gap-2">
                  <Switch
                    id="multi-instance"
                    checked={newResourceMultiInstance}
                    onCheckedChange={setNewResourceMultiInstance}
                  />
                  <Label htmlFor="multi-instance" className="text-xs whitespace-nowrap">Multi</Label>
                </div>
                <Button onClick={addResource} size="icon" className="h-8 w-8">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            {matrix.resources.length > 0 && matrix.processes.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px] text-green-600 font-bold">Process</TableHead>
                    {matrix.resources.map((resource) => (
                      <React.Fragment key={resource.id}>
                        <TableHead className="text-center">
                          <span className="text-green-600 font-bold">{resource.id}</span> <br />
                          <span className="text-xs">
                            (Total: {resource.total}, {resource.isMultiInstance ? 'Multi' : 'Single'})
                          </span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => removeResource(resource.id)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </TableHead>
                      </React.Fragment>
                    ))}
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {matrix.processes.map((process) => (
                    <TableRow key={process.id}>
                      <TableCell className="font-medium text-green-600">{process.id}</TableCell>
                      
                      {matrix.resources.map((resource) => (
                        <TableCell key={`${process.id}-${resource.id}`} className="p-1">
                          <div className="grid grid-cols-2 gap-1">
                            <div className="flex flex-col">
                              <Label className="text-xs text-center">Alloc</Label>
                              <Input
                                type="number"
                                min="0"
                                value={process.allocation[resource.id] || 0}
                                onChange={(e) => 
                                  updateAllocation(
                                    process.id,
                                    resource.id,
                                    parseInt(e.target.value) || 0
                                  )
                                }
                                className="h-8 text-center"
                              />
                            </div>
                            
                            <div className="flex flex-col">
                              <Label className="text-xs text-center">Req</Label>
                              <Input
                                type="number"
                                min="0"
                                value={process.request[resource.id] || 0}
                                onChange={(e) => 
                                  updateRequest(
                                    process.id,
                                    resource.id,
                                    parseInt(e.target.value) || 0
                                  )
                                }
                                className="h-8 text-center"
                              />
                            </div>
                          </div>
                        </TableCell>
                      ))}
                      
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeProcess(process.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Add processes and resources to create the allocation matrix
              </div>
            )}
          </div>
          
          {matrix.processes.length > 0 && (
            <div className="flex justify-end">
              <Button 
                variant="outline" 
                size="sm"
                onClick={clearTable}
                className="text-xs"
              >
                Clear Table
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ResourceTable;
