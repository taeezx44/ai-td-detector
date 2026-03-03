# 🚀 AI-TD Detector Web Dashboard - WSGI Deployment

## 📋 WSGI Server Options

### 1️⃣ Development Server (Testing)
```bash
cd web-dashboard
python app.py
# Runs on http://localhost:5000
```

### 2️⃣ Production WSGI Server (Gunicorn)
```bash
cd web-dashboard
pip install gunicorn
python wsgi_server.py
# Runs on http://localhost:5000 (or $PORT)
```

### 3️⃣ Direct Gunicorn Command
```bash
cd web-dashboard
gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 3 --timeout 120
```

### 4️⃣ Heroku Deployment
```bash
# Deploy to Heroku
git push heroku main
# Automatically uses Procfile
```

### 5️⃣ Render Deployment
- Connect GitHub repository
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn wsgi:application --bind 0.0.0.0:$PORT`

### 6️⃣ Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:5000"]
```

## 🔧 WSGI Configuration

### Gunicorn Settings
- **Workers**: 3 (adjust based on CPU cores)
- **Timeout**: 120s (for large repository analysis)
- **Keepalive**: 5s
- **Max Requests**: 1000 (prevent memory leaks)
- **Log Level**: info

### Environment Variables
```bash
export PORT=5000
export FLASK_ENV=production
export PYTHONPATH=/path/to/ai-td-detector
```

### Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000

## 🌐 Cloud Platform Deployment

### Heroku
1. Create app: `heroku create ai-td-detector`
2. Set buildpack: `heroku buildpacks:set heroku/python`
3. Deploy: `git push heroku main`

### Render
1. Connect GitHub repository
2. Web Service → Python
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn wsgi:application --bind 0.0.0.0:$PORT`

### DigitalOcean App Platform
1. Create app → Python
2. Source Code: GitHub repository
3. Run Command: `gunicorn wsgi:application --bind 0.0.0.0:$PORT`
4. HTTP Port: 5000

### AWS Elastic Beanstalk
1. Create application → Python platform
2. Upload code zip
3. Environment variables: PORT=5000
4. Health check: /

## 📊 Performance Tuning

### For High Traffic
```bash
gunicorn wsgi:application \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class gevent \
  --timeout 120 \
  --keepalive 2 \
  --max-requests 1000 \
  --max-requests-jitter 100
```

### For Memory Optimization
```bash
gunicorn wsgi:application \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --worker-class sync \
  --timeout 120 \
  --max-requests 500 \
  --preload
```

## 🔍 Monitoring

### Health Check Endpoint
```bash
curl http://localhost:5000/health
```

### Logs
```bash
# Access logs
gunicorn --access-logfile access.log wsgi:application

# Error logs
gunicorn --error-logfile error.log wsgi:application
```

### Metrics
- Request rate
- Response time
- Error rate
- Memory usage
- CPU usage

## 🛠️ Troubleshooting

### Common Issues
1. **Port already in use**: Change port or kill existing process
2. **Permission denied**: Use port > 1024 or run with sudo
3. **Module not found**: Check PYTHONPATH and requirements.txt
4. **Timeout errors**: Increase --timeout value
5. **Memory issues**: Reduce workers or add more RAM

### Debug Mode
```bash
export FLASK_ENV=development
python app.py
```

### Production Mode
```bash
export FLASK_ENV=production
gunicorn wsgi:application --bind 0.0.0.0:5000
```
