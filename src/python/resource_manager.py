
import numpy as np
import pandas as pd
from deadlock_detector import Process, Resource, AllocationMatrix, detect_deadlock

class ResourceManager:
    def __init__(self):
        self.matrix = AllocationMatrix()
        self._allocation_df = None  # DataFrame for allocations
        self._request_df = None     # DataFrame for requests
        self._update_dataframes()
    
    def add_process(self, process_id):
        """Add a new process with the given ID"""
        # Check if process ID already exists
        if any(p.id == process_id for p in self.matrix.processes):
            raise ValueError(f"Process ID '{process_id}' already exists")
            
        # Create new process
        new_process = Process(process_id)
        
        # Initialize allocation and request for existing resources
        for resource in self.matrix.resources:
            new_process.allocation[resource.id] = 0
            new_process.request[resource.id] = 0
            
        # Add to process list
        self.matrix.processes.append(new_process)
        
        # Update DataFrames
        self._update_dataframes()
        return True
    
    def add_resource(self, resource_id, instances=1, is_multi_instance=True):
        """Add a new resource with given ID and instance count"""
        # Check if resource ID already exists
        if any(r.id == resource_id for r in self.matrix.resources):
            raise ValueError(f"Resource ID '{resource_id}' already exists")
            
        # If not multi-instance, force instances to 1
        if not is_multi_instance:
            instances = 1
            
        # Create new resource
        new_resource = Resource(resource_id, instances)
        new_resource.is_multi_instance = is_multi_instance
        
        # Add to existing processes
        for process in self.matrix.processes:
            process.allocation[resource_id] = 0
            process.request[resource_id] = 0
            
        # Add to resource list
        self.matrix.resources.append(new_resource)
        
        # Update DataFrames
        self._update_dataframes()
        return True
    
    def update_allocation(self, process_id, resource_id, value):
        """Update allocation value for a process-resource pair"""
        if value < 0:
            value = 0
            
        # Find process and resource
        process = next((p for p in self.matrix.processes if p.id == process_id), None)
        resource = next((r for r in self.matrix.resources if r.id == resource_id), None)
        
        if not process or not resource:
            raise ValueError(f"Process {process_id} or Resource {resource_id} not found")
            
        # Calculate current allocation for this resource (excluding this process)
        current_allocation = sum(
            p.allocation.get(resource_id, 0) 
            for p in self.matrix.processes 
            if p.id != process_id
        )
        
        # Check if enough instances are available
        max_allowable = resource.total - current_allocation
        if value > max_allowable:
            value = max_allowable
            
        # Update allocation
        process.allocation[resource_id] = value
        
        # Update DataFrames
        self._update_dataframes()
        return value  # Return the actual value set (might be limited)
    
    def update_request(self, process_id, resource_id, value):
        """Update request value for a process-resource pair"""
        if value < 0:
            value = 0
            
        # Find process and resource
        process = next((p for p in self.matrix.processes if p.id == process_id), None)
        resource = next((r for r in self.matrix.resources if r.id == resource_id), None)
        
        if not process or not resource:
            raise ValueError(f"Process {process_id} or Resource {resource_id} not found")
            
        # Update request
        process.request[resource_id] = value
        
        # Update DataFrames
        self._update_dataframes()
        return True
    
    def remove_process(self, process_id):
        """Remove a process by ID"""
        self.matrix.processes = [p for p in self.matrix.processes if p.id != process_id]
        self._update_dataframes()
        return True
    
    def remove_resource(self, resource_id):
        """Remove a resource by ID and update all processes to remove this resource"""
        self.matrix.resources = [r for r in self.matrix.resources if r.id != resource_id]
        
        # Remove resource from all processes' allocation and request
        for process in self.matrix.processes:
            if resource_id in process.allocation:
                del process.allocation[resource_id]
            if resource_id in process.request:
                del process.request[resource_id]
                
        self._update_dataframes()
        return True
    
    def clear_all(self):
        """Clear all processes and resources"""
        self.matrix = AllocationMatrix()
        self._update_dataframes()
        return True
    
    def detect_deadlock(self):
        """Run deadlock detection algorithm using current state"""
        return detect_deadlock(self.matrix)
    
    def _update_dataframes(self):
        """Update pandas DataFrames for allocation and request"""
        # If no processes or resources, create empty DataFrames
        if not self.matrix.processes or not self.matrix.resources:
            self._allocation_df = pd.DataFrame()
            self._request_df = pd.DataFrame()
            return
            
        # Create allocation DataFrame
        alloc_data = {}
        for process in self.matrix.processes:
            alloc_data[process.id] = {r.id: process.allocation.get(r.id, 0) for r in self.matrix.resources}
            
        self._allocation_df = pd.DataFrame(alloc_data).T
        
        # Create request DataFrame
        req_data = {}
        for process in self.matrix.processes:
            req_data[process.id] = {r.id: process.request.get(r.id, 0) for r in self.matrix.resources}
            
        self._request_df = pd.DataFrame(req_data).T
    
    def load_example(self):
        """Load a sample example with predefined processes and resources"""
        self.clear_all()
        
        # Add resources
        self.add_resource("R1", 1, False)
        self.add_resource("R2", 2, True)
        
        # Add processes
        self.add_process("P1")
        self.add_process("P2")
        self.add_process("P3")
        
        # Set allocations
        self.update_allocation("P1", "R1", 1)
        self.update_allocation("P1", "R2", 0)
        self.update_allocation("P2", "R1", 0)
        self.update_allocation("P2", "R2", 1)
        self.update_allocation("P3", "R1", 0)
        self.update_allocation("P3", "R2", 1)
        
        # Set requests
        self.update_request("P1", "R1", 0)
        self.update_request("P1", "R2", 1)
        self.update_request("P2", "R1", 1)
        self.update_request("P2", "R2", 0)
        self.update_request("P3", "R1", 0)
        self.update_request("P3", "R2", 0)
    
    @property
    def allocation_matrix(self):
        """Get allocation matrix as numpy array"""
        return self._allocation_df.to_numpy() if not self._allocation_df.empty else np.array([])
    
    @property
    def request_matrix(self):
        """Get request matrix as numpy array"""
        return self._request_df.to_numpy() if not self._request_df.empty else np.array([])
    
    @property
    def allocation_dataframe(self):
        """Get allocation DataFrame"""
        return self._allocation_df
    
    @property
    def request_dataframe(self):
        """Get request DataFrame"""
        return self._request_df
    
    def get_available_resources(self):
        """Get available resources as a dictionary"""
        resources = {}
        for resource in calculate_available_resources(self.matrix):
            resources[resource.id] = resource.available
        return resources
