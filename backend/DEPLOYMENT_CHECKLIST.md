# WeasyPrint Production Deployment Checklist

Use this checklist to ensure WeasyPrint is properly configured for production deployment.

---

## Pre-Deployment

### 1. Version Alignment
- [ ] Update `requirements.txt` to `weasyprint==67.0`
- [ ] Commit version update to git
- [ ] Tag release (e.g., `v1.0.0-weasyprint-67`)

### 2. Local Testing
- [ ] Run verification test: `python test_weasyprint_installation.py`
- [ ] All PDF generation tests pass: `pytest tests/services/test_pdf_generator.py -v`
- [ ] Generate sample PDFs for visual inspection
- [ ] Test with various HTML complexities (simple, tables, images, multi-page)

### 3. Dependencies
- [ ] All Python dependencies installed: `pip install -r requirements.txt`
- [ ] System dependencies documented for target platform
- [ ] Font packages identified and listed

---

## Docker Deployment

### 4. Dockerfile Selection
- [ ] Choose base image:
  - `Dockerfile.ubuntu` - Standard, well-supported (~190 MB)
  - `Dockerfile.alpine` - Smallest size (~75 MB) ✅ RECOMMENDED
  - `Dockerfile.lambda` - AWS Lambda container image (~540 MB)

### 5. Docker Build
```bash
# Build image
docker build -f Dockerfile.alpine -t therapybridge-backend:latest .

# Test locally
docker run -p 8000:8000 therapybridge-backend:latest

# Verify WeasyPrint
docker exec -it <container_id> python test_weasyprint_installation.py
```

- [ ] Docker build succeeds without errors
- [ ] Image size is reasonable (< 200 MB for Alpine)
- [ ] Container starts successfully
- [ ] Health check passes
- [ ] WeasyPrint verification test passes in container

### 6. Docker Registry
```bash
# Tag for registry
docker tag therapybridge-backend:latest your-registry.com/therapybridge:v1.0.0

# Push to registry
docker push your-registry.com/therapybridge:v1.0.0
```

- [ ] Image pushed to registry
- [ ] Image pullable from target environment
- [ ] Version tags applied correctly

---

## AWS Lambda Deployment

### 7. ECR Setup
```bash
# Create ECR repository
aws ecr create-repository --repository-name therapybridge-backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -f Dockerfile.lambda -t therapybridge-lambda .
docker tag therapybridge-lambda:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/therapybridge-backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/therapybridge-backend:latest
```

- [ ] ECR repository created
- [ ] Image pushed to ECR
- [ ] Image URI copied for Lambda configuration

### 8. Lambda Function Configuration
```bash
# Create Lambda function
aws lambda create-function \
    --function-name therapybridge-pdf-generator \
    --package-type Image \
    --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/therapybridge-backend:latest \
    --role arn:aws:iam::123456789012:role/lambda-execution-role \
    --timeout 60 \
    --memory-size 1024 \
    --environment Variables={ENV=production,LOG_LEVEL=info}
```

- [ ] Lambda function created
- [ ] Memory set to at least 1024 MB (for PDF generation)
- [ ] Timeout set to 60 seconds minimum
- [ ] Environment variables configured
- [ ] IAM role has necessary permissions

### 9. Lambda Testing
```bash
# Test Lambda function
aws lambda invoke \
    --function-name therapybridge-pdf-generator \
    --payload '{"action": "health_check"}' \
    response.json

cat response.json
```

- [ ] Lambda function invokes successfully
- [ ] Health check returns 200
- [ ] PDF generation test succeeds
- [ ] CloudWatch logs show no errors

---

## EC2/ECS Deployment

### 10. Server Preparation (Ubuntu)
```bash
# SSH into server
ssh ubuntu@your-server.com

# Update packages
sudo apt-get update

# Install Docker (if not already installed)
sudo apt-get install -y docker.io

# Pull image
sudo docker pull your-registry.com/therapybridge:v1.0.0

# Run container
sudo docker run -d \
    --name therapybridge \
    -p 8000:8000 \
    --restart unless-stopped \
    -v /var/log/therapybridge:/app/logs \
    your-registry.com/therapybridge:v1.0.0
```

- [ ] Server provisioned
- [ ] Docker installed
- [ ] Image pulled successfully
- [ ] Container running
- [ ] Logs directory mounted

### 11. System Dependencies (Non-Docker)
If deploying directly without Docker:

```bash
# Install system dependencies
sudo apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    fonts-dejavu-core

# Install Python dependencies
pip install -r requirements.txt

# Verify
python test_weasyprint_installation.py
```

- [ ] System dependencies installed
- [ ] Python packages installed
- [ ] Verification test passes

---

## Testing in Staging

### 12. Functional Testing
- [ ] Health endpoint responds: `GET /health`
- [ ] PDF generation endpoint works: `POST /api/export/progress-report`
- [ ] Generated PDFs are valid (open in PDF reader)
- [ ] Fonts render correctly
- [ ] Images render correctly (if applicable)
- [ ] Multi-page PDFs work
- [ ] Unicode/special characters render correctly

### 13. Performance Testing
```bash
# Load test PDF generation
# Use tools like Apache Bench, wrk, or Locust

# Example: 100 requests, 10 concurrent
ab -n 100 -c 10 -p test_payload.json -T application/json \
    http://staging.yourapp.com/api/export/progress-report
```

- [ ] Response times acceptable (< 3s for simple PDFs)
- [ ] Memory usage stable (no leaks)
- [ ] CPU usage reasonable
- [ ] No crashes under load
- [ ] Error rate < 1%

### 14. Resource Monitoring
- [ ] Set up memory monitoring
- [ ] Set up CPU monitoring
- [ ] Configure alerts for high memory usage (> 80%)
- [ ] Configure alerts for PDF generation failures

---

## Production Deployment

### 15. Deploy
- [ ] Blue/green deployment or rolling update
- [ ] Smoke test after deployment
- [ ] Monitor logs for errors
- [ ] Verify PDF generation works in production

### 16. Post-Deployment Validation
- [ ] Run verification test: `python test_weasyprint_installation.py`
- [ ] Generate test PDFs
- [ ] Check CloudWatch/application logs
- [ ] Monitor memory usage
- [ ] Monitor error rates

### 17. Rollback Plan
- [ ] Previous Docker image tagged and available
- [ ] Rollback procedure documented
- [ ] Database migrations are reversible (if applicable)

```bash
# Rollback to previous version
docker pull your-registry.com/therapybridge:v0.9.0
docker stop therapybridge
docker rm therapybridge
docker run -d --name therapybridge ... your-registry.com/therapybridge:v0.9.0
```

---

## Monitoring & Alerts

### 18. Application Monitoring
- [ ] PDF generation success rate tracked
- [ ] PDF generation duration tracked
- [ ] Memory usage per PDF generation tracked
- [ ] Error logs aggregated (CloudWatch, Datadog, etc.)

### 19. Alerts Configured
- [ ] Alert on PDF generation failures (> 5% error rate)
- [ ] Alert on high memory usage (> 80%)
- [ ] Alert on slow PDF generation (> 10s)
- [ ] Alert on container/Lambda crashes

---

## Documentation

### 20. Operational Docs
- [ ] Deployment procedure documented
- [ ] Rollback procedure documented
- [ ] Troubleshooting guide created
- [ ] WeasyPrint version documented
- [ ] System dependencies documented

### 21. Runbook
Create runbook with:
- [ ] How to deploy new version
- [ ] How to rollback
- [ ] How to debug PDF generation failures
- [ ] How to scale (increase memory, add instances)
- [ ] Contact information for escalation

---

## Optimization (Optional)

### 22. Performance Tuning
- [ ] Enable PDF caching for frequently generated reports
- [ ] Implement async PDF generation (background jobs)
- [ ] Use task queue (Celery, RQ) for high-volume scenarios
- [ ] Set up dedicated PDF generation workers

### 23. Cost Optimization
- [ ] Right-size memory allocation (start with 1024 MB, adjust based on monitoring)
- [ ] Use Alpine Docker image to reduce storage costs
- [ ] Implement PDF generation rate limiting
- [ ] Consider spot instances for batch PDF generation

---

## Sign-Off

**Deployment Lead:** ___________________________
**Date:** ___________________________
**Environment:** [ ] Staging  [ ] Production
**Version:** ___________________________

**All checklist items completed:** [ ] YES  [ ] NO

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## Quick Reference

**Key Files:**
- `WEASYPRINT_INSTALLATION.md` - Full installation guide
- `WEASYPRINT_QUICKSTART.md` - Quick start commands
- `test_weasyprint_installation.py` - Verification test
- `Dockerfile.ubuntu` - Ubuntu-based Docker image
- `Dockerfile.alpine` - Alpine-based Docker image (smallest)
- `Dockerfile.lambda` - AWS Lambda container image

**Key Commands:**
```bash
# Verify installation
python test_weasyprint_installation.py

# Run PDF tests
pytest tests/services/test_pdf_generator.py -v

# Build Docker image (Alpine)
docker build -f Dockerfile.alpine -t therapybridge:latest .

# Run container
docker run -p 8000:8000 therapybridge:latest
```

**Support:**
- WeasyPrint docs: https://doc.courtbouillon.org/weasyprint/
- GitHub issues: https://github.com/Kozea/WeasyPrint/issues
