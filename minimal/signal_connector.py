"""Signal Connector: Link related signals to detect strategy cascades.

The Butterfly Effect:
When multiple signals connect, they reveal what decision-makers are ACTUALLY doing
before they announce it.

Example:
  Signal 1: Company X hires 50 quantum engineers
  Signal 2: Company X files patent in quantum error correction  
  Signal 3: Company X allocates $100M to quantum R&D
  
  Connection: Company X is building quantum computing capability
  Prediction: Competitors will follow market shift coming
  Timeline Advantage: 6-12 months before Layer 3 news
"""

import json
from typing import List, Dict, Set
from datetime import datetime, timedelta
import hashlib


class SignalConnector:
    """Detect and link related signals across sources and time."""
    
    def __init__(self):
        self.signal_history = {}
        self.connection_rules = self._build_connection_rules()
    
    def _build_connection_rules(self) -> Dict:
        return {
            "company_strategy": {
                "signals": [
                    ("hiring_for_skill", "patent_in_domain"),
                    ("hiring_for_skill", "job_posting_same_domain"),
                    ("executive_hire", "new_division_announcement"),
                ],
                "implication": "Company is pivoting toward new domain",
                "timeline_advantage": "6-12 months"
            },
            "market_shift": {
                "signals": [
                    ("multiple_companies_hiring_for_skill", "patent_surge_in_domain"),
                    ("fund_allocation_convergence", "executive_movement"),
                ],
                "implication": "Industry-wide shift forming",
                "timeline_advantage": "3-6 months"
            }
        }
    
    def store_signal(self, signal: Dict, ttl_hours: int = 168):
        signal_id = hashlib.sha256(
            f"{signal.get('title')}{signal.get('source')}".encode()
        ).hexdigest()[:16]
        
        signal["id"] = signal_id
        signal["timestamp"] = datetime.utcnow().isoformat()
        signal["ttl_expires"] = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()
        
        self.signal_history[signal_id] = signal
        return signal_id
    
    def detect_connections(self) -> List[Dict]:
        connections = []
        signals = list(self.signal_history.values())
        
        # Clean expired signals
        now = datetime.utcnow().isoformat()
        signals = [s for s in signals if s.get("ttl_expires", "") > now]
        
        # Connection Detection 1: Same Company
        company_signals = {}
        for signal in signals:
            company = signal.get("company", "Unknown")
            if company not in company_signals:
                company_signals[company] = []
            company_signals[company].append(signal)
        
        for company, signals_list in company_signals.items():
            if len(signals_list) >= 2:
                connection = self._analyze_company_signals(company, signals_list)
                if connection:
                    connections.append(connection)
        
        # Connection Detection 2: Same Domain, Multiple Companies
        domain_signals = {}
        for signal in signals:
            domains = signal.get("domain", [])
            for domain in domains:
                if domain not in domain_signals:
                    domain_signals[domain] = []
                domain_signals[domain].append(signal)
        
        for domain, signals_list in domain_signals.items():
            if len(set(s.get("company", "") for s in signals_list)) >= 3:
                connection = self._analyze_domain_convergence(domain, signals_list)
                if connection:
                    connections.append(connection)
        
        return connections
    
    def _analyze_company_signals(self, company: str, signals: List[Dict]) -> Dict:
        signal_types = set(s.get("signal_type", "") for s in signals)
        domains = set()
        for s in signals:
            domains.update(s.get("domain", []))
        
        if "hiring" in signal_types and "patent" in signal_types:
            return {
                "pattern": "company_pivoting",
                "company": company,
                "domains": list(domains),
                "implication": f"{company} is building capability in {', '.join(domains)}",
                "timeline_advantage": "6-12 months before announcement",
                "confidence": "High"
            }
        return None
    
    def _analyze_domain_convergence(self, domain: str, signals: List[Dict]) -> Dict:
        companies = list(set(s.get("company", "") for s in signals))
        return {
            "pattern": "market_shift_forming",
            "domain": domain,
            "companies_converging": companies,
            "implication": f"Industry-wide shift toward {domain}",
            "timeline_advantage": "3-6 months",
            "confidence": "Very High"
        }
