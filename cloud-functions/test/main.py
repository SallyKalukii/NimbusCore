import functions_framework

@functions_framework.http
def ingest_no_storage(request):
    """
    Test endpoint - validates but doesn't store
    Measures max ingestion throughput without storage bottleneck
    """
    try:
        log_data = request.get_json()
        
        # Validate (same as real ingestion)
        if not log_data or 'level' not in log_data:
            return {'error': 'Invalid format'}, 400
        
        # Return success immediately (no Pub/Sub, no Firestore)
        return {
            'status': 'accepted',
            'message': 'Test mode - validation only'
        }, 202
        
    except Exception as e:
        return {'error': str(e)}, 500