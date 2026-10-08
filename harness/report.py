"""Report generator for ScamShield evaluation harness (JSON and HTML)."""
import json
import os
import time
from typing import Dict, Any

def generate_report(results: Dict[str, Any], output_dir: str = None) -> Dict[str, str]:
    """Generate JSON and HTML reports from harness execution results."""
    if not output_dir:
        output_dir = os.path.dirname(__file__)

    json_path = os.path.join(output_dir, "harness_report.json")
    html_path = os.path.join(output_dir, "harness_report.html")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Write HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ScamShield Safety & Evaluation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 1rem; }}
        .badge {{ padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold; font-size: 0.875rem; }}
        .badge-pass {{ background: #065f46; color: #34d399; }}
        .badge-fail {{ background: #991b1b; color: #f87171; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0; }}
        .card {{ background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; }}
        .card h3 {{ margin: 0 0 0.5rem 0; font-size: 0.875rem; color: #94a3b8; }}
        .card .value {{ font-size: 2rem; font-weight: bold; color: #38bdf8; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; background: #1e293b; border-radius: 0.75rem; overflow: hidden; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #0f172a; color: #94a3b8; font-size: 0.875rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🛡️ ScamShield Harness Report</h1>
                <p style="color: #94a3b8; margin: 0;">Automated Evaluation and Safety Invariant Verification</p>
            </div>
            <span class="badge {'badge-pass' if results.get('all_invariants_passed') else 'badge-fail'}">
                {'ALL INVARIANTS PASSED' if results.get('all_invariants_passed') else 'FAILURES DETECTED'}
            </span>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Golden Catch Rate</h3>
                <div class="value">{results.get('metrics', {}).get('catch_rate', 0)}%</div>
            </div>
            <div class="card">
                <h3>False Positive Rate</h3>
                <div class="value">{results.get('metrics', {}).get('false_positive_rate', 0)}%</div>
            </div>
            <div class="card">
                <h3>Attacks Defended</h3>
                <div class="value">{results.get('adversarial', {}).get('defended', 0)} / {results.get('adversarial', {}).get('total', 0)}</div>
            </div>
            <div class="card">
                <h3>Invariants Checked</h3>
                <div class="value">I1 — I8</div>
            </div>
        </div>

        <h2>Invariant Verification Summary</h2>
        <table>
            <thead>
                <tr><th>ID</th><th>Invariant Assertion</th><th>Status</th></tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{inv['id']}</td><td>{inv['description']}</td><td style='color: {'#34d399' if inv['passed'] else '#f87171'}'>{'PASS' if inv['passed'] else 'FAIL'}</td></tr>" for inv in results.get('invariants', []))}
            </tbody>
        </table>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return {"json": json_path, "html": html_path}
