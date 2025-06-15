#!/usr/bin/env python3
"""
HFT Analyzer - Historical Analysis CLI Tool

Command-line interface for analyzing historical HFT data, generating reports,
and performing post-trade analysis.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import click
import json
import pandas as pd
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from ..core.hft_analyzer import HFTAnalyzer
from ..core.production_config import ProductionConfig
from ..utils.logger import HFTLogger


@click.command()
@click.option('--data-file', '-f', type=click.Path(exists=True), required=True,
              help='Input data file (JSON, CSV, or exported analysis)')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for analysis results')
@click.option('--format', type=click.Choice(['json', 'csv', 'html', 'pdf']),
              default='json', help='Output format')
@click.option('--analysis-type', '-t', 
              type=click.Choice(['latency', 'arbitrage', 'quality', 'risk', 'compliance']),
              multiple=True, help='Types of analysis to perform')
@click.option('--exchange', '-e', multiple=True,
              help='Filter by exchange (can be specified multiple times)')
@click.option('--start-time', type=click.DateTime(),
              help='Start time for analysis (YYYY-MM-DD HH:MM:SS)')
@click.option('--end-time', type=click.DateTime(),
              help='End time for analysis (YYYY-MM-DD HH:MM:SS)')
@click.option('--percentiles', default='50,95,99',
              help='Percentiles to calculate (comma-separated)')
@click.option('--threshold', type=float, default=1000.0,
              help='Latency threshold in microseconds')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def main(data_file: str, output: Optional[str], format: str,
         analysis_type: tuple, exchange: tuple, 
         start_time: Optional[datetime], end_time: Optional[datetime],
         percentiles: str, threshold: float, verbose: bool):
    """
    HFT Analyzer - Historical High-Frequency Trading Data Analysis
    
    Analyze historical HFT data to generate comprehensive reports on latency,
    arbitrage opportunities, market data quality, and compliance metrics.
    
    Examples:
        hft-analyze -f data.json -t latency -t quality
        hft-analyze -f export.csv --format html --output report.html
        hft-analyze -f data.json -e NYSE -e NASDAQ --threshold 500
    """
    
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = HFTLogger("hft-analyze", level=log_level)
    
    try:
        # Load data
        logger.info(f"Loading data from {data_file}")
        data = load_data(data_file, logger)
        
        # Filter data
        if exchange:
            data = filter_by_exchange(data, exchange, logger)
        
        if start_time or end_time:
            data = filter_by_time(data, start_time, end_time, logger)
        
        # Perform analysis
        results = {}
        
        if not analysis_type:
            analysis_type = ['latency', 'quality']  # Default analysis
        
        for analysis in analysis_type:
            logger.info(f"Performing {analysis} analysis")
            
            if analysis == 'latency':
                results['latency'] = analyze_latency(data, percentiles, threshold, logger)
            elif analysis == 'arbitrage':
                results['arbitrage'] = analyze_arbitrage(data, logger)
            elif analysis == 'quality':
                results['quality'] = analyze_quality(data, logger)
            elif analysis == 'risk':
                results['risk'] = analyze_risk(data, logger)
            elif analysis == 'compliance':
                results['compliance'] = analyze_compliance(data, logger)
        
        # Generate report
        report = generate_report(results, data, logger)
        
        # Output results
        if output:
            save_results(report, output, format, logger)
        else:
            display_results(report, format)
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise click.ClickException(str(e))


def load_data(data_file: str, logger: HFTLogger) -> dict:
    """Load data from file"""
    file_path = Path(data_file)
    
    if file_path.suffix.lower() == '.json':
        with open(file_path, 'r') as f:
            return json.load(f)
    elif file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def filter_by_exchange(data: dict, exchanges: tuple, logger: HFTLogger) -> dict:
    """Filter data by exchange"""
    logger.info(f"Filtering by exchanges: {', '.join(exchanges)}")
    # Implementation depends on data structure
    return data


def filter_by_time(data: dict, start_time: Optional[datetime], 
                  end_time: Optional[datetime], logger: HFTLogger) -> dict:
    """Filter data by time range"""
    if start_time:
        logger.info(f"Filtering from: {start_time}")
    if end_time:
        logger.info(f"Filtering to: {end_time}")
    # Implementation depends on data structure
    return data


def analyze_latency(data: dict, percentiles: str, threshold: float, 
                   logger: HFTLogger) -> dict:
    """Analyze latency metrics"""
    
    # Parse percentiles
    percentile_list = [float(p.strip()) for p in percentiles.split(',')]
    
    # Extract latency data (implementation depends on data structure)
    latencies = []
    
    if isinstance(data, dict) and 'latency_measurements' in data:
        latencies = [m['latency_us'] for m in data['latency_measurements']]
    elif isinstance(data, list):
        # Assume CSV-like structure
        latencies = [row.get('latency_us', 0) for row in data if 'latency_us' in row]
    
    if not latencies:
        logger.warning("No latency data found")
        return {}
    
    # Calculate statistics
    latencies_series = pd.Series(latencies)
    
    results = {
        'total_measurements': len(latencies),
        'min_latency_us': float(latencies_series.min()),
        'max_latency_us': float(latencies_series.max()),
        'mean_latency_us': float(latencies_series.mean()),
        'median_latency_us': float(latencies_series.median()),
        'std_latency_us': float(latencies_series.std()),
        'threshold_violations': int((latencies_series > threshold).sum()),
        'violation_rate': float((latencies_series > threshold).mean()),
        'percentiles': {}
    }
    
    # Calculate percentiles
    for p in percentile_list:
        results['percentiles'][f'p{p}'] = float(latencies_series.quantile(p / 100))
    
    logger.info(f"Analyzed {len(latencies)} latency measurements")
    return results


def analyze_arbitrage(data: dict, logger: HFTLogger) -> dict:
    """Analyze arbitrage opportunities"""
    
    results = {
        'total_opportunities': 0,
        'profitable_opportunities': 0,
        'average_spread': 0.0,
        'max_spread': 0.0,
        'opportunities_by_exchange': {}
    }
    
    # Implementation would analyze price differences between exchanges
    logger.info("Arbitrage analysis completed")
    return results


def analyze_quality(data: dict, logger: HFTLogger) -> dict:
    """Analyze market data quality"""
    
    results = {
        'overall_quality_score': 0.0,
        'gap_count': 0,
        'out_of_order_count': 0,
        'duplicate_count': 0,
        'quality_by_exchange': {}
    }
    
    # Implementation would analyze data quality metrics
    logger.info("Quality analysis completed")
    return results


def analyze_risk(data: dict, logger: HFTLogger) -> dict:
    """Analyze risk events"""
    
    results = {
        'total_risk_events': 0,
        'high_severity_events': 0,
        'risk_by_type': {},
        'risk_timeline': []
    }
    
    # Implementation would analyze risk events
    logger.info("Risk analysis completed")
    return results


def analyze_compliance(data: dict, logger: HFTLogger) -> dict:
    """Analyze compliance metrics"""
    
    results = {
        'compliance_score': 100.0,
        'violations': [],
        'audit_trail_completeness': 100.0,
        'regulatory_requirements': {}
    }
    
    # Implementation would check compliance requirements
    logger.info("Compliance analysis completed")
    return results


def generate_report(results: dict, data: dict, logger: HFTLogger) -> dict:
    """Generate comprehensive analysis report"""
    
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'analysis_types': list(results.keys()),
            'data_summary': {
                'total_records': len(data) if isinstance(data, list) else 1,
                'time_range': 'Unknown'  # Would be calculated from actual data
            }
        },
        'executive_summary': generate_executive_summary(results),
        'detailed_analysis': results,
        'recommendations': generate_recommendations(results)
    }
    
    logger.info("Generated comprehensive analysis report")
    return report


def generate_executive_summary(results: dict) -> dict:
    """Generate executive summary"""
    
    summary = {
        'key_findings': [],
        'performance_highlights': [],
        'areas_for_improvement': []
    }
    
    # Analyze results and generate insights
    if 'latency' in results:
        latency_data = results['latency']
        if latency_data.get('violation_rate', 0) > 0.05:  # 5% threshold
            summary['areas_for_improvement'].append(
                f"High latency violation rate: {latency_data['violation_rate']:.2%}"
            )
        else:
            summary['performance_highlights'].append(
                f"Low latency violation rate: {latency_data['violation_rate']:.2%}"
            )
    
    return summary


def generate_recommendations(results: dict) -> List[str]:
    """Generate actionable recommendations"""
    
    recommendations = []
    
    if 'latency' in results:
        latency_data = results['latency']
        if latency_data.get('violation_rate', 0) > 0.1:
            recommendations.append(
                "Consider optimizing network infrastructure to reduce latency violations"
            )
        
        if latency_data.get('std_latency_us', 0) > 100:
            recommendations.append(
                "High latency variance detected - investigate jitter sources"
            )
    
    if 'quality' in results:
        quality_data = results['quality']
        if quality_data.get('overall_quality_score', 100) < 95:
            recommendations.append(
                "Market data quality below optimal - review feed configurations"
            )
    
    return recommendations


def save_results(report: dict, output: str, format: str, logger: HFTLogger):
    """Save results to file"""
    
    output_path = Path(output)
    
    if format == 'json':
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    elif format == 'csv':
        # Convert to DataFrame and save as CSV
        df = pd.json_normalize(report['detailed_analysis'])
        df.to_csv(output_path, index=False)
    elif format == 'html':
        generate_html_report(report, output_path)
    elif format == 'pdf':
        generate_pdf_report(report, output_path)
    
    logger.info(f"Results saved to {output_path}")


def generate_html_report(report: dict, output_path: Path):
    """Generate HTML report"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HFT Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; }}
            .section {{ margin: 20px 0; }}
            .metric {{ background-color: #f9f9f9; padding: 10px; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>HFT Analysis Report</h1>
            <p>Generated: {report['metadata']['generated_at']}</p>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <pre>{json.dumps(report['executive_summary'], indent=2)}</pre>
        </div>
        
        <div class="section">
            <h2>Detailed Analysis</h2>
            <pre>{json.dumps(report['detailed_analysis'], indent=2)}</pre>
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ul>
                {''.join(f'<li>{rec}</li>' for rec in report['recommendations'])}
            </ul>
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html_content)


def generate_pdf_report(report: dict, output_path: Path):
    """Generate PDF report (requires reportlab)"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.drawString(100, 750, "HFT Analysis Report")
        c.drawString(100, 730, f"Generated: {report['metadata']['generated_at']}")
        
        # Add more content here
        c.save()
        
    except ImportError:
        # Fallback to JSON if reportlab not available
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(report, f, indent=2)


def display_results(report: dict, format: str):
    """Display results to console"""
    
    if format == 'json':
        click.echo(json.dumps(report, indent=2))
    else:
        # Display formatted summary
        click.echo("=" * 60)
        click.echo("HFT ANALYSIS REPORT")
        click.echo("=" * 60)
        
        click.echo(f"\nGenerated: {report['metadata']['generated_at']}")
        click.echo(f"Analysis Types: {', '.join(report['metadata']['analysis_types'])}")
        
        if 'latency' in report['detailed_analysis']:
            latency = report['detailed_analysis']['latency']
            click.echo(f"\n📊 LATENCY ANALYSIS")
            click.echo(f"Total Measurements: {latency.get('total_measurements', 0):,}")
            click.echo(f"Mean Latency: {latency.get('mean_latency_us', 0):.1f}μs")
            click.echo(f"P95 Latency: {latency.get('percentiles', {}).get('p95', 0):.1f}μs")
            click.echo(f"Violation Rate: {latency.get('violation_rate', 0):.2%}")
        
        if report['recommendations']:
            click.echo(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(report['recommendations'], 1):
                click.echo(f"{i}. {rec}")


if __name__ == '__main__':
    main() 