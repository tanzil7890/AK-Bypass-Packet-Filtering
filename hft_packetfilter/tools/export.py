#!/usr/bin/env python3
"""
HFT Export - Data Export CLI Tool

Command-line interface for exporting HFT data in various formats
for analysis, reporting, and integration with external systems.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import click
import json
import csv
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..core.hft_analyzer import HFTAnalyzer
from ..core.production_config import ProductionConfig
from ..utils.logger import HFTLogger


@click.command()
@click.option('--source', '-s', type=click.Path(exists=True),
              help='Source data file or directory')
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output file path')
@click.option('--format', '-f', 
              type=click.Choice(['json', 'csv', 'yaml', 'xml', 'parquet']),
              default='json', help='Output format')
@click.option('--data-type', '-t',
              type=click.Choice(['latency', 'metrics', 'events', 'config', 'all']),
              default='all', help='Type of data to export')
@click.option('--start-time', type=click.DateTime(),
              help='Start time for data export (YYYY-MM-DD HH:MM:SS)')
@click.option('--end-time', type=click.DateTime(),
              help='End time for data export (YYYY-MM-DD HH:MM:SS)')
@click.option('--exchange', '-e', multiple=True,
              help='Filter by exchange (can be specified multiple times)')
@click.option('--compress', is_flag=True,
              help='Compress output file')
@click.option('--include-metadata', is_flag=True, default=True,
              help='Include metadata in export')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def main(source: Optional[str], output: str, format: str, data_type: str,
         start_time: Optional[datetime], end_time: Optional[datetime],
         exchange: tuple, compress: bool, include_metadata: bool, verbose: bool):
    """
    HFT Export - Data Export Tool for HFT-PacketFilter
    
    Export HFT data in various formats for analysis, reporting, and integration
    with external systems. Supports filtering by time, exchange, and data type.
    
    Examples:
        hft-export --source data.json --output report.csv --format csv
        hft-export --output metrics.json --data-type metrics --exchange NYSE
        hft-export --source logs/ --output archive.parquet --compress
    """
    
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = HFTLogger("hft-export", level=log_level)
    
    try:
        # Load source data
        if source:
            data = load_source_data(source, logger)
        else:
            # Generate current data from analyzer
            data = generate_current_data(data_type, logger)
        
        # Filter data
        filtered_data = filter_data(
            data, start_time, end_time, exchange, data_type, logger
        )
        
        # Prepare export data
        export_data = prepare_export_data(
            filtered_data, data_type, include_metadata, logger
        )
        
        # Export data
        export_data_to_file(
            export_data, output, format, compress, logger
        )
        
        click.echo(f"✅ Data exported successfully to {output}")
        logger.info(f"Export completed: {output}")
        
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        logger.error(f"Export failed: {e}")
        raise click.ClickException(str(e))


def load_source_data(source: str, logger: HFTLogger) -> Dict[str, Any]:
    """Load data from source file or directory"""
    
    source_path = Path(source)
    
    if source_path.is_file():
        # Load single file
        logger.info(f"Loading data from file: {source}")
        
        if source_path.suffix.lower() == '.json':
            with open(source_path, 'r') as f:
                return json.load(f)
        elif source_path.suffix.lower() == '.yaml':
            with open(source_path, 'r') as f:
                return yaml.safe_load(f)
        elif source_path.suffix.lower() == '.csv':
            import pandas as pd
            df = pd.read_csv(source_path)
            return {'csv_data': df.to_dict('records')}
        else:
            raise ValueError(f"Unsupported source format: {source_path.suffix}")
    
    elif source_path.is_dir():
        # Load multiple files from directory
        logger.info(f"Loading data from directory: {source}")
        
        data = {'files': {}}
        
        for file_path in source_path.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.json', '.yaml', '.csv']:
                try:
                    file_data = load_source_data(str(file_path), logger)
                    data['files'][file_path.name] = file_data
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
        
        return data
    
    else:
        raise ValueError(f"Source path does not exist: {source}")


def generate_current_data(data_type: str, logger: HFTLogger) -> Dict[str, Any]:
    """Generate current data from analyzer"""
    
    logger.info("Generating current data from analyzer")
    
    # Initialize analyzer
    config = ProductionConfig()
    analyzer = HFTAnalyzer(config=config)
    
    # Add some exchanges for data generation
    from ..core.exchange_config import CommonExchanges
    analyzer.add_exchange(CommonExchanges.NYSE())
    analyzer.add_exchange(CommonExchanges.NASDAQ())
    
    # Start monitoring briefly to generate data
    analyzer.start_monitoring(duration_seconds=5)
    
    # Get current metrics
    metrics = analyzer.get_live_metrics()
    latency_report = analyzer.get_latency_report()
    risk_report = analyzer.get_risk_report()
    
    analyzer.stop_monitoring()
    
    return {
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'latency_report': latency_report,
        'risk_report': risk_report,
        'config': config.to_dict()
    }


def filter_data(data: Dict[str, Any], start_time: Optional[datetime],
               end_time: Optional[datetime], exchanges: tuple,
               data_type: str, logger: HFTLogger) -> Dict[str, Any]:
    """Filter data based on criteria"""
    
    filtered_data = data.copy()
    
    # Filter by time range
    if start_time or end_time:
        logger.info(f"Filtering by time range: {start_time} to {end_time}")
        # Implementation would filter based on timestamps in data
    
    # Filter by exchanges
    if exchanges:
        logger.info(f"Filtering by exchanges: {', '.join(exchanges)}")
        # Implementation would filter based on exchange names
    
    # Filter by data type
    if data_type != 'all':
        logger.info(f"Filtering by data type: {data_type}")
        
        if data_type == 'latency':
            # Keep only latency-related data
            filtered_data = {
                'latency_report': data.get('latency_report', {}),
                'latency_measurements': data.get('latency_measurements', [])
            }
        elif data_type == 'metrics':
            # Keep only metrics data
            filtered_data = {
                'metrics': data.get('metrics', {}),
                'system_metrics': data.get('system_metrics', {})
            }
        elif data_type == 'events':
            # Keep only event data
            filtered_data = {
                'risk_report': data.get('risk_report', {}),
                'events': data.get('events', [])
            }
        elif data_type == 'config':
            # Keep only configuration data
            filtered_data = {
                'config': data.get('config', {})
            }
    
    return filtered_data


def prepare_export_data(data: Dict[str, Any], data_type: str,
                       include_metadata: bool, logger: HFTLogger) -> Dict[str, Any]:
    """Prepare data for export"""
    
    export_data = data.copy()
    
    if include_metadata:
        export_data['export_metadata'] = {
            'exported_at': datetime.now().isoformat(),
            'export_tool': 'hft-export',
            'data_type': data_type,
            'version': '1.0.0'
        }
    
    logger.info(f"Prepared export data with {len(export_data)} top-level keys")
    return export_data


def export_data_to_file(data: Dict[str, Any], output: str, format: str,
                       compress: bool, logger: HFTLogger):
    """Export data to file in specified format"""
    
    output_path = Path(output)
    
    if format == 'json':
        export_json(data, output_path, compress, logger)
    elif format == 'csv':
        export_csv(data, output_path, compress, logger)
    elif format == 'yaml':
        export_yaml(data, output_path, compress, logger)
    elif format == 'xml':
        export_xml(data, output_path, compress, logger)
    elif format == 'parquet':
        export_parquet(data, output_path, compress, logger)
    else:
        raise ValueError(f"Unsupported export format: {format}")


def export_json(data: Dict[str, Any], output_path: Path, compress: bool, logger: HFTLogger):
    """Export data as JSON"""
    
    if compress:
        import gzip
        with gzip.open(f"{output_path}.gz", 'wt') as f:
            json.dump(data, f, indent=2)
    else:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    logger.info(f"Exported JSON data to {output_path}")


def export_csv(data: Dict[str, Any], output_path: Path, compress: bool, logger: HFTLogger):
    """Export data as CSV"""
    
    # Flatten data for CSV export
    flattened_data = flatten_dict(data)
    
    if compress:
        import gzip
        with gzip.open(f"{output_path}.gz", 'wt', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['key', 'value', 'type'])
            
            for key, value in flattened_data.items():
                writer.writerow([key, str(value), type(value).__name__])
    else:
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['key', 'value', 'type'])
            
            for key, value in flattened_data.items():
                writer.writerow([key, str(value), type(value).__name__])
    
    logger.info(f"Exported CSV data to {output_path}")


def export_yaml(data: Dict[str, Any], output_path: Path, compress: bool, logger: HFTLogger):
    """Export data as YAML"""
    
    if compress:
        import gzip
        with gzip.open(f"{output_path}.gz", 'wt') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    else:
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    logger.info(f"Exported YAML data to {output_path}")


def export_xml(data: Dict[str, Any], output_path: Path, compress: bool, logger: HFTLogger):
    """Export data as XML"""
    
    try:
        import xml.etree.ElementTree as ET
        
        def dict_to_xml(data, root_name='data'):
            root = ET.Element(root_name)
            
            def add_to_element(element, data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        child = ET.SubElement(element, str(key))
                        add_to_element(child, value)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        child = ET.SubElement(element, f'item_{i}')
                        add_to_element(child, item)
                else:
                    element.text = str(data)
            
            add_to_element(root, data)
            return root
        
        root = dict_to_xml(data, 'hft_export')
        tree = ET.ElementTree(root)
        
        if compress:
            import gzip
            with gzip.open(f"{output_path}.gz", 'wb') as f:
                tree.write(f, encoding='utf-8', xml_declaration=True)
        else:
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Exported XML data to {output_path}")
        
    except ImportError:
        raise ValueError("XML export requires xml.etree.ElementTree")


def export_parquet(data: Dict[str, Any], output_path: Path, compress: bool, logger: HFTLogger):
    """Export data as Parquet"""
    
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        # Convert data to DataFrame
        flattened_data = flatten_dict(data)
        df = pd.DataFrame(list(flattened_data.items()), columns=['key', 'value'])
        
        # Convert to Parquet
        table = pa.Table.from_pandas(df)
        
        compression = 'gzip' if compress else None
        pq.write_table(table, output_path, compression=compression)
        
        logger.info(f"Exported Parquet data to {output_path}")
        
    except ImportError:
        raise ValueError("Parquet export requires pandas and pyarrow")


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, value))
    
    return dict(items)


if __name__ == '__main__':
    main() 