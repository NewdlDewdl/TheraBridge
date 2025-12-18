# WeasyPrint Documentation Index

**Created:** 2025-12-18 (Wave 2, Feature 7 Validation)
**Total Documentation:** 1,887 lines across 8 files

This directory contains comprehensive WeasyPrint installation and deployment documentation for the TherapyBridge backend.

---

## Quick Start (30 seconds)

```bash
# 1. Verify installation
python test_weasyprint_installation.py

# 2. Choose your deployment platform and see relevant guide:
# - Docker → WEASYPRINT_QUICKSTART.md (section: Docker)
# - AWS Lambda → WEASYPRINT_QUICKSTART.md (section: AWS Lambda)
# - Ubuntu server → WEASYPRINT_QUICKSTART.md (section: Production Server)
```

---

## Documentation Files

### 1. For Quick Deployment
**📄 WEASYPRINT_QUICKSTART.md** (5.1 KB)
- **Use when:** You need copy-paste commands to deploy NOW
- **Contains:** Installation commands for macOS, Ubuntu, Docker, AWS Lambda
- **Time to read:** 3 minutes
- **Start here if:** You're deploying to production today

### 2. For Complete Understanding
**📄 WEASYPRINT_INSTALLATION.md** (20 KB)
- **Use when:** You need deep understanding of WeasyPrint setup
- **Contains:**
  - Current macOS setup details
  - Ubuntu/Debian installation steps
  - Alpine Linux (Docker) configuration
  - AWS Lambda deployment options (layers vs containers)
  - Docker integration with multi-stage builds
  - Common errors and solutions
  - Performance considerations
- **Time to read:** 15 minutes
- **Start here if:** You're planning deployment or troubleshooting

### 3. For Production Deployment
**📄 DEPLOYMENT_CHECKLIST.md** (350+ lines)
- **Use when:** You're deploying to staging/production
- **Contains:**
  - Pre-deployment validation steps
  - Docker build and deployment
  - AWS Lambda deployment
  - EC2/ECS deployment
  - Testing procedures
  - Monitoring setup
  - Rollback procedures
- **Time to complete:** 60-90 minutes
- **Start here if:** You're doing an official production deployment

### 4. For Version Management
**📄 WEASYPRINT_VERSION_UPDATE.md** (3.4 KB)
- **Use when:** Deciding whether to update WeasyPrint version
- **Contains:**
  - Analysis of version discrepancy (60.1 vs 67.0)
  - Pros/cons of each version
  - Update recommendation
  - Rollback plan
- **Time to read:** 5 minutes
- **Start here if:** You're managing dependencies

### 5. For Executive Summary
**📄 WEASYPRINT_DEPLOYMENT_SUMMARY.md** (11 KB)
- **Use when:** You need high-level overview for stakeholders
- **Contains:**
  - What was created (documentation overview)
  - Current status and verification results
  - Key findings and recommendations
  - Deployment paths comparison
  - Performance characteristics
  - Critical action items
- **Time to read:** 10 minutes
- **Start here if:** You're a tech lead or project manager

---

## Docker Templates

### 6. Dockerfile.alpine ✅ RECOMMENDED
- **Size:** ~75 MB (smallest)
- **Base:** python:3.13-alpine
- **Use for:** Production deployments, Kubernetes, cost optimization
- **Build time:** ~3 minutes

### 7. Dockerfile.ubuntu
- **Size:** ~190 MB
- **Base:** python:3.13-slim
- **Use for:** Standard deployments, better compatibility
- **Build time:** ~2 minutes

### 8. Dockerfile.lambda
- **Size:** ~540 MB
- **Base:** public.ecr.aws/lambda/python:3.13
- **Use for:** AWS Lambda container deployments
- **Build time:** ~4 minutes

---

## Test Script

### 9. test_weasyprint_installation.py
- **Purpose:** Automated verification of WeasyPrint installation
- **Tests:**
  - WeasyPrint import and version
  - Required dependencies
  - System library loading
  - Font configuration
  - Actual PDF generation
- **Runtime:** 2-5 seconds
- **Usage:** `python test_weasyprint_installation.py`

---

## Usage Workflows

### Workflow 1: First-Time Setup
```
1. Read: WEASYPRINT_QUICKSTART.md (section for your OS)
2. Install: Follow commands in quickstart
3. Verify: python test_weasyprint_installation.py
4. (Optional) Read: WEASYPRINT_INSTALLATION.md for deep dive
```

### Workflow 2: Docker Deployment
```
1. Choose: Dockerfile.alpine (recommended) or Dockerfile.ubuntu
2. Build: docker build -f Dockerfile.alpine -t therapybridge:latest .
3. Test: docker run -p 8000:8000 therapybridge:latest
4. Verify: docker exec <container> python test_weasyprint_installation.py
5. Deploy: Follow DEPLOYMENT_CHECKLIST.md
```

### Workflow 3: AWS Lambda Deployment
```
1. Read: WEASYPRINT_INSTALLATION.md (AWS Lambda section)
2. Build: docker build -f Dockerfile.lambda -t therapybridge-lambda .
3. Push: Follow ECR push steps in WEASYPRINT_QUICKSTART.md
4. Deploy: Create Lambda function from container image
5. Verify: Test Lambda invocation
6. Monitor: Set up CloudWatch alerts
```

### Workflow 4: Troubleshooting
```
1. Run: python test_weasyprint_installation.py
2. Check: Error messages in output
3. Search: WEASYPRINT_INSTALLATION.md (Troubleshooting section)
4. Fix: Apply solution for your error
5. Verify: Rerun test script
```

---

## Current Status

**✅ WeasyPrint 67.0 - FULLY FUNCTIONAL**

- **Installation:** Working on macOS development environment
- **System Dependencies:** Installed via Homebrew (cairo, pango, gdk-pixbuf)
- **Verification Test:** All tests passing
- **PDF Generation Tests:** 26/26 passing
- **Integration:** Working with PDF generator service

**⚠️ Action Required:** Update requirements.txt from 60.1 to 67.0

---

## Decision Tree

**Are you deploying to production?**
- YES → Start with `DEPLOYMENT_CHECKLIST.md`
- NO → Continue below

**Do you need to install WeasyPrint now?**
- YES → Use `WEASYPRINT_QUICKSTART.md`
- NO → Continue below

**Are you troubleshooting an issue?**
- YES → Run `test_weasyprint_installation.py`, then check `WEASYPRINT_INSTALLATION.md` Troubleshooting section
- NO → Continue below

**Do you need to understand WeasyPrint architecture?**
- YES → Read `WEASYPRINT_INSTALLATION.md`
- NO → Continue below

**Are you managing versions/dependencies?**
- YES → Read `WEASYPRINT_VERSION_UPDATE.md`
- NO → Continue below

**Do you need an executive summary?**
- YES → Read `WEASYPRINT_DEPLOYMENT_SUMMARY.md`
- NO → You probably don't need this documentation right now

---

## File Sizes Summary

| File | Size | Lines | Purpose |
|------|------|-------|---------|
| WEASYPRINT_INSTALLATION.md | 20 KB | ~600 | Complete installation guide |
| WEASYPRINT_DEPLOYMENT_SUMMARY.md | 11 KB | ~450 | Executive summary |
| WEASYPRINT_QUICKSTART.md | 5.1 KB | ~230 | Quick commands |
| test_weasyprint_installation.py | 4.3 KB | ~120 | Verification script |
| WEASYPRINT_VERSION_UPDATE.md | 3.4 KB | ~140 | Version analysis |
| Dockerfile.alpine | 1.1 KB | ~35 | Alpine container |
| Dockerfile.ubuntu | 1.0 KB | ~30 | Ubuntu container |
| Dockerfile.lambda | 880 B | ~27 | Lambda container |
| **TOTAL** | **46.7 KB** | **1,887** | Complete documentation |

---

## Support

**For Installation Issues:**
- Run `python test_weasyprint_installation.py` first
- Check error against `WEASYPRINT_INSTALLATION.md` Troubleshooting section
- Search WeasyPrint docs: https://doc.courtbouillon.org/weasyprint/

**For Deployment Issues:**
- Follow `DEPLOYMENT_CHECKLIST.md` step by step
- Verify Docker build with `docker build -f Dockerfile.alpine .`
- Check CloudWatch/application logs for errors

**For Performance Issues:**
- Review Performance Considerations in `WEASYPRINT_INSTALLATION.md`
- Monitor memory usage (should be 20-50 MB per PDF)
- Consider background task queue for high volume

**For Version Questions:**
- Read `WEASYPRINT_VERSION_UPDATE.md`
- Current recommendation: Use version 67.0

---

## Quick Reference Commands

```bash
# Verify installation
python test_weasyprint_installation.py

# Build Docker image (Alpine - smallest)
docker build -f Dockerfile.alpine -t therapybridge:latest .

# Build Docker image (Ubuntu - more compatible)
docker build -f Dockerfile.ubuntu -t therapybridge:latest .

# Build Lambda image
docker build -f Dockerfile.lambda -t therapybridge-lambda .

# Run container locally
docker run -p 8000:8000 therapybridge:latest

# Test PDF generation
python -c "from weasyprint import HTML; HTML(string='<h1>Test</h1>').write_pdf('/tmp/test.pdf')"

# Run PDF generation tests
pytest tests/services/test_pdf_generator.py -v
```

---

## What's Next

1. **Immediate:** Update requirements.txt to weasyprint==67.0
2. **Short-term:** Choose deployment platform (Docker recommended)
3. **Medium-term:** Deploy to staging using DEPLOYMENT_CHECKLIST.md
4. **Long-term:** Monitor performance and optimize as needed

---

**Last Updated:** 2025-12-18
**Maintainer:** Backend Dev Team
**Version:** 1.0
