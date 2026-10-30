"""Explicit CICIoT2023 attack taxonomy and filename conventions."""
from __future__ import annotations

import re
from pathlib import Path

ATTACK_GROUPS = {
    'BenignTraffic': 'Benign',
    'Backdoor_Malware': 'Web-based', 'BrowserHijacking': 'Web-based',
    'CommandInjection': 'Web-based', 'SqlInjection': 'Web-based',
    'Uploading_Attack': 'Web-based', 'XSS': 'Web-based',
    'DictionaryBruteForce': 'BruteForce',
    'DNS_Spoofing': 'Spoofing', 'MITM-ArpSpoofing': 'Spoofing',
    'Recon-HostDiscovery': 'Recon', 'Recon-OSScan': 'Recon',
    'Recon-PingSweep': 'Recon', 'Recon-PortScan': 'Recon',
    'VulnerabilityScan': 'Recon',
    'Mirai-greeth_flood': 'Mirai', 'Mirai-greip_flood': 'Mirai',
    'Mirai-udpplain': 'Mirai',
    **{f'DDoS-{name}': 'DDoS' for name in [
        'ACK_Fragmentation', 'HTTP_Flood', 'ICMP_Flood', 'ICMP_Fragmentation',
        'PSHACK_Flood', 'RSTFINFlood', 'SlowLoris', 'SynonymousIP_Flood',
        'SYN_Flood', 'TCP_Flood', 'UDP_Flood', 'UDP_Fragmentation',
    ]},
    **{f'DoS-{name}': 'DoS' for name in ['HTTP_Flood', 'SYN_Flood', 'TCP_Flood', 'UDP_Flood']},
}
def filename_label(path: Path) -> str:
    if not path.name.endswith('.pcap.csv'):
        raise ValueError(f'Unrecognized unlabeled filename: {path.name}')
    name = re.sub(r'\d+$', '', path.name.removesuffix('.pcap.csv')).rstrip('-')
    if name not in ATTACK_GROUPS:
        raise ValueError(f'Unknown attack label in filename: {path.name}')
    return name
