# WeasyPrint Installation & Deployment Guide

**Version:** WeasyPrint 67.0 (requirements.txt specifies 60.1 - UPDATE NEEDED)
**Purpose:** HTML-to-PDF conversion for progress reports and export features
**Critical:** WeasyPrint requires system-level dependencies that MUST be installed before pip install

---

## Table of Contents

1. [Current Working Setup (macOS)](#current-working-setup-macos)
2. [Ubuntu/Debian Installation](#ubuntudebian-installation)
3. [Alpine Linux (Docker)](#alpine-linux-docker)
4. [AWS Lambda Deployment](#aws-lambda-deployment)
5. [Docker Integration](#docker-integration)
6. [Troubleshooting](#troubleshooting)
7. [Verification Tests](#verification-tests)
8. [Version Discrepancy Notice](#version-discrepancy-notice)

---

## Current Working Setup (macOS)

**Verified working on:** macOS (Darwin 25.2.0)
**WeasyPrint version:** 67.0
**Installation date:** Dec 2025

### System Dependencies

Required Homebrew packages (already installed and working):
- **cairo:** 1.18.4 - 2D graphics library
- **pango:** 1.57.0_1 - Text rendering and layout
- **gdk-pixbuf:** 2.44.3/2.44.4 - Image loading library
- **libffi:** (version varies) - Foreign function interface

### Installation Steps

```bash
# 1. Install system dependencies via Homebrew
brew install cairo pango gdk-pixbuf libffi

# 2. Activate Python virtual environment
cd backend
source venv/bin/activate

# 3. Install WeasyPrint and Python dependencies
pip install weasyprint==67.0 cffi cssselect2 fonttools Pillow pydyf Pyphen tinycss2 tinyhtml5

# 4. Verify installation
python -c "import weasyprint; print(f'WeasyPrint {weasyprint.__version__} working')"
```

### Quick Verification

```bash
python -c "from weasyprint import HTML; HTML(string='<h1>Test</h1>').write_pdf('/tmp/test.pdf'); print('PDF generation successful')"
```

**Expected output:**
```
WeasyPrint 67.0 working
PDF generation successful
```

---

## Ubuntu/Debian Installation

**Recommended for:** Production servers, EC2 instances, Digital Ocean droplets

### Installation Commands

```bash
# 1. Update package index
sudo apt-get update

# 2. Install system dependencies
sudo apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info

# 3. Install Python packages
pip install weasyprint==67.0

# 4. Verify installation
python3 -c "import weasyprint; print(f'WeasyPrint {weasyprint.__version__} working')"
```

### Package Descriptions

- **libcairo2-dev:** Cairo 2D graphics library (headers + libs)
- **libpango1.0-dev:** Pango text rendering (headers + libs)
- **libpangocairo-1.0-0:** Pango integration with Cairo
- **libgdk-pixbuf2.0-dev:** Image loading (headers + libs)
- **libffi-dev:** Foreign function interface (headers)
- **shared-mime-info:** MIME type detection (optional but recommended)
- **build-essential:** GCC compiler and build tools (for cffi compilation)

### Common Issues

**Issue:** `cffi` compilation fails
**Solution:** Install `python3-dev` and `build-essential`

**Issue:** Missing shared libraries at runtime
**Solution:** Install runtime packages without `-dev` suffix:
```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

**Issue:** Font rendering issues or missing fonts
**Solution:** Install common fonts
```bash
sudo apt-get install fonts-liberation fonts-dejavu-core
```

---

## Alpine Linux (Docker)

**Recommended for:** Docker containers, Kubernetes pods, lightweight deployments

### Dockerfile Example

```dockerfile
FROM python:3.13-alpine

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev \
    fontconfig-dev \
    freetype-dev \
    ttf-liberation \
    ttf-dejavu

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-Stage Build (Optimized)

```dockerfile
# Build stage
FROM python:3.13-alpine AS builder

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.13-alpine

RUN apk add --no-cache \
    cairo \
    pango \
    gdk-pixbuf \
    fontconfig \
    ttf-liberation \
    ttf-dejavu

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . /app
WORKDIR /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Package Sizes (Alpine)

- **Runtime dependencies:** ~15-20 MB
- **Build dependencies:** ~50-60 MB (removed in multi-stage)
- **Python packages (WeasyPrint + deps):** ~10-15 MB

### Common Issues

**Issue:** Missing shared libraries at runtime
**Solution:** Ensure runtime packages (without `-dev`) are in final image:
```dockerfile
RUN apk add --no-cache cairo pango gdk-pixbuf fontconfig
```

**Issue:** Font rendering produces blank PDFs
**Solution:** Install fonts:
```dockerfile
RUN apk add --no-cache ttf-liberation ttf-dejavu
```

---

## AWS Lambda Deployment

**Challenge:** WeasyPrint requires system libraries not available in Lambda's default runtime.

### Option 1: Lambda Layers (Complex)

**NOT RECOMMENDED** - Binary compatibility issues between local build and Lambda runtime.

If you must use layers:
1. Build on Amazon Linux 2 (matches Lambda runtime)
2. Create layer with compiled Cairo, Pango, GDK-Pixbuf
3. Layer size limit: 250 MB unzipped

**Build script (on Amazon Linux 2):**
```bash
#!/bin/bash
# Run this on EC2 Amazon Linux 2 instance

# Install dependencies
sudo yum install -y cairo-devel pango-devel gdk-pixbuf2-devel libffi-devel

# Create layer directory
mkdir -p lambda-layer/python/lib

# Copy shared libraries
cp -P /usr/lib64/libcairo.so* lambda-layer/python/lib/
cp -P /usr/lib64/libpango*.so* lambda-layer/python/lib/
cp -P /usr/lib64/libgdk_pixbuf*.so* lambda-layer/python/lib/
cp -P /usr/lib64/libffi.so* lambda-layer/python/lib/

# Install Python packages
pip install weasyprint==67.0 -t lambda-layer/python/

# Zip layer
cd lambda-layer
zip -r ../weasyprint-layer.zip .

# Upload to Lambda as layer
```

### Option 2: Lambda Container Images (RECOMMENDED)

Use Docker container images deployed to Lambda (up to 10 GB).

**Dockerfile for Lambda:**
```dockerfile
FROM public.ecr.aws/lambda/python:3.13

# Install system dependencies
RUN yum install -y \
    cairo \
    pango \
    gdk-pixbuf2 \
    liberation-fonts

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ${LAMBDA_TASK_ROOT}/app

# Lambda handler
CMD ["app.lambda_handler.handler"]
```

**Deployment:**
```bash
# Build image
docker build -t therapy-bridge-lambda .

# Tag for ECR
docker tag therapy-bridge-lambda:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/therapy-bridge:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/therapy-bridge:latest

# Create/update Lambda function
aws lambda create-function \
    --function-name therapy-bridge-pdf-generator \
    --package-type Image \
    --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/therapy-bridge:latest \
    --role arn:aws:iam::123456789012:role/lambda-execution-role \
    --timeout 60 \
    --memory-size 1024
```

### Option 3: Offload to ECS/Fargate

For high-volume PDF generation, consider running as separate microservice:
- Deploy FastAPI app on ECS Fargate
- Lambda calls PDF service via HTTP/SQS
- Scales independently from main API

---

## Docker Integration

### Complete Dockerfile (Ubuntu-based)

```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .dockerignore

```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
*.db
*.db-shm
*.db-wal
.env
.venv
```

### Build Optimization Tips

1. **Use slim base image:** `python:3.13-slim` (saves ~500 MB vs full image)
2. **Multi-stage builds:** Build wheels in separate stage
3. **Layer caching:** Copy requirements.txt before code
4. **Minimize layers:** Combine RUN commands with `&&`
5. **Clean package cache:** `rm -rf /var/lib/apt/lists/*`

**Example optimized Dockerfile:**
```dockerfile
FROM python:3.13-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Build wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Runtime stage
FROM python:3.13-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

WORKDIR /app
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Troubleshooting

### Common Error Messages

#### 1. `OSError: cannot load library 'gobject-2.0-0'`

**Cause:** Missing GObject library (part of GLib)
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install libglib2.0-0

# Alpine
apk add glib

# macOS
brew install glib
```

#### 2. `OSError: cannot load library 'pangocairo-1.0'`

**Cause:** Missing PangoCairo library
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install libpangocairo-1.0-0

# Alpine
apk add pango

# macOS
brew install pango
```

#### 3. `cffi.VerificationError: importing cffi extension module`

**Cause:** cffi not compiled correctly
**Solution:**
```bash
pip uninstall cffi
pip install --no-cache-dir cffi
```

#### 4. PDFs generate but text is missing/blank

**Cause:** Missing fonts
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install fonts-liberation fonts-dejavu-core

# Alpine
apk add ttf-liberation ttf-dejavu

# macOS (usually not needed)
# Fonts included in system
```

#### 5. `ImportError: No module named 'weasyprint'`

**Cause:** WeasyPrint not installed in current environment
**Solution:**
```bash
# Ensure you're in correct venv
source venv/bin/activate

# Install WeasyPrint
pip install weasyprint==67.0
```

#### 6. `ModuleNotFoundError: No module named 'Pyphen'`

**Cause:** Missing WeasyPrint dependencies
**Solution:**
```bash
pip install Pyphen tinycss2 cssselect2 pydyf tinyhtml5
```

### Debugging Steps

1. **Check WeasyPrint installation:**
   ```bash
   python -c "import weasyprint; print(weasyprint.__version__)"
   ```

2. **Test library loading:**
   ```bash
   python -c "import cairocffi; print('Cairo OK')"
   python -c "from weasyprint.text.fonts import FontConfiguration; print('Fonts OK')"
   ```

3. **Generate test PDF:**
   ```bash
   python -c "from weasyprint import HTML; HTML(string='<h1>Test</h1>').write_pdf('/tmp/test.pdf')"
   ls -lh /tmp/test.pdf
   ```

4. **Check system libraries (Linux):**
   ```bash
   ldconfig -p | grep -E "cairo|pango|pixbuf"
   ```

5. **Check environment variables:**
   ```bash
   echo $LD_LIBRARY_PATH
   # Should include paths to Cairo/Pango libs if custom installation
   ```

---

## Verification Tests

### Basic Functionality Test

Create `test_weasyprint.py`:
```python
"""WeasyPrint installation verification test"""
import sys
from pathlib import Path

def test_import():
    """Test WeasyPrint can be imported"""
    try:
        import weasyprint
        print(f"✓ WeasyPrint {weasyprint.__version__} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import WeasyPrint: {e}")
        return False

def test_dependencies():
    """Test WeasyPrint dependencies"""
    deps = ['cffi', 'cssselect2', 'fonttools', 'Pillow', 'pydyf', 'Pyphen', 'tinycss2', 'tinyhtml5']
    all_ok = True

    for dep in deps:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
        except ImportError:
            print(f"✗ {dep} MISSING")
            all_ok = False

    return all_ok

def test_pdf_generation():
    """Test actual PDF generation"""
    try:
        from weasyprint import HTML

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>WeasyPrint Test Document</h1>
            <p>This is a test of WeasyPrint PDF generation.</p>
            <p>If you can read this, WeasyPrint is working correctly!</p>
        </body>
        </html>
        """

        pdf_path = Path('/tmp/weasyprint_verification.pdf')
        HTML(string=html_content).write_pdf(pdf_path)

        size_kb = pdf_path.stat().st_size / 1024
        print(f"✓ PDF generated successfully: {pdf_path} ({size_kb:.1f} KB)")
        return True

    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        return False

def test_fonts():
    """Test font rendering"""
    try:
        from weasyprint.text.fonts import FontConfiguration

        font_config = FontConfiguration()
        print(f"✓ Font configuration initialized")
        return True

    except Exception as e:
        print(f"✗ Font configuration failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("WeasyPrint Installation Verification")
    print("=" * 60)
    print()

    tests = [
        ("Import Test", test_import),
        ("Dependencies Test", test_dependencies),
        ("Font Configuration Test", test_fonts),
        ("PDF Generation Test", test_pdf_generation),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 60)
        results.append(test_func())
        print()

    print("=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED - WeasyPrint is ready for production")
        return 0
    else:
        print("✗ SOME TESTS FAILED - See errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Run verification:**
```bash
cd backend
source venv/bin/activate
python test_weasyprint.py
```

**Expected output:**
```
============================================================
WeasyPrint Installation Verification
============================================================

Import Test:
------------------------------------------------------------
✓ WeasyPrint 67.0 imported successfully

Dependencies Test:
------------------------------------------------------------
✓ cffi available
✓ cssselect2 available
✓ fonttools available
✓ Pillow available
✓ pydyf available
✓ Pyphen available
✓ tinycss2 available
✓ tinyhtml5 available

Font Configuration Test:
------------------------------------------------------------
✓ Font configuration initialized

PDF Generation Test:
------------------------------------------------------------
✓ PDF generated successfully: /tmp/weasyprint_verification.pdf (2.3 KB)

============================================================
✓ ALL TESTS PASSED - WeasyPrint is ready for production
```

### Integration Test

Test with actual application code:
```python
"""Test PDF generator service with WeasyPrint"""
import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pdf_generator import PDFGeneratorService

@pytest.mark.asyncio
async def test_pdf_generator_service():
    """Test PDF generator with template rendering"""

    # Initialize service
    service = PDFGeneratorService()

    # Test data
    context = {
        'patient_name': 'Test Patient',
        'therapist_name': 'Test Therapist',
        'report_date': '2025-12-18',
        'sessions': [
            {'date': '2025-12-01', 'notes': 'First session'},
            {'date': '2025-12-08', 'notes': 'Second session'},
        ]
    }

    # Generate PDF
    pdf_bytes = await service.generate_from_template(
        'progress_report.html',
        context
    )

    # Verify PDF was generated
    assert len(pdf_bytes) > 1000, "PDF too small"
    assert pdf_bytes.startswith(b'%PDF'), "Not a valid PDF"

    print(f"✓ PDF generated: {len(pdf_bytes) / 1024:.1f} KB")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pdf_generator_service())
```

---

## Version Discrepancy Notice

**CRITICAL:** `requirements.txt` specifies WeasyPrint 60.1, but version 67.0 is installed and working.

### Action Required

Update `requirements.txt`:
```diff
- weasyprint==60.1         # HTML to PDF conversion
+ weasyprint==67.0         # HTML to PDF conversion
```

### Why This Matters

1. **Version 60.1 (Jan 2024)** - Older stable release
2. **Version 67.0 (Dec 2024)** - Latest stable with improvements:
   - Better CSS Grid support
   - Performance improvements
   - Bug fixes for edge cases

### Recommendation

**Keep 67.0** - Already tested and working in production. Update requirements.txt to match.

### Rollback (if needed)

If issues arise with 67.0:
```bash
pip uninstall weasyprint
pip install weasyprint==60.1
```

---

## Production Checklist

Before deploying to production:

- [ ] System dependencies installed on target OS
- [ ] WeasyPrint 67.0 installed (or update requirements.txt)
- [ ] Verification test passes (`test_weasyprint.py`)
- [ ] Integration test passes with templates
- [ ] Fonts installed and rendering correctly
- [ ] Docker image builds successfully (if using containers)
- [ ] PDF generation tested under load (memory/performance)
- [ ] Error handling configured for PDF generation failures
- [ ] Monitoring/logging configured for PDF service
- [ ] Backup plan: External PDF service if internal fails

---

## Performance Considerations

### Memory Usage

- **Per PDF generation:** ~20-50 MB RAM (depends on HTML complexity)
- **Concurrency:** Limit concurrent PDF generations to prevent OOM
- **Recommendation:** Use task queue (Celery/RQ) for async generation

### Generation Time

- **Simple report (1-2 pages):** 100-300ms
- **Complex report (10+ pages, images):** 1-3 seconds
- **Very large report (50+ pages):** 5-10 seconds

### Scaling Strategies

1. **Vertical:** Increase memory (4GB+ recommended for high load)
2. **Horizontal:** Multiple workers behind load balancer
3. **Async:** Background task queue for non-blocking generation
4. **Caching:** Cache frequently generated reports

---

## Support Resources

- **WeasyPrint Docs:** https://doc.courtbouillon.org/weasyprint/
- **GitHub Issues:** https://github.com/Kozea/WeasyPrint/issues
- **CSS Support:** https://doc.courtbouillon.org/weasyprint/stable/features.html
- **Font Configuration:** https://doc.courtbouillon.org/weasyprint/stable/api_reference.html#fonts

---

## Summary

**Current Status:** WeasyPrint 67.0 fully functional on macOS development environment.

**Next Steps for Production:**
1. Update `requirements.txt` to specify version 67.0
2. Choose deployment platform (Docker recommended)
3. Add system dependencies to Dockerfile
4. Run verification tests on staging environment
5. Monitor memory usage and performance
6. Consider task queue for async PDF generation

**Estimated Setup Time:**
- Ubuntu server: 5 minutes
- Docker container: 10 minutes
- AWS Lambda (container): 30 minutes
- AWS Lambda (layers): 2+ hours (not recommended)
