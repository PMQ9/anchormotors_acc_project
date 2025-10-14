import pdfplumber
import re
import sys

def extract_metrics(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"
        
        # Use regex to find the metrics in the Summary section
        total_match = re.search(r"Total Tests: (\d+)", all_text)
        passed_match = re.search(r"Passed: (\d+)", all_text)
        warnings_match = re.search(r"Passed with warnings: (\d+)", all_text)
        failed_match = re.search(r"Failed: (\d+)", all_text)
        
        if not all([total_match, passed_match, warnings_match, failed_match]):
            raise ValueError("Could not extract all metrics from PDF. Check PDF structure.")
        
        return {
            "total_tests": int(total_match.group(1)),
            "passed": int(passed_match.group(1)),
            "passed_with_warnings": int(warnings_match.group(1)),
            "failed": int(failed_match.group(1))
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python extract_pdf_report_metrics.py <pdf_path>")
    
    pdf_path = sys.argv[1]
    metrics = extract_metrics(pdf_path)
    
    # Output in key=value format for easy sourcing in GitHub Actions
    print(f"total_tests={metrics['total_tests']}")
    print(f"passed={metrics['passed']}")
    print(f"passed_with_warnings={metrics['passed_with_warnings']}")
    print(f"failed={metrics['failed']}")