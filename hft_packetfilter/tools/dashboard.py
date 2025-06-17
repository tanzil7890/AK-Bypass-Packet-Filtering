#!/usr/bin/env python3
"""
HFT Dashboard - Web-based Monitoring Dashboard

Command-line interface for launching a web-based dashboard for
real-time HFT monitoring and visualization.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import click
import threading
import time
from typing import Optional

try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from ..core.hft_analyzer import HFTAnalyzer
from ..core.exchange_config import CommonExchanges
from ..core.production_config import ProductionConfig
from ..utils.logger import HFTLogger


@click.command()
@click.option('--host', '-h', default='localhost',
              help='Host to bind the dashboard to')
@click.option('--port', '-p', type=int, default=8080,
              help='Port to bind the dashboard to')
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Configuration file path')
@click.option('--performance-mode', 
              type=click.Choice(['standard', 'high_performance', 'ultra_low_latency']),
              default='standard', help='Performance mode')
@click.option('--debug', is_flag=True,
              help='Enable debug mode')
@click.option('--auto-refresh', type=int, default=1,
              help='Auto-refresh interval in seconds')
def main(host: str, port: int, config: Optional[str], 
         performance_mode: str, debug: bool, auto_refresh: int):
    """
    HFT Dashboard - Web-based Real-time Monitoring Dashboard
    
    Launch a web-based dashboard for real-time monitoring of HFT network
    performance, latency metrics, and trading infrastructure health.
    
    Examples:
        hft-dashboard --port 8080
        hft-dashboard --host 0.0.0.0 --port 3000 --debug
        hft-dashboard --config production.yaml --performance-mode ultra_low_latency
    """
    
    if not FLASK_AVAILABLE:
        click.echo("❌ Flask is required for the dashboard. Install with: pip install flask flask-cors")
        raise click.ClickException("Flask not available")
    
    logger = HFTLogger("hft-dashboard")
    
    try:
        # Initialize HFT analyzer
        if config:
            prod_config = ProductionConfig.from_file(config)
        else:
            prod_config = ProductionConfig(performance_mode=performance_mode)
        
        analyzer = HFTAnalyzer(
            config=prod_config,
            performance_mode=performance_mode
        )
        
        # Add default exchanges
        analyzer.add_exchange(CommonExchanges.NYSE())
        analyzer.add_exchange(CommonExchanges.NASDAQ())
        analyzer.add_exchange(CommonExchanges.CBOE())
        
        # Start monitoring
        analyzer.start_monitoring()
        
        # Create Flask app
        app = create_dashboard_app(analyzer, auto_refresh, logger)
        
        click.echo("=" * 60)
        click.echo("HFT Dashboard Starting")
        click.echo("=" * 60)
        click.echo(f"🌐 Dashboard URL: http://{host}:{port}")
        click.echo(f"📊 Performance Mode: {performance_mode}")
        click.echo(f"🔄 Auto-refresh: {auto_refresh}s")
        click.echo("=" * 60)
        click.echo("Press Ctrl+C to stop the dashboard")
        
        # Run Flask app
        app.run(host=host, port=port, debug=debug, threaded=True)
        
    except KeyboardInterrupt:
        click.echo("\n🛑 Dashboard stopped by user")
    except Exception as e:
        click.echo(f"❌ Dashboard failed: {e}")
        logger.error(f"Dashboard failed: {e}")
        raise click.ClickException(str(e))
    finally:
        if 'analyzer' in locals():
            analyzer.stop_monitoring()


def create_dashboard_app(analyzer: HFTAnalyzer, auto_refresh: int, logger: HFTLogger) -> Flask:
    """Create Flask dashboard application"""
    
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    CORS(app)
    
    @app.route('/')
    def dashboard():
        """Main dashboard page"""
        return render_template('dashboard.html', auto_refresh=auto_refresh)
    
    @app.route('/api/metrics')
    def api_metrics():
        """API endpoint for live metrics"""
        try:
            metrics = analyzer.get_live_metrics()
            return jsonify({
                'success': True,
                'data': metrics,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/latency')
    def api_latency():
        """API endpoint for latency report"""
        try:
            latency_report = analyzer.get_latency_report()
            return jsonify({
                'success': True,
                'data': latency_report,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error getting latency report: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/risk')
    def api_risk():
        """API endpoint for risk report"""
        try:
            risk_report = analyzer.get_risk_report()
            return jsonify({
                'success': True,
                'data': risk_report,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error getting risk report: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/exchanges')
    def api_exchanges():
        """API endpoint for exchange information"""
        try:
            exchanges = {}
            for name, config in analyzer.exchanges.items():
                exchanges[name] = {
                    'name': config.name,
                    'host': config.host,
                    'ports': config.ports,
                    'protocol': config.protocol,
                    'latency_target_us': config.latency_target_us,
                    'is_primary': config.is_primary
                }
            
            return jsonify({
                'success': True,
                'data': exchanges,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error getting exchanges: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/config')
    def api_config():
        """API endpoint for configuration"""
        try:
            config_data = {
                'performance_mode': analyzer.performance_mode,
                'is_monitoring': analyzer.is_monitoring,
                'exchange_count': len(analyzer.exchanges),
                'uptime_seconds': time.time() - analyzer.start_time
            }
            
            return jsonify({
                'success': True,
                'data': config_data,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/export', methods=['POST'])
    def api_export():
        """API endpoint for exporting data"""
        try:
            export_format = request.json.get('format', 'json')
            filename = f"hft_export_{int(time.time())}.{export_format}"
            
            analyzer.export_analysis(filename, format=export_format)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'message': f'Data exported to {filename}'
            })
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app


# Create basic HTML template if templates don't exist
def create_basic_template():
    """Create a basic HTML template for the dashboard"""
    
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HFT Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        .refresh-info {
            text-align: center;
            color: #666;
            margin-top: 20px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 HFT Dashboard</h1>
        <p>Real-time High-Frequency Trading Network Monitoring</p>
    </div>
    
    <div id="dashboard-content">
        <div class="loading">
            <h3>Loading dashboard...</h3>
            <p>Fetching real-time metrics...</p>
        </div>
    </div>
    
    <div class="refresh-info">
        <p>Auto-refreshing every {{ auto_refresh }} seconds</p>
        <p id="last-update">Last updated: Never</p>
    </div>

    <script>
        let autoRefreshInterval = {{ auto_refresh }} * 1000;
        
        function updateDashboard() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        renderDashboard(data.data);
                        document.getElementById('last-update').textContent = 
                            'Last updated: ' + new Date().toLocaleTimeString();
                    } else {
                        showError('Failed to fetch metrics: ' + data.error);
                    }
                })
                .catch(error => {
                    showError('Network error: ' + error.message);
                });
        }
        
        function renderDashboard(metrics) {
            const content = document.getElementById('dashboard-content');
            
            let html = '<div class="metrics-grid">';
            
            // System Status
            html += `
                <div class="metric-card">
                    <div class="metric-title">📊 System Status</div>
                    <div class="metric-value ${metrics.is_monitoring ? 'status-good' : 'status-error'}">
                        ${metrics.is_monitoring ? '✅ Active' : '❌ Stopped'}
                    </div>
                    <p>Uptime: ${Math.round(metrics.uptime_seconds)}s</p>
                    <p>Mode: ${metrics.performance_mode}</p>
                </div>
            `;
            
            // Trading Metrics
            if (metrics.trading_metrics) {
                html += `
                    <div class="metric-card">
                        <div class="metric-title">📈 Trading Metrics</div>
                        <div class="metric-value">${metrics.trading_metrics.total_packets.toLocaleString()}</div>
                        <p>Total Packets</p>
                        <p>Latency: ${metrics.trading_metrics.latency_us.toFixed(1)}μs</p>
                    </div>
                `;
            }
            
            // Exchange Status
            if (metrics.exchanges) {
                for (const [name, exchange] of Object.entries(metrics.exchanges)) {
                    const quality = metrics.market_data_quality[name] || {};
                    const statusClass = exchange.status === 'connected' ? 'status-good' : 'status-error';
                    
                    html += `
                        <div class="metric-card">
                            <div class="metric-title">🏛️ ${name}</div>
                            <div class="metric-value ${statusClass}">
                                ${exchange.status === 'connected' ? '🟢 Connected' : '🔴 Disconnected'}
                            </div>
                            <p>Latency: ${(quality.latency_us || 0).toFixed(1)}μs</p>
                            <p>Quality: ${(quality.quality_score || 0).toFixed(1)}%</p>
                            <p>Target: ${exchange.latency_target_us}μs</p>
                        </div>
                    `;
                }
            }
            
            // Latency Statistics
            if (metrics.latency_stats && metrics.latency_stats.count > 0) {
                html += `
                    <div class="metric-card">
                        <div class="metric-title">⚡ Latency Stats (60s)</div>
                        <div class="metric-value">${metrics.latency_stats.avg.toFixed(1)}μs</div>
                        <p>Average Latency</p>
                        <p>Min: ${metrics.latency_stats.min.toFixed(1)}μs</p>
                        <p>Max: ${metrics.latency_stats.max.toFixed(1)}μs</p>
                        <p>Count: ${metrics.latency_stats.count.toLocaleString()}</p>
                    </div>
                `;
            }
            
            html += '</div>';
            content.innerHTML = html;
        }
        
        function showError(message) {
            const content = document.getElementById('dashboard-content');
            content.innerHTML = `
                <div class="metric-card" style="text-align: center; color: #dc3545;">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
        
        // Initial load
        updateDashboard();
        
        // Set up auto-refresh
        setInterval(updateDashboard, autoRefreshInterval);
    </script>
</body>
</html>
    """


if __name__ == '__main__':
    main() 