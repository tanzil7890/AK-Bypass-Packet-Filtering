# AK-Bypass and Packet Filtering

A comprehensive network packet filtering and analysis system designed for High-Frequency Trading (HFT) enviroment specifically for research purposes.

## ⚠️ Important Notice

**This project is for educational and research purposes only.** Use only on networks you own or have explicit permission to test. Always comply with local laws and regulations.

## 🚀 Features

### Core Functionality
- **Real-time Packet Capture**: Monitor network traffic on specified interfaces
- **Advanced Packet Filtering**: Rule-based filtering with multiple actions (ALLOW, BLOCK, LOG, MODIFY)
- **Multi-layer Packet Parsing**: Extract information from L2-L7 network layers
- **Suspicious Pattern Detection**: Identify potential security threats and anomalies
- **Statistics and Reporting**: Comprehensive traffic analysis and reporting
- **Export Capabilities**: Save captured data in multiple formats

### Supported Protocols
- **Layer 2**: Ethernet, ARP
- **Layer 3**: IPv4, IPv6, ICMP
- **Layer 4**: TCP, UDP
- **Layer 7**: HTTP, HTTPS, DNS, SSH, FTP, and more

### Security Analysis
- Port scan detection
- TCP flag analysis (SYN floods, NULL scans, XMAS scans)
- Fragmented packet detection
- Encrypted traffic identification
- Unusual port usage monitoring

## 📋 Requirements

### System Requirements
- **Operating System**: macOS, Linux (Windows support planned)
- **Python**: 3.8 or higher
- **Privileges**: Root/sudo access for packet capture
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB for installation

### Dependencies
- Python 3.8+
- Scapy (packet manipulation)
- psutil (system monitoring)
- netifaces (network interface detection)
- Additional packages listed in `requirements.txt`

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AK-Bypass_and_packet_filtering
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python3 demo.py
```

## 🎯 Quick Start

### Basic Demo
Run the demonstration script to see the system in action:
```bash
python3 demo.py
```

### Live Packet Capture
**Note**: Requires sudo privileges
```bash
sudo python3 demo.py --capture
```

### Export Results
```bash
python3 demo.py --export my_analysis
```

## 📖 Usage Examples

### Basic Packet Filtering
```python
from src.core.packet_filter import PacketFilter, FilterRule, FilterAction

# Initialize packet filter
pf = PacketFilter()

# Add filtering rules
pf.add_rule(FilterRule(
    name="Block SSH",
    protocol="tcp",
    dst_port=22,
    action=FilterAction.BLOCK
))

pf.add_rule(FilterRule(
    name="Log HTTP",
    protocol="tcp",
    dst_port=80,
    action=FilterAction.LOG
))

# Start capture
pf.start_capture(count=100, timeout=30)
```

### Packet Analysis
```python
from src.core.packet_parser import PacketParser

# Initialize parser
parser = PacketParser()

# Parse a packet (from capture or file)
parsed = parser.parse_packet(packet)

# Access parsed information
print(f"Source: {parsed.ip_src}:{parsed.src_port}")
print(f"Destination: {parsed.ip_dst}:{parsed.dst_port}")
print(f"Protocol: {parsed.ip_protocol}")
print(f"Suspicious flags: {parsed.suspicious_flags}")
```

### Generate Reports
```python
# Get statistics
stats = pf.get_statistics()
print(f"Total packets: {stats['capture_stats']['total_packets']}")

# Generate detailed report
report = parser.generate_summary_report()
print(json.dumps(report, indent=2))
```

## 📁 Project Structure

```
AK-Bypass_and_packet_filtering/
├── src/
│   ├── core/
│   │   ├── packet_filter.py      # Core filtering engine
│   │   ├── packet_parser.py      # Packet analysis module
│   │   └── bypass_engine.py      # Bypass techniques (planned)
│   ├── utils/                    # Utility modules (planned)
│   ├── tests/                    # Test suite (planned)
│   └── tools/                    # Additional tools (planned)
├── config/                       # Configuration files
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── venv/                         # Virtual environment
├── demo.py                       # Demonstration script
├── requirements.txt              # Python dependencies
├── Development_guide.md          # Development roadmap
├── Track.md                      # Progress tracking
├── Debug.md                      # Debug information
└── README.md                     # This file
```

## 🔧 Configuration

### Filter Rules
Create custom filtering rules with the following parameters:
- **name**: Unique identifier
- **protocol**: tcp, udp, icmp, or None (any)
- **src_ip/dst_ip**: Source/destination IP addresses
- **src_port/dst_port**: Source/destination ports
- **action**: ALLOW, BLOCK, LOG, or MODIFY
- **priority**: Rule priority (lower = higher priority)

### Network Interfaces
The system auto-detects available network interfaces. You can specify a particular interface:
```python
pf = PacketFilter(interface="en0")  # macOS WiFi
pf = PacketFilter(interface="eth0") # Linux Ethernet
```

## 📊 Analysis Features

### Traffic Statistics
- Packet counts by protocol
- Top source/destination IPs
- Port usage analysis
- Bandwidth utilization

### Security Analysis
- **Port Scanning**: Detect systematic port probes
- **TCP Attacks**: Identify SYN floods, NULL scans, XMAS scans
- **Fragmentation**: Monitor packet fragmentation patterns
- **Encryption**: Identify encrypted vs. plaintext traffic

### Export Formats
- **PCAP**: Standard packet capture format
- **JSON**: Structured data for analysis
- **CSV**: Spreadsheet-compatible format (planned)

## 🧪 Testing

### Run Demo Tests
```bash
python3 demo.py
```

### Unit Tests (Planned)
```bash
python3 -m pytest src/tests/
```

### Performance Tests (Planned)
```bash
python3 scripts/performance_test.py
```

## 🚧 Development Status

### ✅ Completed (Phase 1 & 2)
- [x] Project setup and environment
- [x] Core packet filtering engine
- [x] Multi-layer packet parser
- [x] Rule-based filtering system
- [x] Statistics and reporting
- [x] Suspicious pattern detection
- [x] Demo and testing framework

### 🔄 In Progress (Phase 3)
- [ ] Bypass techniques implementation
- [ ] Advanced evasion methods
- [ ] Protocol tunneling
- [ ] Packet fragmentation tools

### 📋 Planned (Phase 4-6)
- [ ] Web-based dashboard
- [ ] Real-time visualization
- [ ] Machine learning integration
- [ ] Advanced reporting tools
- [ ] Performance optimization
- [ ] Comprehensive test suite

## 🤝 Contributing

This is an educational project. Contributions are welcome for:
- Bug fixes and improvements
- Additional protocol support
- New analysis features
- Documentation enhancements
- Test coverage

Please ensure all contributions maintain the educational focus and include appropriate disclaimers.

## 📚 Documentation

- **[Development Guide](Development_guide.md)**: Comprehensive development roadmap
- **[Progress Tracking](Track.md)**: Current status and completed tasks
- **[Debug Information](Debug.md)**: Troubleshooting and known issues
- **API Documentation**: Coming soon

## ⚖️ Legal and Ethical Considerations

### Educational Use Only
This software is designed for:
- Learning network security concepts
- Understanding packet filtering techniques
- Research in controlled environments
- Educational demonstrations

### Prohibited Uses
- Unauthorized network monitoring
- Malicious traffic interception
- Attacks on systems you don't own
- Any illegal activities

### Responsible Disclosure
If you discover security vulnerabilities:
1. Do not exploit them maliciously
2. Report them responsibly
3. Allow time for fixes before disclosure
4. Follow coordinated disclosure practices

## 🆘 Support and Troubleshooting

### Common Issues
1. **Permission Denied**: Use sudo for packet capture
2. **Interface Not Found**: Check available interfaces with `ifconfig -a`
3. **Package Import Errors**: Ensure virtual environment is activated
4. **Performance Issues**: Consider filtering at capture level for high traffic

### Getting Help
- Check the [Debug.md](Debug.md) file for troubleshooting
- Review the [Development_guide.md](Development_guide.md) for setup instructions
- Ensure you're using a supported Python version (3.8+)

## 📄 License

This project is released under an educational license. See LICENSE file for details.

**Remember**: Always use this software responsibly and in compliance with applicable laws and regulations.

---

**Disclaimer**: The authors are not responsible for any misuse of this software. Users are solely responsible for ensuring their use complies with all applicable laws and regulations. 