
import subprocess, sys, os

TESTS = [
    "sha_test.py",
    "blockchain_test.py",
    "ledger_test.py",
    "ovt_test.py",
    "paillier_test.py",
    "database_test.py",
]

def run_test(script):
    print(f"\n=== Running {script} ===")
    # Ensure subprocesses can import top-level packages by setting PYTHONPATH to repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    env = os.environ.copy()
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = repo_root + (os.pathsep + prev if prev else "")
    proc = subprocess.run([sys.executable, script], capture_output=True, text=True, env=env)
    if proc.returncode == 0:
        print(proc.stdout.strip())
        print(f"--- {script}: PASS ---")
        return True
    else:
        print(proc.stdout)
        print(proc.stderr)
        print(f"--- {script}: FAIL (exit {proc.returncode}) ---")
        return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    passes = 0
    for t in TESTS:
        if run_test(t):
            passes += 1
    print(f"\nSummary: {passes}/{len(TESTS)} passed")
