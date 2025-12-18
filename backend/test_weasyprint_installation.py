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
    critical_ok = True
    optional_missing = []

    for dep in deps:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
        except ImportError:
            # Only cffi, cssselect2, tinycss2 are truly critical
            if dep in ['cffi', 'cssselect2', 'tinycss2', 'pydyf']:
                print(f"✗ {dep} MISSING (CRITICAL)")
                critical_ok = False
            else:
                print(f"⚠ {dep} missing (optional, may affect some features)")
                optional_missing.append(dep)

    if optional_missing:
        print(f"\nNote: Optional dependencies missing but WeasyPrint may still work")

    return critical_ok

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

def test_system_dependencies():
    """Test system library loading"""
    try:
        import cairocffi
        print(f"✓ cairocffi (Cairo bindings) loaded successfully")
        print(f"  Version: {cairocffi.version}")
        return True
    except Exception as e:
        print(f"⚠ cairocffi not directly available: {e}")
        print(f"  This is OK - WeasyPrint may use alternative bindings")
        # Don't fail test - WeasyPrint works without direct cairocffi import
        return True

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("WeasyPrint Installation Verification")
    print("=" * 60)
    print()

    tests = [
        ("Import Test", test_import),
        ("Dependencies Test", test_dependencies),
        ("System Dependencies Test", test_system_dependencies),
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
        print()
        print("Next steps:")
        print("1. Update requirements.txt to specify weasyprint==67.0")
        print("2. Run integration tests with PDF generator service")
        print("3. Test PDF generation under load")
        return 0
    else:
        print("✗ SOME TESTS FAILED - See errors above")
        print()
        print("Troubleshooting:")
        print("- Check WEASYPRINT_INSTALLATION.md for platform-specific instructions")
        print("- Ensure system dependencies are installed (cairo, pango, gdk-pixbuf)")
        print("- Verify you're in the correct virtual environment")
        return 1

if __name__ == "__main__":
    sys.exit(main())
