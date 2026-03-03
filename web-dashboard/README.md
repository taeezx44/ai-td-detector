# AI-TD Detector Web Dashboard

Interactive web dashboard for visualizing AI-induced technical debt analysis results.

## 🚀 Features

### 📊 Real-time Analytics
- **Repository Statistics**: Total repos, AI vs Human breakdown
- **Score Comparisons**: Average AI-TD scores with effect size
- **Interactive Charts**: Distribution, dimensions, languages, severity

### 🔍 Repository Analysis
- **Quick Analysis**: Analyze any GitHub repository on-demand
- **Detailed Results**: AI-TD score, dimensions, severity, file counts
- **Filtering & Sorting**: By type, language, score, severity

### 📈 Visualizations
- **Score Distribution**: Histogram comparing AI vs Human repos
- **Dimension Comparison**: Bar chart of technical debt dimensions
- **Language Distribution**: Pie chart of programming languages
- **Severity Distribution**: Stacked bar chart of severity levels

### 📤 Data Management
- **Export**: Download analysis results as CSV
- **Refresh**: Reload latest data from backend
- **Pagination**: Browse large datasets efficiently

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Node.js (for development)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure data directory exists
mkdir -p data

# Load sample dataset (optional)
python scripts/create_sample_dataset.py
```

## 🚀 Running the Dashboard

### Development Mode
```bash
cd web-dashboard
python app.py
```

### Production Mode
```bash
# Using gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Access
Open your browser and navigate to:
- **Local**: http://localhost:5000
- **Network**: http://your-ip:5000

## 📊 API Endpoints

### Statistics
- `GET /api/stats` - Dataset statistics

### Repository Data
- `GET /api/repositories` - Paginated repository list
- `POST /api/analyze` - Analyze single repository

### Charts
- `GET /api/charts/score-distribution` - Score distribution chart
- `GET /api/charts/dimension-comparison` - Dimensions comparison
- `GET /api/charts/language-distribution` - Language distribution
- `GET /api/charts/severity-distribution` - Severity distribution

### Data Export
- `GET /api/export` - Export dataset as CSV

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Custom dataset path
export DATASET_PATH="data/your_dataset.csv"

# Optional: GitHub token for analysis
export GITHUB_TOKEN="your_github_token"
```

### Dashboard Settings
Edit `app.py` to customize:
- Default dataset path
- Chart colors and styling
- Pagination settings
- Analysis parameters

## 📱 Usage Guide

### 1. View Overview
- **Statistics Cards**: Quick overview of dataset
- **Score Comparison**: AI vs Human averages
- **Quick Analysis**: Analyze new repositories

### 2. Explore Charts
- **Score Distribution**: Compare score ranges
- **Dimension Comparison**: See which dimensions differ most
- **Language Distribution**: Understand language breakdown
- **Severity Distribution**: View severity levels

### 3. Browse Repositories
- **Filter**: By type (AI/Human) and language
- **Sort**: By score, stars, or other metrics
- **Paginate**: Navigate through large datasets
- **Details**: Click repository names to view on GitHub

### 4. Analyze New Repositories
1. Enter GitHub repository URL
2. Click "Analyze"
3. View results in the analysis panel

### 5. Export Data
- Click "Export Data" to download CSV
- Includes all repositories with analysis results
- Filename includes timestamp

## 🎨 Customization

### Styling
- Edit `templates/index.html` for UI changes
- Uses Tailwind CSS for styling
- Plotly.js for interactive charts

### Charts
- Modify chart functions in `app.py`
- Customize colors, layouts, and data
- Add new chart types as needed

### Features
- Add new API endpoints
- Extend repository analysis
- Integrate with external services

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Not Loading
```bash
# Check if Flask is running
curl http://localhost:5000/api/stats

# Check logs for errors
python app.py --debug
```

#### No Data Available
```bash
# Ensure dataset exists
ls data/*.csv

# Create sample dataset
python scripts/create_sample_dataset.py
```

#### Charts Not Displaying
- Check browser console for JavaScript errors
- Verify Plotly.js is loading correctly
- Check API responses in Network tab

#### Analysis Not Working
- Verify GitHub token is set (if required)
- Check repository URL format
- Review backend logs for errors

### Performance Tips
- Use pagination for large datasets
- Cache chart data in production
- Optimize database queries
- Use CDN for static assets

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Docker Compose
```yaml
version: '3'
services:
  dashboard:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATASET_PATH=data/merged_real_dataset.csv
    volumes:
      - ./data:/app/data
```

### Cloud Platforms
- **Heroku**: Easy deployment with Git
- **AWS**: Elastic Beanstalk or ECS
- **Google Cloud**: App Engine or Cloud Run
- **Azure**: App Service or Container Instances

## 📈 Monitoring

### Health Checks
- `GET /api/stats` - Backend status
- Response time monitoring
- Error rate tracking

### Analytics
- User interaction tracking
- Popular repositories
- Analysis frequency
- Export usage

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use semantic HTML
- Test API endpoints
- Document new features

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check troubleshooting section
2. Review GitHub issues
3. Create new issue with details
4. Include error logs and screenshots

---

**Built with ❤️ for AI-TD Research**
