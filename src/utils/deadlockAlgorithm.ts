
export type Process = {
  id: string;
  allocation: { [resourceId: string]: number };
  request: { [resourceId: string]: number };
};

export type Resource = {
  id: string;
  total: number;
  available: number;
  isMultiInstance: boolean;
};

export type AllocationMatrix = {
  processes: Process[];
  resources: Resource[];
};

// Calculate available resources based on total and allocations
export const calculateAvailableResources = (matrix: AllocationMatrix): Resource[] => {
  const resources = [...matrix.resources];
  
  // Reset available to total
  resources.forEach(resource => {
    resource.available = resource.total;
  });
  
  // Subtract allocated resources
  matrix.processes.forEach(process => {
    Object.entries(process.allocation).forEach(([resourceId, allocated]) => {
      const resource = resources.find(r => r.id === resourceId);
      if (resource) {
        resource.available -= allocated;
      }
    });
  });
  
  return resources;
};

export type DetectionResult = {
  deadlocked: string[]; // Process IDs that are deadlocked
  safeSequence: string[] | null; // Safe execution sequence if no deadlock
  steps: DetectionStep[]; // Steps of algorithm execution
};

export type DetectionStep = {
  description: string;
  remainingProcesses: string[];
  availableResources: { [resourceId: string]: number };
  processedThisRound: string[];
};

// Implement deadlock detection algorithm (Banker's algorithm variation)
export const detectDeadlock = (matrix: AllocationMatrix): DetectionResult => {
  // Deep copy the matrix
  const workingMatrix: AllocationMatrix = JSON.parse(JSON.stringify(matrix));
  
  // Calculate available resources
  workingMatrix.resources = calculateAvailableResources(workingMatrix);
  
  const availableResources: { [resourceId: string]: number } = {};
  workingMatrix.resources.forEach(resource => {
    availableResources[resource.id] = resource.available;
  });
  
  // Track processes that are finished
  const finished = new Set<string>();
  const steps: DetectionStep[] = [];
  const allProcessIds = workingMatrix.processes.map(p => p.id);
  const safeSequence: string[] = [];
  
  // Initial step - show available resources
  steps.push({
    description: "Initial available resources",
    remainingProcesses: [...allProcessIds],
    availableResources: { ...availableResources },
    processedThisRound: []
  });
  
  let changeInLastIteration = true;
  
  while (changeInLastIteration) {
    changeInLastIteration = false;
    const processedThisRound: string[] = [];
    
    for (const process of workingMatrix.processes) {
      // Skip already finished processes
      if (finished.has(process.id)) continue;
      
      // Check if all requested resources can be satisfied
      let canFinish = true;
      
      // For each resource the process requests
      Object.entries(process.request).forEach(([resourceId, requested]) => {
        // Skip if requesting 0
        if (requested <= 0) return;
        
        const available = availableResources[resourceId] || 0;
        if (requested > available) {
          canFinish = false;
        }
      });
      
      if (canFinish) {
        // Process can finish, release its resources
        finished.add(process.id);
        safeSequence.push(process.id);
        Object.entries(process.allocation).forEach(([resourceId, allocated]) => {
          availableResources[resourceId] = (availableResources[resourceId] || 0) + allocated;
        });
        changeInLastIteration = true;
        processedThisRound.push(process.id);
        
        // Add detailed step for this process completion
        let description = `Process ${process.id} can be executed with the available resources.`;
        if (process.request && Object.values(process.request).some(val => val > 0)) {
          description += ` Its resource requests can be satisfied.`;
        }
        description += ` After completion, ${process.id} releases its resources.`;
        
        steps.push({
          description,
          remainingProcesses: allProcessIds.filter(id => !finished.has(id)),
          availableResources: { ...availableResources },
          processedThisRound: [process.id]
        });
        
        // We only process one process at a time for clearer steps
        break;
      }
    }
    
    // If no process could finish in this iteration, and there are still unfinished processes, we have a deadlock
    if (!changeInLastIteration && finished.size < workingMatrix.processes.length) {
      const deadlocked = workingMatrix.processes
        .filter(p => !finished.has(p.id))
        .map(p => p.id);
      
      // Add final step for deadlock detection
      steps.push({
        description: `No process can be satisfied with the available resources. Deadlock detected involving processes: ${deadlocked.join(", ")}`,
        remainingProcesses: deadlocked,
        availableResources: { ...availableResources },
        processedThisRound: []
      });
      
      return {
        deadlocked,
        safeSequence: null,
        steps
      };
    }
  }
  
  // Add final step for safe completion
  if (steps.length > 1) {
    steps.push({
      description: `All processes have been executed successfully. System is in a safe state. Safe sequence: ${safeSequence.join(" → ")}`,
      remainingProcesses: [],
      availableResources: { ...availableResources },
      processedThisRound: []
    });
  }
  
  // No deadlock - determine safe sequence
  return {
    deadlocked: [],
    safeSequence,
    steps
  };
};

export const generateResourceFlowGraph = (matrix: AllocationMatrix) => {
  // Create nodes for processes and resources
  const nodes = [
    // Process nodes
    ...matrix.processes.map(process => ({
      id: process.id,
      type: 'process',
      data: { label: process.id }
    })),
    
    // Resource nodes
    ...matrix.resources.map(resource => ({
      id: resource.id,
      type: 'resource',
      data: { 
        label: resource.id,
        instances: resource.total,
        isMultiInstance: resource.isMultiInstance
      }
    }))
  ];
  
  // Create edges for allocation (resource → process)
  const allocationEdges = matrix.processes.flatMap(process => 
    Object.entries(process.allocation)
      .filter(([_, amount]) => amount > 0)
      .map(([resourceId, amount]) => ({
        id: `${resourceId}-${process.id}`,
        source: resourceId,
        target: process.id,
        type: 'allocation',
        data: { amount }
      }))
  );
  
  // Create edges for request (process → resource)
  const requestEdges = matrix.processes.flatMap(process => 
    Object.entries(process.request)
      .filter(([_, amount]) => amount > 0)
      .map(([resourceId, amount]) => ({
        id: `${process.id}-${resourceId}`,
        source: process.id,
        target: resourceId,
        type: 'request',
        data: { amount }
      }))
  );
  
  return {
    nodes,
    edges: [...allocationEdges, ...requestEdges]
  };
};
