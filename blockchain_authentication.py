@app.route('/blockchain/verify', methods=['GET'])
def verify_blockchain():
    """Verify blockchain integrity"""
    is_valid, message = auth_blockchain.verify_chain()
    return jsonify({
        'valid': is_valid,
        'message': message,
        'total_blocks': len(auth_blockchain.chain)
    })


@app.route('/blockchain/history/<username>', methods=['GET'])
def get_user_history(username):
    """Get authentication history for a user"""
    user_blocks = auth_blockchain.get_user_history(username)
    
    return jsonify({
        'username': username,
        'total_events': len(user_blocks),
        'history': user_blocks
    })


@app.route('/blockchain/stats', methods=['GET'])
def get_blockchain_stats():
    """Get blockchain statistics"""
    total_blocks = len(auth_blockchain.chain)
    
    # Count event types
    event_counts = {}
    for block in auth_blockchain.chain[1:]:
        if isinstance(block['data'], dict):
            event_type = block['data'].get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    return jsonify({
        'total_blocks': total_blocks,
        'event_distribution': event_counts,
        'last_block_time': auth_blockchain.chain[-1]['timestamp']
    })
