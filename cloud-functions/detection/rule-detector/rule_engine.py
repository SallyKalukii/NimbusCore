"""
Rule-Based Anomaly Detection Engine
Detects known attack patterns using explicit rules
"""

# Thresholds (from training baseline)
LATENCY_BRUTE_THRESHOLD = 699.865006594
LATENCY_DDOS_THRESHOLD = 1076.71539476
MSG_LEN_SQLI_THRESHOLD = 61.10605199999999
LATENCY_FRAUD_THRESHOLD = 646.029236856

ODD_HOURS_BRUTE = {2, 3, 4, 22, 23}
ODD_HOURS_UNUSUAL = {1, 2, 3, 4, 5}
ODD_HOURS_FRAUD = {0, 1, 2, 3, 22, 23}

def check_brute_force(log):
    """Rule 1: Brute Force Detection"""
    score = 0
    if log['level_encoded'] == 2:        score += 0.4
    if log['hour'] in ODD_HOURS_BRUTE:   score += 0.3
    if log['processing_latency_ms'] > LATENCY_BRUTE_THRESHOLD:  score += 0.3

    if score >= 0.7:
        return {'rule': 'brute_force', 'confidence': score, 'severity': 'HIGH' if score >= 0.9 else 'MEDIUM'}
    return None

def check_ddos(log):
    """Rule 2: DDoS Detection (Improved)"""
    score = 0
    if log['level_encoded'] == 1:        score += 0.5
    if log['processing_latency_ms'] > LATENCY_DDOS_THRESHOLD:  score += 0.3
    if log['has_user_agent'] == 1:       score += 0.2

    if score >= 0.7:
        return {'rule': 'ddos', 'confidence': score, 'severity': 'HIGH' if score >= 0.9 else 'MEDIUM'}
    return None

def check_sql_injection(log):
    """Rule 3: SQL Injection Detection"""
    score = 0
    if log['level_encoded'] == 2:        score += 0.3
    if log['has_user_agent'] == 0:       score += 0.4
    if log['message_length'] > MSG_LEN_SQLI_THRESHOLD:  score += 0.3

    if score >= 0.7:
        return {'rule': 'sql_injection', 'confidence': score, 'severity': 'HIGH' if score >= 0.9 else 'MEDIUM'}
    return None

def check_unusual_traffic(log):
    """Rule 4: Unusual Traffic Detection"""
    score = 0
    if log['hour'] in ODD_HOURS_UNUSUAL:  score += 0.4
    if log['has_geo'] == 0:               score += 0.3
    if log['has_user_agent'] == 0:        score += 0.3

    if score >= 0.7:
        return {'rule': 'unusual_traffic', 'confidence': score, 'severity': 'MEDIUM'}
    return None

def check_payment_fraud(log):
    """Rule 5: Payment Fraud Detection"""
    score = 0
    if log['level_encoded'] == 2:        score += 0.3
    if log['hour'] in ODD_HOURS_FRAUD:   score += 0.3
    if log['processing_latency_ms'] > LATENCY_FRAUD_THRESHOLD:  score += 0.2
    if log['has_geo'] == 1:              score += 0.2

    if score >= 0.7:
        return {'rule': 'payment_fraud', 'confidence': score, 'severity': 'HIGH' if score >= 0.8 else 'MEDIUM'}
    return None

def detect_anomalies(log):
    """
    Run all rules on a single log entry
    Returns first matching rule or None
    """
    all_rules = [
        check_brute_force,
        check_ddos,
        check_sql_injection,
        check_unusual_traffic,
        check_payment_fraud
    ]

    for rule_fn in all_rules:
        result = rule_fn(log)
        if result:
            return result

    return None
