#!/usr/bin/env python3
"""
HFT Config - Configuration Management CLI Tool

Command-line interface for managing HFT-PacketFilter configurations,
validating settings, and generating configuration templates.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import click
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any

from ..core.production_config import ProductionConfig
from ..core.exchange_config import ExchangeConfig, CommonExchanges
from ..utils.logger import HFTLogger


@click.group()
def main():
    """
    HFT Config - Configuration Management for HFT-PacketFilter
    
    Manage configurations, validate settings, and generate templates
    for HFT-PacketFilter deployments.
    """
    pass


@main.command()
@click.option('--output', '-o', type=click.Path(), default='hft-config.yaml',
              help='Output configuration file')
@click.option('--performance-mode', '-p', 
              type=click.Choice(['standard', 'high_performance', 'ultra_low_latency']),
              default='standard', help='Performance mode')
@click.option('--include-exchanges', is_flag=True,
              help='Include common exchange configurations')
@click.option('--format', type=click.Choice(['yaml', 'json']),
              default='yaml', help='Output format')
def generate(output: str, performance_mode: str, include_exchanges: bool, format: str):
    """Generate a configuration template"""
    
    logger = HFTLogger("hft-config")
    
    try:
        # Create base configuration
        config = ProductionConfig(performance_mode=performance_mode)
        
        # Convert to dictionary
        config_dict = config.to_dict()
        
        # Add exchange configurations if requested
        if include_exchanges:
            config_dict['exchanges'] = {
                'NYSE': CommonExchanges.nyse().to_dict(),
                'NASDAQ': CommonExchanges.nasdaq().to_dict(),
                'CBOE': CommonExchanges.cboe().to_dict(),
            }
        
        # Save configuration
        output_path = Path(output)
        
        if format == 'yaml':
            with open(output_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        else:
            with open(output_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        
        click.echo(f"✅ Configuration template generated: {output_path}")
        logger.info(f"Generated configuration template: {output_path}")
        
    except Exception as e:
        click.echo(f"❌ Error generating configuration: {e}")
        logger.error(f"Error generating configuration: {e}")


@main.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Verbose validation output')
def validate(config_file: str, verbose: bool):
    """Validate a configuration file"""
    
    log_level = "DEBUG" if verbose else "INFO"
    logger = HFTLogger("hft-config", level=log_level)
    
    try:
        # Load configuration file
        with open(config_file, 'r') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)
        
        # Extract exchanges section if present
        exchanges = config_data.pop('exchanges', None)
        
        # Validate the core configuration
        config = ProductionConfig(**config_data)
        
        click.echo(f"✅ Configuration file is valid: {config_file}")
        
        if verbose:
            click.echo(f"\nConfiguration Summary:")
            click.echo(f"  Performance Mode: {config.performance_mode}")
            click.echo(f"  Log Level: {config.log_level}")
            click.echo(f"  Memory Pool: {config.memory_pool_size}")
            click.echo(f"  Metrics Enabled: {config.metrics_enabled}")
            click.echo(f"  SSL Enabled: {config.ssl_enabled}")
            click.echo(f"  Alerts Enabled: {config.alerts_enabled}")
            
            if exchanges:
                click.echo(f"  Exchanges: {', '.join(exchanges.keys())}")
        
        logger.info(f"Configuration validation successful: {config_file}")
        
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}")
        logger.error(f"Configuration validation failed: {e}")
        raise click.ClickException(str(e))


@main.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--key', '-k', required=True, help='Configuration key to get')
def get(config_file: str, key: str):
    """Get a specific configuration value"""
    
    logger = HFTLogger("hft-config")
    
    try:
        config = ProductionConfig.from_file(config_file)
        
        # Get value using dot notation (e.g., "alert_thresholds.latency_threshold_us")
        value = get_nested_value(config.to_dict(), key)
        
        if value is not None:
            click.echo(value)
        else:
            click.echo(f"❌ Key not found: {key}")
            
    except Exception as e:
        click.echo(f"❌ Error reading configuration: {e}")
        logger.error(f"Error reading configuration: {e}")


@main.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--key', '-k', required=True, help='Configuration key to set')
@click.option('--value', '-v', required=True, help='Value to set')
@click.option('--type', '-t', type=click.Choice(['str', 'int', 'float', 'bool']),
              default='str', help='Value type')
def set(config_file: str, key: str, value: str, type: str):
    """Set a specific configuration value"""
    
    logger = HFTLogger("hft-config")
    
    try:
        # Load configuration
        with open(config_file, 'r') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                config_dict = yaml.safe_load(f)
            else:
                config_dict = json.load(f)
        
        # Convert value to appropriate type
        if type == 'int':
            typed_value = int(value)
        elif type == 'float':
            typed_value = float(value)
        elif type == 'bool':
            typed_value = value.lower() in ('true', '1', 'yes', 'on')
        else:
            typed_value = value
        
        # Set value using dot notation
        set_nested_value(config_dict, key, typed_value)
        
        # Save configuration
        with open(config_file, 'w') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)
        
        click.echo(f"✅ Set {key} = {typed_value}")
        logger.info(f"Updated configuration: {key} = {typed_value}")
        
    except Exception as e:
        click.echo(f"❌ Error updating configuration: {e}")
        logger.error(f"Error updating configuration: {e}")


@main.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
def show(config_file: str, format: str):
    """Show configuration contents"""
    
    logger = HFTLogger("hft-config")
    
    try:
        config = ProductionConfig.from_file(config_file)
        config_dict = config.to_dict()
        
        if format == 'json':
            click.echo(json.dumps(config_dict, indent=2))
        elif format == 'yaml':
            click.echo(yaml.dump(config_dict, default_flow_style=False, indent=2))
        else:
            # Table format
            click.echo("=" * 60)
            click.echo("HFT-PacketFilter Configuration")
            click.echo("=" * 60)
            
            print_config_table(config_dict)
        
    except Exception as e:
        click.echo(f"❌ Error reading configuration: {e}")
        logger.error(f"Error reading configuration: {e}")


@main.command()
@click.argument('source_config', type=click.Path(exists=True))
@click.argument('target_config', type=click.Path(exists=True))
def diff(source_config: str, target_config: str):
    """Compare two configuration files"""
    
    logger = HFTLogger("hft-config")
    
    try:
        # Load both configurations
        config1 = ProductionConfig.from_file(source_config)
        config2 = ProductionConfig.from_file(target_config)
        
        dict1 = config1.to_dict()
        dict2 = config2.to_dict()
        
        # Find differences
        differences = find_differences(dict1, dict2)
        
        if not differences:
            click.echo("✅ Configurations are identical")
        else:
            click.echo(f"Found {len(differences)} differences:")
            click.echo("=" * 60)
            
            for key, (val1, val2) in differences.items():
                click.echo(f"Key: {key}")
                click.echo(f"  {Path(source_config).name}: {val1}")
                click.echo(f"  {Path(target_config).name}: {val2}")
                click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error comparing configurations: {e}")
        logger.error(f"Error comparing configurations: {e}")


def get_nested_value(data: dict, key: str):
    """Get nested value using dot notation"""
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    
    return value


def set_nested_value(data: dict, key: str, value):
    """Set nested value using dot notation"""
    keys = key.split('.')
    current = data
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value


def print_config_table(config_dict: dict, prefix: str = ""):
    """Print configuration in table format"""
    
    for key, value in config_dict.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            click.echo(f"\n[{full_key}]")
            print_config_table(value, full_key)
        else:
            click.echo(f"  {key:25} = {value}")


def find_differences(dict1: dict, dict2: dict, prefix: str = "") -> dict:
    """Find differences between two dictionaries"""
    
    differences = {}
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        full_key = f"{prefix}.{key}" if prefix else key
        
        if key not in dict1:
            differences[full_key] = (None, dict2[key])
        elif key not in dict2:
            differences[full_key] = (dict1[key], None)
        elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            # Recursively compare nested dictionaries
            nested_diffs = find_differences(dict1[key], dict2[key], full_key)
            differences.update(nested_diffs)
        elif dict1[key] != dict2[key]:
            differences[full_key] = (dict1[key], dict2[key])
    
    return differences


if __name__ == '__main__':
    main() 