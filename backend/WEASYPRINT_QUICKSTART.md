# WeasyPrint Deployment Quick Start

**TL;DR:** Copy-paste commands to get WeasyPrint working in different environments.

---

## Local Development (macOS)

```bash
# Install system dependencies
brew install cairo pango gdk-pixbuf libffi

# Install WeasyPrint
pip install weasyprint==67.0

# Verify
python test_weasyprint_installation.py
```

---

## Production Server (Ubuntu 22.04 / Debian)

```bash
# Update packages
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    fonts-dejavu-core

# Install WeasyPrint
pip install weasyprint==67.0

# Verify
python test_weasyprint_installation.py
```

---

## Docker (Ubuntu-based)

**Option 1: Use provided Dockerfile**
```bash
# Build image
docker build -f Dockerfile.ubuntu -t therapybridge-backend .

# Run container
docker run -p 8000:8000 therapybridge-backend

# Test
curl http://localhost:8000/health
```

**Option 2: Add to existing Dockerfile**
```dockerfile
# Add this to your existing Dockerfile
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
```

---

## Docker (Alpine-based - Smaller Image)

**Option 1: Use provided Dockerfile**
```bash
# Build image (smaller than Ubuntu)
docker build -f Dockerfile.alpine -t therapybridge-backend:alpine .

# Run container
docker run -p 8000:8000 therapybridge-backend:alpine
```

**Option 2: Add to existing Alpine Dockerfile**
```dockerfile
# Add runtime dependencies
RUN apk add --no-cache \
    cairo \
    pango \
    gdk-pixbuf \
    fontconfig \
    ttf-liberation \
    ttf-dejavu

# Add build dependencies before pip install
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev

# After pip install, remove build deps
RUN apk del .build-deps
```

---

## AWS Lambda (Container Image)

**Step 1: Create Lambda-compatible Dockerfile**
```bash
# Use provided Dockerfile.lambda
docker build -f Dockerfile.lambda -t therapybridge-lambda .
```

**Step 2: Push to ECR**
```bash
# Create ECR repository
aws ecr create-repository --repository-name therapybridge-backend

# Get login token
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag therapybridge-lambda:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/therapybridge-backend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/therapybridge-backend:latest
```

**Step 3: Create Lambda function**
```bash
# Create function from container image
aws lambda create-function \
    --function-name therapybridge-pdf-generator \
    --package-type Image \
    --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/therapybridge-backend:latest \
    --role arn:aws:iam::123456789012:role/lambda-execution-role \
    --timeout 60 \
    --memory-size 1024
```

---

## Verification

**After installation, run verification test:**
```bash
python test_weasyprint_installation.py
```

**Expected output:**
```
✓ ALL TESTS PASSED - WeasyPrint is ready for production
```

**Test PDF generation:**
```bash
python -c "
from weasyprint import HTML
HTML(string='<h1>Test</h1>').write_pdf('/tmp/test.pdf')
print('PDF created: /tmp/test.pdf')
"
```

---

## Troubleshooting

**Problem:** `cannot load library 'gobject-2.0-0'`
```bash
# Ubuntu
sudo apt-get install libglib2.0-0

# Alpine
apk add glib
```

**Problem:** PDFs are blank (no text)
```bash
# Ubuntu
sudo apt-get install fonts-liberation fonts-dejavu-core

# Alpine
apk add ttf-liberation ttf-dejavu
```

**Problem:** `ModuleNotFoundError: No module named 'weasyprint'`
```bash
# Check you're in correct venv
which python
source venv/bin/activate

# Install WeasyPrint
pip install weasyprint==67.0
```

---

## Image Sizes

**Comparison of Docker base images:**

- **Ubuntu (python:3.13-slim):** ~150 MB (base) + 40 MB (deps) = ~190 MB
- **Alpine (python:3.13-alpine):** ~50 MB (base) + 25 MB (deps) = ~75 MB
- **Lambda (public.ecr.aws/lambda/python:3.13):** ~500 MB (base) + 40 MB (deps) = ~540 MB

**Recommendation:** Use Alpine for production containers (60% smaller than Ubuntu).

---

## Next Steps

1. **Update requirements.txt:**
   ```diff
   - weasyprint==60.1
   + weasyprint==67.0
   ```

2. **Choose deployment platform:**
   - Docker on EC2/ECS → Use `Dockerfile.ubuntu` or `Dockerfile.alpine`
   - AWS Lambda → Use `Dockerfile.lambda`
   - Kubernetes → Use `Dockerfile.alpine` (smaller image)

3. **Test in staging:**
   - Build Docker image
   - Run verification tests
   - Generate sample PDFs
   - Load test PDF generation

4. **Monitor in production:**
   - Memory usage (20-50 MB per PDF)
   - Generation time (100ms - 3s depending on complexity)
   - Error rates

---

## Support

- Full documentation: `WEASYPRINT_INSTALLATION.md`
- Test script: `test_weasyprint_installation.py`
- Dockerfiles: `Dockerfile.ubuntu`, `Dockerfile.alpine`, `Dockerfile.lambda`
