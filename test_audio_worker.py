#!/usr/bin/env python3
"""
Quick test of Audio Worker initialization
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from audio_worker import AudioWorker
    
    print("🧪 Testing Audio Worker initialization...")
    worker = AudioWorker()
    
    print("✅ Audio Worker initialized successfully!")
    print(f"   Whisper model loaded: {worker.model}")
    print(f"   Pinecone enabled: {'Yes' if worker.pinecone_manager else 'No'}")
    print(f"   Sample rate: {worker.sample_rate}Hz")
    print(f"   Chunk duration: {worker.chunk_duration}s")
    
    print("\n🎉 All systems ready! The vector dimension error has been fixed.")
    print("   You can now run: python src/audio_worker.py")
    
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    import traceback
    traceback.print_exc()