"""
Performance Benchmark System for PC Maintenance Dashboard
Comprehensive system performance testing with CPU, RAM, and Disk I/O benchmarks.
"""

import time
import os
import tempfile
import threading
import math
import random
import json
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import psutil


class BenchmarkWorker(QThread):
    """Worker thread for running performance benchmarks."""
    
    progress_updated = pyqtSignal(int)
    result_updated = pyqtSignal(str)
    test_completed = pyqtSignal(str, dict)
    benchmark_finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, tests_config):
        super().__init__()
        self.tests_config = tests_config
        self.should_stop = False
        self.results = {}
        
    def run(self):
        """Main benchmark execution."""
        try:
            self.result_updated.emit("\n🚀 Starting Performance Benchmark...")
            self.result_updated.emit("=" * 60)
            
            total_tests = sum(1 for test in ['cpu', 'ram', 'disk'] if self.tests_config.get(f'{test}_enabled', False))
            current_test = 0
            
            # System info
            self.result_updated.emit(f"\n📊 System Information:")
            self.result_updated.emit(f"CPU: {psutil.cpu_count()} cores @ {psutil.cpu_freq().max:.0f} MHz")
            self.result_updated.emit(f"RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
            self.result_updated.emit(f"OS: {os.name}")
            
            # CPU Benchmark
            if self.tests_config.get('cpu_enabled', False) and not self.should_stop:
                current_test += 1
                self.result_updated.emit(f"\n🔥 CPU Benchmark Test ({current_test}/{total_tests})")
                self.result_updated.emit("-" * 40)
                cpu_result = self._run_cpu_benchmark()
                self.results['cpu'] = cpu_result
                self.test_completed.emit('cpu', cpu_result)
                
            # RAM Benchmark
            if self.tests_config.get('ram_enabled', False) and not self.should_stop:
                current_test += 1
                self.result_updated.emit(f"\n🧠 RAM Benchmark Test ({current_test}/{total_tests})")
                self.result_updated.emit("-" * 40)
                ram_result = self._run_ram_benchmark()
                self.results['ram'] = ram_result
                self.test_completed.emit('ram', ram_result)
                
            # Disk Benchmark
            if self.tests_config.get('disk_enabled', False) and not self.should_stop:
                current_test += 1
                self.result_updated.emit(f"\n💾 Disk I/O Benchmark Test ({current_test}/{total_tests})")
                self.result_updated.emit("-" * 40)
                disk_result = self._run_disk_benchmark()
                self.results['disk'] = disk_result
                self.test_completed.emit('disk', disk_result)
            
            if not self.should_stop:
                self._generate_summary()
                self.benchmark_finished.emit(self.results)
                
        except Exception as e:
            self.error_occurred.emit(f"Benchmark error: {str(e)}")
    
    def _run_cpu_benchmark(self):
        """Run CPU performance benchmark."""
        duration = self.tests_config.get('duration', 10)
        
        # Prime number calculation test
        self.result_updated.emit("Testing prime number calculations...")
        start_time = time.time()
        prime_count = 0
        operations = 0
        
        while time.time() - start_time < duration and not self.should_stop:
            # Calculate primes up to 1000
            for num in range(2, 1000):
                if self._is_prime(num):
                    prime_count += 1
                operations += 1
                
                if operations % 1000 == 0:
                    elapsed = time.time() - start_time
                    progress = min(int((elapsed / duration) * 100), 100)
                    self.progress_updated.emit(progress)
        
        elapsed_time = time.time() - start_time
        ops_per_second = operations / elapsed_time
        
        # Mathematical computation test
        self.result_updated.emit("Testing mathematical computations...")
        math_start = time.time()
        math_ops = 0
        
        while time.time() - math_start < duration / 2 and not self.should_stop:
            # Complex mathematical operations
            for i in range(1000):
                result = math.sqrt(i) * math.sin(i) + math.cos(i) * math.log(i + 1)
                math_ops += 1
        
        math_elapsed = time.time() - math_start
        math_ops_per_second = math_ops / math_elapsed
        
        # Calculate CPU score
        cpu_score = int((ops_per_second + math_ops_per_second) / 100)
        
        result = {
            'prime_operations': operations,
            'prime_ops_per_second': int(ops_per_second),
            'math_operations': math_ops,
            'math_ops_per_second': int(math_ops_per_second),
            'total_time': elapsed_time + math_elapsed,
            'score': cpu_score
        }
        
        self.result_updated.emit(f"✓ Prime calculations: {operations:,} operations ({int(ops_per_second):,} ops/sec)")
        self.result_updated.emit(f"✓ Math operations: {math_ops:,} operations ({int(math_ops_per_second):,} ops/sec)")
        self.result_updated.emit(f"✓ CPU Score: {cpu_score}")
        
        return result
    
    def _run_ram_benchmark(self):
        """Run RAM performance benchmark."""
        duration = self.tests_config.get('duration', 10)
        
        # Memory allocation test
        self.result_updated.emit("Testing memory allocation and access...")
        start_time = time.time()
        allocations = 0
        total_mb_allocated = 0
        
        arrays = []
        
        while time.time() - start_time < duration and not self.should_stop:
            # Allocate 1MB arrays
            try:
                array_size = 1024 * 1024 // 4  # 1MB of integers
                new_array = [random.randint(1, 1000) for _ in range(array_size)]
                arrays.append(new_array)
                allocations += 1
                total_mb_allocated += 1
                
                # Perform operations on the array
                if len(arrays) > 0:
                    test_array = arrays[-1]
                    # Sort operation
                    sorted_array = sorted(test_array[:1000])
                    # Sum operation
                    array_sum = sum(test_array[:1000])
                
                # Clean up old arrays to prevent memory overflow
                if len(arrays) > 50:
                    arrays.pop(0)
                
                if allocations % 10 == 0:
                    elapsed = time.time() - start_time
                    progress = min(int((elapsed / duration) * 100), 100)
                    self.progress_updated.emit(progress)
                    
            except MemoryError:
                break
        
        elapsed_time = time.time() - start_time
        mb_per_second = total_mb_allocated / elapsed_time
        
        # Memory bandwidth test
        self.result_updated.emit("Testing memory bandwidth...")
        bandwidth_start = time.time()
        bandwidth_ops = 0
        
        # Create large array for bandwidth testing
        test_array = list(range(1000000))  # ~4MB array
        
        while time.time() - bandwidth_start < duration / 2 and not self.should_stop:
            # Memory copy operations
            copied_array = test_array.copy()
            bandwidth_ops += 1
            
            # Memory access patterns
            for i in range(0, len(test_array), 1000):
                value = test_array[i]
                bandwidth_ops += 1
        
        bandwidth_elapsed = time.time() - bandwidth_start
        bandwidth_ops_per_second = bandwidth_ops / bandwidth_elapsed
        
        # Calculate RAM score
        ram_score = int((mb_per_second * 10) + (bandwidth_ops_per_second / 100))
        
        result = {
            'allocations': allocations,
            'total_mb_allocated': total_mb_allocated,
            'mb_per_second': mb_per_second,
            'bandwidth_operations': bandwidth_ops,
            'bandwidth_ops_per_second': bandwidth_ops_per_second,
            'total_time': elapsed_time + bandwidth_elapsed,
            'score': ram_score
        }
        
        self.result_updated.emit(f"✓ Memory allocated: {total_mb_allocated} MB ({mb_per_second:.1f} MB/sec)")
        self.result_updated.emit(f"✓ Bandwidth operations: {bandwidth_ops:,} ({int(bandwidth_ops_per_second):,} ops/sec)")
        self.result_updated.emit(f"✓ RAM Score: {ram_score}")
        
        return result
    
    def _run_disk_benchmark(self):
        """Run disk I/O performance benchmark."""
        test_size_mb = self.tests_config.get('disk_size_mb', 50)
        
        # Create temporary file for testing
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, f"benchmark_test_{int(time.time())}.tmp")
        
        try:
            # Write test
            self.result_updated.emit(f"Testing disk write speed ({test_size_mb} MB)...")
            write_start = time.time()
            
            # Generate test data
            chunk_size = 1024 * 1024  # 1MB chunks
            test_data = b'0' * chunk_size
            
            with open(test_file, 'wb') as f:
                for i in range(test_size_mb):
                    if self.should_stop:
                        break
                    f.write(test_data)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                    
                    progress = int(((i + 1) / test_size_mb) * 50)  # 50% for write
                    self.progress_updated.emit(progress)
            
            write_time = time.time() - write_start
            write_speed = test_size_mb / write_time
            
            # Read test
            self.result_updated.emit(f"Testing disk read speed ({test_size_mb} MB)...")
            read_start = time.time()
            
            with open(test_file, 'rb') as f:
                bytes_read = 0
                while True:
                    if self.should_stop:
                        break
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    
                    progress = 50 + int((bytes_read / (test_size_mb * 1024 * 1024)) * 50)
                    self.progress_updated.emit(min(progress, 100))
            
            read_time = time.time() - read_start
            read_speed = test_size_mb / read_time
            
            # Random access test
            self.result_updated.emit("Testing random access performance...")
            random_start = time.time()
            random_ops = 0
            
            with open(test_file, 'rb') as f:
                file_size = os.path.getsize(test_file)
                for _ in range(100):  # 100 random seeks
                    if self.should_stop:
                        break
                    pos = random.randint(0, file_size - 1024)
                    f.seek(pos)
                    data = f.read(1024)
                    random_ops += 1
            
            random_time = time.time() - random_start
            random_ops_per_second = random_ops / random_time if random_time > 0 else 0
            
            # Calculate disk score
            disk_score = int((write_speed + read_speed) * 2 + random_ops_per_second)
            
            result = {
                'test_size_mb': test_size_mb,
                'write_speed_mb_s': write_speed,
                'read_speed_mb_s': read_speed,
                'write_time': write_time,
                'read_time': read_time,
                'random_operations': random_ops,
                'random_ops_per_second': random_ops_per_second,
                'score': disk_score
            }
            
            self.result_updated.emit(f"✓ Write speed: {write_speed:.1f} MB/s")
            self.result_updated.emit(f"✓ Read speed: {read_speed:.1f} MB/s")
            self.result_updated.emit(f"✓ Random access: {int(random_ops_per_second)} ops/sec")
            self.result_updated.emit(f"✓ Disk Score: {disk_score}")
            
            return result
            
        finally:
            # Clean up test file
            try:
                if os.path.exists(test_file):
                    os.remove(test_file)
            except:
                pass
    
    def _generate_summary(self):
        """Generate benchmark summary."""
        self.result_updated.emit("\n" + "=" * 60)
        self.result_updated.emit("📊 BENCHMARK SUMMARY")
        self.result_updated.emit("=" * 60)
        
        total_score = 0
        test_count = 0
        
        if 'cpu' in self.results:
            cpu_score = self.results['cpu']['score']
            total_score += cpu_score
            test_count += 1
            self.result_updated.emit(f"🔥 CPU Performance Score: {cpu_score}")
            
        if 'ram' in self.results:
            ram_score = self.results['ram']['score']
            total_score += ram_score
            test_count += 1
            self.result_updated.emit(f"🧠 RAM Performance Score: {ram_score}")
            
        if 'disk' in self.results:
            disk_score = self.results['disk']['score']
            total_score += disk_score
            test_count += 1
            self.result_updated.emit(f"💾 Disk Performance Score: {disk_score}")
        
        if test_count > 0:
            overall_score = total_score // test_count
            self.results['overall_score'] = overall_score
            
            self.result_updated.emit("-" * 60)
            self.result_updated.emit(f"🏆 OVERALL PERFORMANCE SCORE: {overall_score}")
            
            # Performance rating
            if overall_score >= 1000:
                rating = "Excellent"
                emoji = "🚀"
            elif overall_score >= 750:
                rating = "Very Good"
                emoji = "⭐"
            elif overall_score >= 500:
                rating = "Good"
                emoji = "👍"
            elif overall_score >= 250:
                rating = "Average"
                emoji = "👌"
            else:
                rating = "Below Average"
                emoji = "⚠️"
            
            self.result_updated.emit(f"{emoji} Performance Rating: {rating}")
            self.results['rating'] = rating
            self.results['rating_emoji'] = emoji
        
        self.result_updated.emit("=" * 60)
        self.result_updated.emit(f"✅ Benchmark completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _is_prime(self, n):
        """Check if a number is prime."""
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True
    
    def stop(self):
        """Stop the benchmark."""
        self.should_stop = True


class BenchmarkExporter:
    """Export benchmark results to various formats."""
    
    @staticmethod
    def export_to_json(results, filename):
        """Export results to JSON file."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'cpu_freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'os': os.name
            },
            'results': results
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    @staticmethod
    def export_to_text(results, filename):
        """Export results to text file."""
        with open(filename, 'w') as f:
            f.write("PC Maintenance Dashboard - Performance Benchmark Results\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # System info
            f.write("System Information:\n")
            f.write("-" * 20 + "\n")
            f.write(f"CPU Cores: {psutil.cpu_count()}\n")
            if psutil.cpu_freq():
                f.write(f"CPU Max Frequency: {psutil.cpu_freq().max:.0f} MHz\n")
            f.write(f"Total RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB\n")
            f.write(f"Operating System: {os.name}\n\n")
            
            # Results
            if 'cpu' in results:
                cpu = results['cpu']
                f.write("CPU Benchmark Results:\n")
                f.write("-" * 25 + "\n")
                f.write(f"Prime Operations: {cpu['prime_operations']:,}\n")
                f.write(f"Prime Ops/Second: {cpu['prime_ops_per_second']:,}\n")
                f.write(f"Math Operations: {cpu['math_operations']:,}\n")
                f.write(f"Math Ops/Second: {cpu['math_ops_per_second']:,}\n")
                f.write(f"CPU Score: {cpu['score']}\n\n")
            
            if 'ram' in results:
                ram = results['ram']
                f.write("RAM Benchmark Results:\n")
                f.write("-" * 25 + "\n")
                f.write(f"Memory Allocated: {ram['total_mb_allocated']} MB\n")
                f.write(f"Allocation Speed: {ram['mb_per_second']:.1f} MB/s\n")
                f.write(f"Bandwidth Operations: {ram['bandwidth_operations']:,}\n")
                f.write(f"Bandwidth Ops/Second: {ram['bandwidth_ops_per_second']:,.0f}\n")
                f.write(f"RAM Score: {ram['score']}\n\n")
            
            if 'disk' in results:
                disk = results['disk']
                f.write("Disk Benchmark Results:\n")
                f.write("-" * 26 + "\n")
                f.write(f"Test Size: {disk['test_size_mb']} MB\n")
                f.write(f"Write Speed: {disk['write_speed_mb_s']:.1f} MB/s\n")
                f.write(f"Read Speed: {disk['read_speed_mb_s']:.1f} MB/s\n")
                f.write(f"Random Access: {disk['random_ops_per_second']:.0f} ops/sec\n")
                f.write(f"Disk Score: {disk['score']}\n\n")
            
            if 'overall_score' in results:
                f.write("Overall Results:\n")
                f.write("-" * 16 + "\n")
                f.write(f"Overall Score: {results['overall_score']}\n")
                f.write(f"Performance Rating: {results.get('rating', 'N/A')}\n")
