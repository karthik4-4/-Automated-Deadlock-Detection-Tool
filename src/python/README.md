
# Deadlock Detection Algorithm in Python

This Python implementation provides a deadlock detection algorithm based on the Banker's Algorithm. It analyzes resource allocation and request patterns to determine if a system is in a deadlock state or if there exists a safe execution sequence.

## Core Components

- `Process`: Represents a process with its resource allocations and requests
- `Resource`: Represents a system resource with a specified number of instances
- `AllocationMatrix`: Contains the state of all processes and resources
- `detect_deadlock()`: The main algorithm that determines if deadlock exists

## How the Algorithm Works

The deadlock detection algorithm works as follows:

1. **Calculate Available Resources**: Determine how many instances of each resource are still available by subtracting allocated resources from total resources.

2. **Iterative Process Execution**:
   - For each process, check if its resource requests can be satisfied with currently available resources.
   - If a process can complete with available resources, simulate its execution by:
     - Marking it as "finished"
     - Adding it to the safe sequence
     - Releasing all resources it was holding (adding them back to available)
   - Continue until either all processes finish (no deadlock) or no process can make progress (deadlock).

3. **Deadlock Identification**:
   - If there are processes that cannot complete because their resource requests cannot be satisfied, and no other process can release resources, a deadlock exists.
   - The algorithm identifies exactly which processes are involved in the deadlock.

## Example

The included `run_example()` function demonstrates a classic deadlock scenario with three processes (P1, P2, P3) and three resources (R1, R2, R3) where:
- P1 holds R1 and needs R2
- P2 holds R2 and needs R3
- P3 holds R3 and needs R1

This creates a circular wait condition, resulting in deadlock.

## Usage

```python
# Create the allocation matrix
matrix = AllocationMatrix()

# Add resources and processes
# Set allocations and requests

# Run the detection algorithm
result = detect_deadlock(matrix)

# Check results
if result.deadlocked:
    print(f"Deadlock detected! Processes involved: {', '.join(result.deadlocked)}")
else:
    print(f"No deadlock. Safe sequence: {' → '.join(result.safe_sequence)}")
```

Each step of the algorithm's execution is recorded in the `steps` field of the result, allowing for detailed explanation of how the algorithm reached its conclusion.
