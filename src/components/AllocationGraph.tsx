import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AllocationMatrix, generateResourceFlowGraph } from '@/utils/deadlockAlgorithm';
import { Circle, Square } from 'lucide-react';
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  useReactFlow,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

type AllocationGraphProps = {
  matrix: AllocationMatrix;
  deadlockedProcesses: string[];
};

// Custom Process Node
const ProcessNode = ({ data }: { data: any }) => {
  const isDeadlocked = data.deadlocked;
  
  return (
    <div className={`w-16 h-16 rounded-full bg-green-50 border-2 border-green-200 flex items-center justify-center ${isDeadlocked ? 'animate-pulse-gentle bg-red-100 border-red-200' : ''}`}>
      <div className="text-lg font-semibold text-gray-700">{data.label}</div>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};

// Custom Resource Node
const ResourceNode = ({ data }: { data: any }) => {
  const dots = Array(data.instances).fill(0);
  
  return (
    <div className="relative">
      <div className="w-16 h-12 bg-emerald-600 flex flex-col items-center justify-center rounded-sm">
        <div className="text-white font-semibold mb-1">{data.label}</div>
        <div className="flex gap-1 justify-center">
          {dots.map((_, index) => (
            <div key={index} className="w-2 h-2 bg-white rounded-full" />
          ))}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} />
      <Handle type="target" position={Position.Top} />
    </div>
  );
};

const nodeTypes = {
  process: ProcessNode,
  resource: ResourceNode,
};

const AllocationGraphContent = ({ matrix, deadlockedProcesses }: AllocationGraphProps) => {
  const { fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isLocked, setIsLocked] = useState(false);

  useEffect(() => {
    if (matrix.processes.length === 0 || matrix.resources.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const { nodes: graphNodes, edges: graphEdges } = generateResourceFlowGraph(matrix);

    // Position nodes in a more organized layout
    const processNodes = graphNodes
      .filter(n => n.type === 'process')
      .map((node, idx) => ({
        ...node,
        position: { x: 100 + (idx * 200), y: 200 },
        data: {
          ...node.data,
          deadlocked: deadlockedProcesses.includes(node.id)
        }
      }));
    
    const resourceNodes = graphNodes
      .filter(n => n.type === 'resource')
      .map((node, idx) => ({
        ...node,
        position: { x: 100 + (idx * 200), y: 50 }
      }));
    
    const styledEdges = graphEdges.map(edge => ({
      ...edge,
      style: { 
        stroke: '#000',
        strokeWidth: 1.5
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 20,
        height: 20,
        color: '#000'
      },
      label: edge.data.amount > 1 ? `${edge.data.amount}` : '',
      animated: edge.type === 'request'
    }));

    setNodes([...processNodes, ...resourceNodes]);
    setEdges(styledEdges);
    
    setTimeout(() => {
      fitView({ padding: 0.5 });
    }, 50);
  }, [matrix, deadlockedProcesses, setNodes, setEdges, fitView]);

  return (
    <div className="flex flex-col h-[500px]">
      {matrix.processes.length === 0 || matrix.resources.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
          <p>Add processes and resources to visualize the allocation graph</p>
        </div>
      ) : (
        <>
          <div className="relative flex-grow border rounded-lg">
            <div className="absolute top-2 right-2 z-10">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsLocked(!isLocked)}
              >
                {isLocked ? "Unlock Graph" : "Lock Graph"}
              </Button>
            </div>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              zoomOnScroll={!isLocked}
              panOnScroll={!isLocked}
              zoomOnPinch={!isLocked}
              panOnDrag={!isLocked}
              zoomOnDoubleClick={!isLocked}
              nodesDraggable={!isLocked}
            >
              <Background />
              <Controls />
            </ReactFlow>
          </div>
          
          <div className="flex justify-center mt-4 gap-x-6 p-4 border-t">
            <div className="flex items-center gap-x-2">
              <div className="w-3 h-3 rounded-full bg-green-50 border-2 border-green-200" />
              <span className="text-sm">Process</span>
            </div>
            <div className="flex items-center gap-x-2">
              <div className="w-3 h-3 bg-emerald-600" />
              <span className="text-sm">Resource</span>
            </div>
            <div className="flex items-center gap-x-2">
              <div className="w-2 h-2 bg-white border border-emerald-600 rounded-full" />
              <span className="text-sm">Resource Instance</span>
            </div>
            <div className="flex items-center gap-x-2">
              <div className="h-0.5 w-5 bg-black" />
              <span className="text-sm">Allocation/Request</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const AllocationGraph: React.FC<AllocationGraphProps> = ({ matrix, deadlockedProcesses }) => {
  return (
    <Card className="w-full shadow-lg">
      <CardHeader>
        <CardTitle>Resource Allocation Graph</CardTitle>
        <CardDescription>
          Visualizes the allocation and request relationships between processes and resources
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ReactFlowProvider>
          <AllocationGraphContent matrix={matrix} deadlockedProcesses={deadlockedProcesses} />
        </ReactFlowProvider>
      </CardContent>
    </Card>
  );
};

export default AllocationGraph;
