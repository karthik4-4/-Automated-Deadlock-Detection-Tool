
import numpy as np
import pandas as pd

class Process:
    def __init__(self, id):
        self.id = id
        self.allocation = {}  # Resources currently allocated to this process
        self.request = {}     # Resources requested by this process

class Resource:
    def __init__(self, id, total):
        self.id = id
        self.total = total
        self.available = total
        self.is_multi_instance = total > 1

class AllocationMatrix:
    def __init__(self):
        self.processes = []
        self.resources = []

class DetectionStep:
    def __init__(self, description, remaining_processes, available_resources, processed_this_round):
        self.description = description
        self.remaining_processes = remaining_processes
        self.available_resources = available_resources
        self.processed_this_round = processed_this_round

class DetectionResult:
    def __init__(self):
        self.deadlocked = []       # Process IDs that are deadlocked
        self.safe_sequence = None  # Safe execution sequence if no deadlock
        self.steps = []            # Steps of algorithm execution

def calculate_available_resources(matrix):
    """Calculate available resources based on total and allocations"""
    resources = [Resource(r.id, r.total) for r in matrix.resources]
    
    # Reset available to total
    for resource in resources:
        resource.available = resource.total
    
    # Subtract allocated resources
    for process in matrix.processes:
        for resource_id, allocated in process.allocation.items():
            for resource in resources:
                if resource.id == resource_id:
                    resource.available -= allocated
    
    return resources

def detect_deadlock(matrix):
    """Implement deadlock detection algorithm (Banker's algorithm variation)"""
    # Deep copy the matrix
    import copy
    working_matrix = copy.deepcopy(matrix)
    
    # Calculate available resources
    working_matrix.resources = calculate_available_resources(working_matrix)
    
    available_resources = {}
    for resource in working_matrix.resources:
        available_resources[resource.id] = resource.available
    
    # Track processes that are finished
    finished = set()
    steps = []
    all_process_ids = [p.id for p in working_matrix.processes]
    safe_sequence = []
    
    # Initial step - show available resources
    steps.append(DetectionStep(
        "Initial available resources",
        all_process_ids.copy(),
        available_resources.copy(),
        []
    ))
    
    change_in_last_iteration = True
    
    while change_in_last_iteration:
        change_in_last_iteration = False
        processed_this_round = []
        
        for process in working_matrix.processes:
            # Skip already finished processes
            if process.id in finished:
                continue
            
            # Check if all requested resources can be satisfied
            can_finish = True
            
            # For each resource the process requests
            for resource_id, requested in process.request.items():
                # Skip if requesting 0
                if requested <= 0:
                    continue
                
                available = available_resources.get(resource_id, 0)
                if requested > available:
                    can_finish = False
                    break
            
            if can_finish:
                # Process can finish, release its resources
                finished.add(process.id)
                safe_sequence.append(process.id)
                
                for resource_id, allocated in process.allocation.items():
                    available_resources[resource_id] = available_resources.get(resource_id, 0) + allocated
                
                change_in_last_iteration = True
                processed_this_round.append(process.id)
                
                # Add detailed step for this process completion
                description = f"Process {process.id} can be executed with the available resources."
                if process.request and any(val > 0 for val in process.request.values()):
                    description += f" Its resource requests can be satisfied."
                description += f" After completion, {process.id} releases its resources."
                
                steps.append(DetectionStep(
                    description,
                    [pid for pid in all_process_ids if pid not in finished],
                    available_resources.copy(),
                    [process.id]
                ))
                
                # We only process one process at a time for clearer steps
                break
        
        # If no process could finish in this iteration, and there are still unfinished processes, we have a deadlock
        if not change_in_last_iteration and len(finished) < len(working_matrix.processes):
            deadlocked = [p.id for p in working_matrix.processes if p.id not in finished]
            
            # Add final step for deadlock detection
            steps.append(DetectionStep(
                f"No process can be satisfied with the available resources. Deadlock detected involving processes: {', '.join(deadlocked)}",
                deadlocked,
                available_resources.copy(),
                []
            ))
            
            result = DetectionResult()
            result.deadlocked = deadlocked
            result.safe_sequence = None
            result.steps = steps
            return result
    
    # Add final step for safe completion
    if len(steps) > 1:
        steps.append(DetectionStep(
            f"All processes have been executed successfully. System is in a safe state. Safe sequence: {' → '.join(safe_sequence)}",
            [],
            available_resources.copy(),
            []
        ))
    
    # No deadlock - return safe sequence
    result = DetectionResult()
    result.deadlocked = []
    result.safe_sequence = safe_sequence
    result.steps = steps
    return result

def generate_resource_flow_graph(matrix):
    """Generate a graph representation of resource allocation"""
    nodes = []
    edges = []
    
    # Create process nodes
    for process in matrix.processes:
        nodes.append({
            "id": process.id,
            "type": "process",
            "data": {"label": process.id}
        })
    
    # Create resource nodes
    for resource in matrix.resources:
        nodes.append({
            "id": resource.id,
            "type": "resource",
            "data": {
                "label": resource.id,
                "instances": resource.total,
                "isMultiInstance": resource.is_multi_instance
            }
        })
    
    # Create allocation edges (resource → process)
    for process in matrix.processes:
        for resource_id, amount in process.allocation.items():
            if amount > 0:
                edges.append({
                    "id": f"{resource_id}-{process.id}",
                    "source": resource_id,
                    "target": process.id,
                    "type": "allocation",
                    "data": {"amount": amount}
                })
    
    # Create request edges (process → resource)
    for process in matrix.processes:
        for resource_id, amount in process.request.items():
            if amount > 0:
                edges.append({
                    "id": f"{process.id}-{resource_id}",
                    "source": process.id,
                    "target": resource_id,
                    "type": "request",
                    "data": {"amount": amount}
                })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

# Example usage function
def run_example():
    """Run an example deadlock detection scenario"""
    matrix = AllocationMatrix()
    
    # Create resources
    r1 = Resource("R1", 1)
    r2 = Resource("R2", 1)
    r3 = Resource("R3", 1)
    matrix.resources = [r1, r2, r3]
    
    # Create processes
    p1 = Process("P1")
    p2 = Process("P2")
    p3 = Process("P3")
    
    # Set allocations
    p1.allocation = {"R1": 1}
    p2.allocation = {"R2": 1}
    p3.allocation = {"R3": 1}
    
    # Set requests
    p1.request = {"R2": 1}
    p2.request = {"R3": 1}
    p3.request = {"R1": 1}
    
    matrix.processes = [p1, p2, p3]
    
    # Run detection algorithm
    result = detect_deadlock(matrix)
    
    # Print results
    if result.deadlocked:
        print(f"Deadlock detected! Processes involved: {', '.join(result.deadlocked)}")
    else:
        print(f"No deadlock. Safe sequence: {' → '.join(result.safe_sequence)}")
    
    print("\nStep-by-step explanation:")
    for i, step in enumerate(result.steps):
        print(f"\nStep {i+1}: {step.description}")
        if step.processed_this_round:
            print(f"Processed: {', '.join(step.processed_this_round)}")
        print(f"Available resources: {step.available_resources}")
        if step.remaining_processes:
            print(f"Remaining processes: {', '.join(step.remaining_processes)}")

if __name__ == "__main__":
    run_example()
