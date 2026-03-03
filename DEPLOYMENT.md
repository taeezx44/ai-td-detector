# 🚀 AI-TD Detector Deployment Guide

## 📦 Deployment Options

### 1️⃣ VS Code Extension (Recommended for Developers)

**Installation:**
```bash
# Option 1: Install from GitHub
code --install-extension https://github.com/taeezx44/ai-td-detector/releases/download/v1.0.0/ai-td-detector-1.0.0.vsix

# Option 2: Download and install manually
wget https://github.com/taeezx44/ai-td-detector/releases/download/v1.0.0/ai-td-detector-1.0.0.vsix
code --install-extension ai-td-detector-1.0.0.vsix
```

**Configuration:**
```json
{
  "aitd.enginePath": "/path/to/ai-td-detector",
  "aitd.pythonPath": "python3",
  "aitd.autoAnalyzeOnSave": true,
  "aitd.showInlineAnnotations": true,
  "aitd.severityThreshold": "medium"
}
```

**Enterprise Deployment:**
```bash
# Deploy to multiple machines
for machine in machine1 machine2 machine3; do
  ssh $machine "code --install-extension ai-td-detector-1.0.0.vsix"
done
```

---

### 2️⃣ Web Dashboard (For Teams/CI/CD)

**Local Development:**
```bash
cd web-dashboard
pip install -r requirements.txt
python app.py
```

**Production Deployment (Docker):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  ai-td-dashboard:
    build: ./web-dashboard
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
```

**Cloud Deployment Options:**

| Platform | Setup | Cost | Scaling |
|----------|-------|------|----------|
| **Heroku** | `git push heroku main` | Free tier | Easy |
| **Railway** | Connect GitHub repo | $5+/mo | Auto-scaling |
| **DigitalOcean** | Docker deployment | $4+/mo | Manual |
| **AWS** | ECS + RDS | $10+/mo | Enterprise |

---

### 3️⃣ CLI Tool (For CI/CD Pipelines)

**Installation:**
```bash
# Global install
pip install git+https://github.com/taeezx44/ai-td-detector.git

# Local install
git clone https://github.com/taeezx44/ai-td-detector.git
cd ai-td-detector
pip install -e .
```

**GitHub Actions Integration:**
```yaml
name: AI-TD Analysis
on: [push, pull_request]

jobs:
  ai-td-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install AI-TD Detector
      run: |
        pip install git+https://github.com/taeezx44/ai-td-detector.git
    
    - name: Analyze Repository
      run: |
        ai-td-analyze --directory . --output ai-td-results.json
    
    - name: Upload Results
      uses: actions/upload-artifact@v3
      with:
        name: ai-td-results
        path: ai-td-results.json
```

**GitLab CI:**
```yaml
ai_td_analysis:
  stage: test
  image: python:3.11
  script:
    - pip install git+https://github.com/taeezx44/ai-td-detector.git
    - ai-td-analyze --directory . --output ai-td-results.json
  artifacts:
    reports:
      junit: ai-td-results.json
```

---

### 4️⃣ API Service (For Integration)

**FastAPI Service:**
```python
# api_server.py
from fastapi import FastAPI
from engine.main import analyze_directory
import uvicorn

app = FastAPI()

@app.post("/analyze")
async def analyze_repo(repo_url: str):
    results = analyze_directory(repo_url)
    return {"ai_td_score": results.total_score, "details": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Deployment:**
```bash
pip install fastapi uvicorn
python api_server.py
```

**Client Usage:**
```python
import requests

response = requests.post("http://localhost:8000/analyze", 
                        json={"repo_url": "https://github.com/user/repo"})
print(response.json())
```

---

## 🔧 Configuration Management

### Environment Variables
```bash
export AI_TD_ENGINE_PATH="/path/to/engine"
export AI_TD_PYTHON_PATH="python3"
export AI_TD_LOG_LEVEL="INFO"
export AI_TD_CACHE_DIR="/tmp/ai-td-cache"
```

### Configuration File
```yaml
# ai-td-config.yaml
engine:
  path: "/opt/ai-td-detector/engine"
  python: "python3.11"

weights:
  complexity: 0.30
  duplication: 0.25
  documentation: 0.20
  error_handling: 0.25

thresholds:
  low: 0.30
  medium: 0.60
  high: 1.00

cache:
  enabled: true
  ttl: 3600
  directory: "/tmp/ai-td-cache"
```

---

## 📊 Monitoring & Logging

### Health Check Endpoint
```python
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### Metrics Collection
```python
from prometheus_client import Counter, Histogram

ai_td_analyses = Counter('ai_td_analyses_total', 'Total AI-TD analyses')
ai_td_duration = Histogram('ai_td_analysis_duration_seconds', 'Analysis duration')
```

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ai-td-detector.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🚀 Production Checklist

### Security
- [ ] Validate input file paths
- [ ] Sanitize user inputs
- [ ] Rate limiting for API endpoints
- [ ] HTTPS for web dashboard
- [ ] Authentication for sensitive operations

### Performance
- [ ] Implement caching for repeated analyses
- [ ] Use async processing for large repositories
- [ ] Optimize Tree-sitter parsing
- [ ] Monitor memory usage

### Reliability
- [ ] Error handling for network requests
- [ ] Graceful degradation for unsupported files
- [ ] Retry logic for GitHub API calls
- [ ] Backup and recovery procedures

### Scalability
- [ ] Horizontal scaling for web dashboard
- [ ] Load balancing for API services
- [ ] Distributed processing for large analyses
- [ ] Database for storing analysis results

---

## 🛠️ Troubleshooting

### Common Issues

**Extension not loading:**
```bash
# Check extension installation
code --list-extensions | grep ai-td

# Reinstall extension
code --uninstall-extension korawit-chuluen.ai-td-detector
code --install-extension ai-td-detector-1.0.0.vsix
```

**Python engine not found:**
```bash
# Check Python path
which python3
python3 --version

# Update VS Code settings
{
  "aitd.pythonPath": "/usr/bin/python3"
}
```

**Dashboard not starting:**
```bash
# Check dependencies
pip install -r web-dashboard/requirements.txt

# Check port availability
netstat -tulpn | grep 5000

# Run in debug mode
FLASK_ENV=development python app.py
```

### Support Channels

- **GitHub Issues**: https://github.com/taeezx44/ai-td-detector/issues
- **Documentation**: https://github.com/taeezx44/ai-td-detector/wiki
- **Discussions**: https://github.com/taeezx44/ai-td-detector/discussions

---

## 📈 Success Metrics

### Adoption Metrics
- Extension downloads and installations
- Dashboard active users
- API request volume
- CI/CD pipeline integrations

### Quality Metrics
- Analysis accuracy (false positive/negative rates)
- Processing time per repository
- User satisfaction scores
- Bug reports and resolution time

### Business Impact
- Reduction in technical debt
- Improved code review efficiency
- Developer productivity gains
- Cost savings from early detection

---

**🎉 Ready to deploy AI-TD Detector in your organization!**

For questions or support, visit our [GitHub repository](https://github.com/taeezx44/ai-td-detector).
