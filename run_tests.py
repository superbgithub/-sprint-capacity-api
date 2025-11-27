"""
Test runner script to execute all test suites.
Usage: python run_tests.py [test_type]

Test types:
- all: Run all tests
- unit: Run only unit tests
- contract: Run only contract tests
- component: Run only component tests
- functional: Run only functional tests
- resiliency: Run only resiliency tests
- performance: Run performance tests with Locust
"""
import sys
import subprocess
import time


def run_pytest(test_path, marker=None):
    """Run pytest with specified path and marker"""
    cmd = ["pytest", test_path, "-v", "--tb=short"]
    
    if marker:
        cmd.extend(["-m", marker])
    
    print(f"\n{'='*60}")
    print(f"Running tests: {test_path}")
    if marker:
        print(f"Marker: {marker}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def run_locust():
    """Run Locust performance tests"""
    print(f"\n{'='*60}")
    print("Starting performance tests with Locust")
    print(f"{'='*60}\n")
    print("Please ensure the FastAPI server is running on http://127.0.0.1:8000")
    print("Then open http://localhost:8089 to start the load test")
    print("Press Ctrl+C to stop")
    print()
    
    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--host=http://127.0.0.1:8000"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nPerformance tests stopped")


def main():
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    test_suites = {
        "unit": ("tests/unit/", "unit"),
        "contract": ("tests/contract/", "contract"),
        "component": ("tests/component/", "component"),
        "functional": ("tests/functional/", "functional"),
        "resiliency": ("tests/resiliency/", "resiliency"),
    }
    
    results = {}
    
    if test_type == "performance":
        run_locust()
        return
    
    if test_type == "all":
        print("\n" + "="*60)
        print("Running ALL test suites")
        print("="*60)
        
        for name, (path, marker) in test_suites.items():
            results[name] = run_pytest(path, marker)
    
    elif test_type in test_suites:
        path, marker = test_suites[test_type]
        results[test_type] = run_pytest(path, marker)
    
    else:
        print(f"Unknown test type: {test_type}")
        print(f"Available types: {', '.join(['all', 'performance'] + list(test_suites.keys()))}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name.upper():20s} {status}")
    
    print("="*60)
    
    # Exit with error if any test failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
