#!/usr/bin/env python3
"""
NCBA Safina RAG Assistant - Optimized Startup Manager
Handles service orchestration, port management, and health monitoring
"""
import subprocess
import sys
import signal
import socket
import psutil
import requests
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
SERVICES = {
    'docker': {'cmd': 'docker-compose up -d', 'wait': 10},
    'backend': {'port': BACKEND_PORT, 'health': f'http://localhost:{BACKEND_PORT}/health'},
    'frontend': {'port': FRONTEND_PORT}
}

class ServiceManager:
    def __init__(self):
        self.root = Path(__file__).parent
        self.processes = []
        self._setup_logging()
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
    
    def _setup_logging(self):
        """Configure logging with timestamped files in logs/runtime/"""
        log_dir = self.root / 'logs' / 'runtime'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'startup_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file)
            ]
        )
        self.log = logging.getLogger(__name__)
        self.log.info(f"📝 Logs: {log_file}")
    
    def check_port(self, port: int, name: str) -> bool:
        """Check port availability, offer to kill conflicting processes"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return True
        
        # Port in use - find processes
        procs = [p for p in psutil.process_iter(['pid', 'name']) 
                 if any(c.laddr.port == port for c in p.connections() 
                 if hasattr(c.laddr, 'port'))]
        
        if not procs:
            return False
        
        self.log.warning(f"\n⚠️  Port {port} occupied by: {', '.join(p.info['name'] for p in procs)}")
        
        try:
            choice = input(f"Kill processes on port {port}? (y/N): ").strip().lower()
            if choice == 'y':
                for p in procs:
                    p.terminate()
                    p.wait(timeout=3)
                self.log.info(f"✅ Freed port {port}")
                return True
        except (KeyboardInterrupt, Exception) as e:
            self.log.error(f"❌ Could not free port {port}: {e}")
        
        return False
    
    def start_docker(self):
        """Start Docker services"""
        self.log.info("🐳 Starting Docker services...")
        result = subprocess.run(
            'docker-compose up -d',
            shell=True,
            cwd=self.root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.log.warning(f"⚠️  Docker issue: {result.stderr}")
        else:
            self.log.info("✅ Docker services started")
        
        import time
        time.sleep(10)  # Wait for stabilization
    
    def start_backend(self):
        """Start backend server"""
        if not self.check_port(BACKEND_PORT, 'backend'):
            self.log.error(f"❌ Cannot start backend - port {BACKEND_PORT} unavailable")
            return None
        
        backend_dir = self.root / 'backend'
        venv_python = backend_dir / 'venv' / 'bin' / 'python'
        
        # Setup venv if missing
        if not venv_python.exists():
            self.log.info("📦 Setting up Python environment...")
            subprocess.run('python -m venv venv', shell=True, cwd=backend_dir, check=True)
            subprocess.run(f'{venv_python} -m pip install -r requirements.txt', 
                         shell=True, cwd=backend_dir, check=True)
        
        self.log.info(f"🚀 Starting backend on port {BACKEND_PORT}...")
        proc = subprocess.Popen(
            f'{venv_python} -m uvicorn api.main:app --host 0.0.0.0 --port {BACKEND_PORT}',
            shell=True,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(('backend', proc))
        return proc
    
    def start_frontend(self):
        """Start frontend server"""
        if not self.check_port(FRONTEND_PORT, 'frontend'):
            self.log.error(f"❌ Cannot start frontend - port {FRONTEND_PORT} unavailable")
            return None
        
        frontend_dir = self.root / 'frontend'
        
        # Install deps if missing
        if not (frontend_dir / 'node_modules').exists():
            self.log.info("📦 Installing frontend dependencies...")
            subprocess.run('npm install', shell=True, cwd=frontend_dir, check=True)
        
        self.log.info(f"🚀 Starting frontend on port {FRONTEND_PORT}...")
        proc = subprocess.Popen(
            'npm run dev',
            shell=True,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(('frontend', proc))
        return proc
    
    def health_check(self) -> Dict[str, bool]:
        """Verify services are healthy"""
        import time
        time.sleep(5)  # Wait for startup
        
        health = {}
        
        # Backend health
        try:
            resp = requests.get(f'http://localhost:{BACKEND_PORT}/health', timeout=5)
            health['backend'] = resp.status_code == 200
            self.log.info(f"✅ Backend healthy: {resp.json()}")
        except Exception as e:
            health['backend'] = False
            self.log.warning(f"⚠️  Backend health check failed: {e}")
        
        # Frontend check
        try:
            resp = requests.get(f'http://localhost:{FRONTEND_PORT}', timeout=5)
            health['frontend'] = resp.status_code == 200
            self.log.info("✅ Frontend responsive")
        except Exception as e:
            health['frontend'] = False
            self.log.warning(f"⚠️  Frontend check failed: {e}")
        
        return health
    
    def warmup_llm(self):
        """Warm up LLM with test query"""
        self.log.info("🔥 Warming up LLM...")
        try:
            resp = requests.post(
                f'http://localhost:{BACKEND_PORT}/api/ask',
                json={'query': 'What is LFA?'},
                timeout=30
            )
            if resp.status_code == 200:
                self.log.info("✅ LLM warmed up successfully")
            else:
                self.log.warning(f"⚠️  LLM warmup returned {resp.status_code}")
        except Exception as e:
            self.log.warning(f"⚠️  LLM warmup failed: {e}")
    
    def monitor(self):
        """Monitor running processes"""
        self.log.info("\n" + "="*60)
        self.log.info("🚀 ALL SERVICES STARTED")
        self.log.info("="*60)
        self.log.info(f"📍 Frontend:  http://localhost:{FRONTEND_PORT}")
        self.log.info(f"📍 Backend:   http://localhost:{BACKEND_PORT}")
        self.log.info(f"📍 API Docs:  http://localhost:{BACKEND_PORT}/docs")
        self.log.info("\n💡 Press Ctrl+C to stop all services\n")
        
        import time
        while True:
            time.sleep(5)
            for name, proc in self.processes:
                if proc.poll() is not None:
                    self.log.error(f"❌ {name} stopped unexpectedly (code {proc.returncode})")
                    self.cleanup()
    
    def cleanup(self, *args):
        """Gracefully shutdown all services"""
        self.log.info("\n🛑 Shutting down...")
        
        for name, proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                self.log.info(f"✅ Stopped {name}")
            except:
                proc.kill()
                self.log.warning(f"⚠️  Force killed {name}")
        
        sys.exit(0)
    
    def run(self):
        """Main orchestration"""
        try:
            self.log.info("\n🏦 NCBA SAFINA RAG ASSISTANT\n")
            
            # Start services
            self.start_docker()
            self.start_backend()
            self.start_frontend()
            
            # Health checks
            health = self.health_check()
            
            # Warmup LLM
            if health.get('backend'):
                self.warmup_llm()
            
            # Monitor
            self.monitor()
            
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            self.log.error(f"❌ Fatal error: {e}", exc_info=True)
            self.cleanup()

if __name__ == '__main__':
    ServiceManager().run()