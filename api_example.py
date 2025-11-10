#!/usr/bin/env python3
"""
Example API Integration Script
Demonstrates how to use the JSON output from SimpleOCR in an API context
"""
import json
import os
from flask import Flask, jsonify, request
from spreadsheet_writer import DataWriter
import config

app = Flask(__name__)

# Load receipts data from JSON file
def load_receipts():
    """Load receipts from JSON file"""
    if os.path.exists(config.JSON_OUTPUT_FILE):
        with open(config.JSON_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    return {'metadata': {}, 'receipts': []}

@app.route('/api/receipts', methods=['GET'])
def get_receipts():
    """Get all receipts"""
    data = load_receipts()
    
    # Query parameters for filtering
    vendor = request.args.get('vendor')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    min_total = request.args.get('min_total', type=float)
    max_total = request.args.get('max_total', type=float)
    
    receipts = data.get('receipts', [])
    
    # Filter receipts
    filtered_receipts = receipts
    if vendor:
        filtered_receipts = [r for r in filtered_receipts if vendor.lower() in r.get('vendor', '').lower()]
    if date_from:
        filtered_receipts = [r for r in filtered_receipts if r.get('date', '') >= date_from]
    if date_to:
        filtered_receipts = [r for r in filtered_receipts if r.get('date', '') <= date_to]
    if min_total:
        filtered_receipts = [r for r in filtered_receipts if r.get('total') and r.get('total') >= min_total]
    if max_total:
        filtered_receipts = [r for r in filtered_receipts if r.get('total') and r.get('total') <= max_total]
    
    return jsonify({
        'metadata': data.get('metadata', {}),
        'receipts': filtered_receipts,
        'count': len(filtered_receipts)
    })

@app.route('/api/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get a specific receipt by index"""
    data = load_receipts()
    receipts = data.get('receipts', [])
    
    if 0 <= receipt_id < len(receipts):
        return jsonify(receipts[receipt_id])
    else:
        return jsonify({'error': 'Receipt not found'}), 404

@app.route('/api/receipts/stats', methods=['GET'])
def get_stats():
    """Get statistics about receipts"""
    data = load_receipts()
    receipts = data.get('receipts', [])
    
    if not receipts:
        return jsonify({
            'total_receipts': 0,
            'total_amount': 0,
            'average_amount': 0,
            'vendors': []
        })
    
    total_amount = sum(r.get('total', 0) or 0 for r in receipts)
    average_amount = total_amount / len(receipts) if receipts else 0
    
    # Get unique vendors
    vendors = list(set(r.get('vendor', 'Unknown') for r in receipts if r.get('vendor')))
    
    return jsonify({
        'total_receipts': len(receipts),
        'total_amount': round(total_amount, 2),
        'average_amount': round(average_amount, 2),
        'vendors': sorted(vendors),
        'date_range': {
            'earliest': min(r.get('date', '') for r in receipts if r.get('date')),
            'latest': max(r.get('date', '') for r in receipts if r.get('date'))
        }
    })

@app.route('/api/receipts/vendors', methods=['GET'])
def get_vendors():
    """Get list of all vendors"""
    data = load_receipts()
    receipts = data.get('receipts', [])
    
    vendors = {}
    for receipt in receipts:
        vendor = receipt.get('vendor', 'Unknown')
        if vendor not in vendors:
            vendors[vendor] = {
                'name': vendor,
                'count': 0,
                'total_amount': 0
            }
        vendors[vendor]['count'] += 1
        vendors[vendor]['total_amount'] += receipt.get('total', 0) or 0
    
    return jsonify({
        'vendors': list(vendors.values())
    })

if __name__ == '__main__':
    print("Starting SimpleOCR API Server...")
    print(f"Receipts file: {config.JSON_OUTPUT_FILE}")
    print("API endpoints:")
    print("  GET /api/receipts - Get all receipts (supports query parameters: vendor, date_from, date_to, min_total, max_total)")
    print("  GET /api/receipts/<id> - Get specific receipt by index")
    print("  GET /api/receipts/stats - Get statistics")
    print("  GET /api/receipts/vendors - Get vendor list")
    print("\nExample: http://localhost:5000/api/receipts?vendor=Amazon&min_total=50")
    app.run(debug=True, host='0.0.0.0', port=5000)

