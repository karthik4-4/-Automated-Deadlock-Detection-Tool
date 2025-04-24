
import sys
from resource_manager import ResourceManager
from deadlock_detector import DetectionResult

class DeadlockDetectionCLI:
    def __init__(self):
        self.resource_manager = ResourceManager()
        self.commands = {
            "help": self.show_help,
            "add-process": self.add_process,
            "add-resource": self.add_resource,
            "update-allocation": self.update_allocation,
            "update-request": self.update_request,
            "remove-process": self.remove_process,
            "remove-resource": self.remove_resource,
            "show-matrix": self.show_matrix,
            "detect-deadlock": self.detect_deadlock,
            "load-example": self.load_example,
            "clear": self.clear_all,
            "exit": self.exit_program
        }
    
    def run(self):
        print("Deadlock Detection CLI")
        print("Type 'help' for a list of commands")
        
        while True:
            try:
                command = input("\n> ").strip()
                parts = command.split()
                
                if not parts:
                    continue
                    
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for a list of commands.")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
                
            except Exception as e:
                print(f"Error: {e}")
    
    def show_help(self, args):
        print("Available commands:")
        print("  help                                   - Show this help message")
        print("  add-process <process_id>              - Add a new process")
        print("  add-resource <resource_id> [instances] - Add a new resource (default: 1 instance)")
        print("  update-allocation <process> <resource> <value> - Set allocation value")
        print("  update-request <process> <resource> <value> - Set request value")
        print("  remove-process <process_id>           - Remove a process")
        print("  remove-resource <resource_id>         - Remove a resource")
        print("  show-matrix                           - Show allocation and request matrices")
        print("  detect-deadlock                       - Run deadlock detection algorithm")
        print("  load-example                          - Load a sample example")
        print("  clear                                 - Clear all processes and resources")
        print("  exit                                  - Exit the program")
    
    def add_process(self, args):
        if not args:
            print("Error: Process ID is required")
            return
            
        process_id = args[0].upper()
        self.resource_manager.add_process(process_id)
        print(f"Process {process_id} added")
    
    def add_resource(self, args):
        if not args:
            print("Error: Resource ID is required")
            return
            
        resource_id = args[0].upper()
        instances = 1
        
        if len(args) > 1:
            try:
                instances = int(args[1])
            except ValueError:
                print("Error: Instances must be an integer")
                return
        
        self.resource_manager.add_resource(resource_id, instances, instances > 1)
        print(f"Resource {resource_id} added with {instances} instance(s)")
    
    def update_allocation(self, args):
        if len(args) < 3:
            print("Error: Process ID, Resource ID, and value are required")
            return
            
        process_id = args[0].upper()
        resource_id = args[1].upper()
        
        try:
            value = int(args[2])
        except ValueError:
            print("Error: Value must be an integer")
            return
            
        actual_value = self.resource_manager.update_allocation(process_id, resource_id, value)
        print(f"Updated allocation: {process_id} allocated {actual_value} of {resource_id}")
    
    def update_request(self, args):
        if len(args) < 3:
            print("Error: Process ID, Resource ID, and value are required")
            return
            
        process_id = args[0].upper()
        resource_id = args[1].upper()
        
        try:
            value = int(args[2])
        except ValueError:
            print("Error: Value must be an integer")
            return
            
        self.resource_manager.update_request(process_id, resource_id, value)
        print(f"Updated request: {process_id} requesting {value} of {resource_id}")
    
    def remove_process(self, args):
        if not args:
            print("Error: Process ID is required")
            return
            
        process_id = args[0].upper()
        self.resource_manager.remove_process(process_id)
        print(f"Process {process_id} removed")
    
    def remove_resource(self, args):
        if not args:
            print("Error: Resource ID is required")
            return
            
        resource_id = args[0].upper()
        self.resource_manager.remove_resource(resource_id)
        print(f"Resource {resource_id} removed")
    
    def show_matrix(self, args):
        if self.resource_manager.allocation_dataframe.empty:
            print("No processes or resources defined yet")
            return
            
        print("\nAllocation Matrix:")
        print(self.resource_manager.allocation_dataframe)
        
        print("\nRequest Matrix:")
        print(self.resource_manager.request_dataframe)
        
        print("\nAvailable Resources:")
        available = self.resource_manager.get_available_resources()
        for resource_id, count in available.items():
            print(f"{resource_id}: {count}")
    
    def detect_deadlock(self, args):
        if not self.resource_manager.matrix.processes or not self.resource_manager.matrix.resources:
            print("No processes or resources defined yet")
            return
            
        result = self.resource_manager.detect_deadlock()
        
        print("\n" + "="*50)
        if result.deadlocked:
            print(f"DEADLOCK DETECTED! Processes involved: {', '.join(result.deadlocked)}")
        else:
            print("No deadlock detected.")
            print(f"Safe sequence: {' → '.join(result.safe_sequence)}")
        print("="*50)
        
        print("\nStep-by-step explanation:")
        for i, step in enumerate(result.steps):
            print(f"\nStep {i+1}: {step.description}")
            if step.processed_this_round:
                print(f"Processed: {', '.join(step.processed_this_round)}")
            print(f"Available resources: {step.available_resources}")
            if step.remaining_processes:
                print(f"Remaining processes: {', '.join(step.remaining_processes)}")
    
    def load_example(self, args):
        self.resource_manager.load_example()
        print("Loaded sample example")
        self.show_matrix([])
    
    def clear_all(self, args):
        self.resource_manager.clear_all()
        print("Cleared all processes and resources")
    
    def exit_program(self, args):
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    cli = DeadlockDetectionCLI()
    cli.run()
