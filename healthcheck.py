import sys

try:
    import psutil

    processes = [
        p for p in psutil.process_iter(attrs=['pid', 'name', 'cmdline'])
        if p.info.get('cmdline') and any('audio_worker.py' in part for part in p.info['cmdline'])
    ]

    if not processes:
        print("Audio worker not running")
        sys.exit(1)

    print("Audio worker healthy")
    sys.exit(0)

except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
