
import json
import glob
import os
import re
from datetime import datetime

def parse_date_from_filename(filename):
    # expect tft_collection_YYYYMMDD.json
    match = re.search(r'(\d{8})', filename)
    if match:
        return match.group(1)
    return None

def main():
    base_dir = '/Volumes/joaquinu/UIUC 2/tft-data-extraction'
    reports_dir = os.path.join(base_dir, 'reports')
    
    # Find the latest cross_cycle report
    cross_cycle_files = glob.glob(os.path.join(reports_dir, 'cross_cycle_*.json'))
    # Filter out potential non-timestamped files if needed, but the glob catches them all.
    # We want to ignore the generic 'cross_cycle_report.json' if it's old or use it if it's new.
    # Better to rely on the dated ones or just the latest modified.
    
    if not cross_cycle_files:
        print("No cross-cycle reports found.")
        return

    # Sort by modification time to get the latest
    latest_report_path = max(cross_cycle_files, key=os.path.getmtime)
    print(f"Using latest report: {latest_report_path}")

    with open(latest_report_path, 'r') as f:
        cc_data = json.load(f)

    # 1. Extract Quantity & Date Info
    daily_stats = {} # Key: Date string (YYYYMMDD)

    for item in cc_data.get('metrics_summary', []):
        filename = item.get('filename', '')
        date_str = parse_date_from_filename(filename)
        if not date_str:
            continue
        
        daily_stats[date_str] = {
            'players': item.get('total_players', 0),
            'matches': item.get('total_matches', 0),
            'quality_score': None,
            'retention': None
        }

    # 2. Fill Quality Scores from quality_*.json files
    for date_str in daily_stats.keys():
        quality_file = os.path.join(reports_dir, f"quality_{date_str}.json")
        if os.path.exists(quality_file):
            try:
                with open(quality_file, 'r') as f:
                    q_data = json.load(f)
                    if 'quality_score' in q_data and isinstance(q_data['quality_score'], dict):
                        score = q_data['quality_score'].get('overall_score')
                    else:
                        score = q_data.get('overall_score')
                    
                    if score is not None:
                        daily_stats[date_str]['quality_score'] = float(score)
            except Exception as e:
                print(f"Error reading {quality_file}: {e}")

    # 3. Fill Retention Rates
    trends = cc_data.get('continuity_analysis', {}).get('continuity_trends', [])
    if len(trends) == len(cc_data['metrics_summary']) - 1:
        for i, trend in enumerate(trends):
            # trends[i] corresponds to the transition TO metrics_summary[i] (which is the newer file)
            # metrics_summary is sorted presumably Newest -> Oldest based on previous listing.
            # So metrics_summary[0] is newest. trend[0] is retention for that newest file vs previous.
            
            filename = cc_data['metrics_summary'][i]['filename']
            date = parse_date_from_filename(filename)
            if date and date in daily_stats:
                daily_stats[date]['retention'] = trend.get('retention_rate', 0) * 100

    sorted_dates = sorted(daily_stats.keys())

    # 4. Generate Markdown
    md_lines = []
    md_lines.append(f"# Long Term Health Report")
    md_lines.append(f"")
    md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append(f"")

    # Table 1: Quality Score Trend
    md_lines.append(f"## 1. Quality Score Trend")
    md_lines.append(f"| Date | Quality Score |")
    md_lines.append(f"|------|---------------|")
    for date in sorted_dates:
        score = daily_stats[date].get('quality_score')
        score_str = f"{score:.2f}" if score is not None else "N/A"
        md_lines.append(f"| {date} | {score_str} |")
    md_lines.append(f"")

    # Table 2: Data Volume Trend
    md_lines.append(f"## 2. Data Volume Trend")
    md_lines.append(f"| Date | Players | Matches |")
    md_lines.append(f"|------|---------|---------|")
    for date in sorted_dates:
        p = daily_stats[date]['players']
        m = daily_stats[date]['matches']
        md_lines.append(f"| {date} | {p} | {m} |")
    md_lines.append(f"")

    # Table 3: Retention Rates
    md_lines.append(f"## 3. Retention Rates")
    md_lines.append(f"| Cycle | Retention Rate (%) |")
    md_lines.append(f"|-------|--------------------|")
    for date in sorted_dates:
        ret = daily_stats[date]['retention']
        if ret is not None:
             md_lines.append(f"| {date} | {ret:.2f}% |")
    md_lines.append(f"")

    # 4. Summary Analysis
    valid_scores = [d['quality_score'] for d in daily_stats.values() if d['quality_score'] is not None]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    total_collections = len(daily_stats)

    md_lines.append(f"## 4. Summary Analysis")
    md_lines.append(f"- **Average Quality Score:** {avg_score:.2f}")
    md_lines.append(f"- **Total Collections Analyzed:** {total_collections}")
    
    output_path = os.path.join(base_dir, "Documents/LONG_TERM_HEALTH_REPORT_P313.md")
    with open(output_path, 'w') as f:
        f.write("\n".join(md_lines))
    
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    main()
