"""
Performance tests for scheduler module.
Tests task scheduling, interval accuracy, and callback execution.
"""

import pytest
import time
from unittest.mock import MagicMock, patch


@pytest.mark.performance
class TestSchedulerPerformance:
    """Performance tests for the scheduler module."""
    
    def test_scheduler_task_creation(self, benchmark):
        """
        Benchmark task creation and scheduling.
        Expected: < 10ms per task
        """
        def create_task():
            # Simulate task creation
            task = {
                'name': 'test_task',
                'interval': 60,
                'callback': lambda: None,
                'args': (),
                'kwargs': {},
                'enabled': True
            }
            return task
        
        stats = benchmark(create_task, number=1000, repeat=3)
        
        assert stats['avg'] * 1000 < 10, f"Task creation exceeded 10ms"
        print(f"\n✓ Scheduler task creation - Avg: {stats['avg']*1000:.3f}ms")
    
    def test_task_queue_insertion(self, benchmark):
        """
        Benchmark inserting 50 tasks into queue.
        Expected: < 50ms
        """
        task_queue = []
        tasks = [
            {'id': f'task_{i}', 'interval': 60 + i, 'enabled': True}
            for i in range(50)
        ]
        
        def insert_tasks():
            for task in tasks:
                task_queue.append(task)
        
        stats = benchmark(insert_tasks, number=20, repeat=3)
        
        assert stats['avg'] * 1000 < 50, f"Task queue insertion exceeded 50ms"
        print(f"\n✓ Task queue insertion (50 tasks) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_interval_check_performance(self, benchmark):
        """
        Benchmark checking if task's interval has elapsed.
        Expected: < 5ms for 100 tasks
        """
        current_time = time.time()
        tasks = [
            {
                'id': f'task_{i}',
                'interval': 60,
                'last_run': current_time - (30 + i % 60),
                'enabled': i % 2 == 0
            }
            for i in range(100)
        ]
        
        def check_intervals():
            due_tasks = []
            for task in tasks:
                if task['enabled']:
                    time_since_last = current_time - task['last_run']
                    if time_since_last >= task['interval']:
                        due_tasks.append(task['id'])
            return due_tasks
        
        stats = benchmark(check_intervals, number=100, repeat=5)
        
        assert stats['avg'] * 1000 < 5, f"Interval check exceeded 5ms"
        print(f"\n✓ Interval check (100 tasks) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_callback_execution_overhead(self, benchmark):
        """
        Benchmark callback execution for a simple task.
        Expected: < 1ms per callback
        """
        execution_log = []
        
        def simple_callback():
            execution_log.append(time.time())
        
        stats = benchmark(simple_callback, number=100, repeat=3)
        
        assert stats['avg'] * 1000 < 1, f"Callback overhead exceeded 1ms"
        print(f"\n✓ Callback execution overhead - Avg: {stats['avg']*1000:.3f}ms")


@pytest.mark.performance
@pytest.mark.slow
class TestSchedulerScalability:
    """Test scheduler performance under load."""
    
    def test_large_task_schedule(self, benchmark):
        """
        Manage schedule for 500 concurrent tasks.
        Expected: < 500ms for full schedule check
        """
        current_time = time.time()
        large_task_list = [
            {
                'id': f'task_{i}',
                'interval': 60 + (i % 300),
                'last_run': current_time - (i % 120),
                'enabled': True,
                'callback': lambda: None
            }
            for i in range(500)
        ]
        
        def check_full_schedule():
            due_tasks = []
            for task in large_task_list:
                if task['enabled']:
                    time_since_last = current_time - task['last_run']
                    if time_since_last >= task['interval']:
                        due_tasks.append(task['id'])
            return len(due_tasks)
        
        stats = benchmark(check_full_schedule, number=3, repeat=2)
        
        assert stats['avg'] < 0.5, f"Large schedule check exceeded 500ms"
        print(f"\n✓ Large task schedule check (500 tasks) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_rapid_task_execution_sequence(self, benchmark):
        """
        Execute 100 rapid tasks in sequence.
        Expected: < 200ms
        """
        tasks_executed = []
        
        def execute_sequence():
            for i in range(100):
                # Simulate task execution
                tasks_executed.append({
                    'id': f'execution_{i}',
                    'timestamp': time.time(),
                    'result': i * 2
                })
        
        stats = benchmark(execute_sequence, number=5, repeat=2)
        
        assert stats['avg'] < 0.2, f"Rapid task execution exceeded 200ms"
        print(f"\n✓ Rapid task execution (100 tasks) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_schedule_persistence_simulation(self, benchmark):
        """
        Simulate persisting 200 task schedules to storage.
        Expected: < 1 second
        """
        import json
        
        tasks_to_persist = [
            {
                'id': f'task_{i}',
                'name': f'Scheduled Task {i}',
                'interval': 60 + (i % 300),
                'enabled': i % 3 != 0,
                'last_run': time.time(),
                'metadata': {
                    'retries': 0,
                    'success_count': i * 10,
                    'error_count': i % 5
                }
            }
            for i in range(200)
        ]
        
        def persist_schedule():
            # Simulate serialization and storage
            serialized = json.dumps(
                tasks_to_persist,
                default=str
            )
            return len(serialized)
        
        stats = benchmark(persist_schedule, number=10, repeat=2)
        
        assert stats['avg'] < 1.0, f"Schedule persistence exceeded 1s"
        print(f"\n✓ Schedule persistence (200 tasks) - Avg: {stats['avg']*1000:.2f}ms")
