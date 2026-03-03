# Test file for AI-TD Detector Extension
# This file contains various patterns that should trigger AI-TD detection

import os
import sys
import json
from typing import List, Dict, Optional

def complex_function(data: List[Dict], threshold: float = 0.5, 
                    mode: str = "auto", debug: bool = False, 
                    output_format: str = "json", validate: bool = True,
                    max_iterations: int = 1000, tolerance: float = 0.001):
    """This function is intentionally complex to trigger complexity detection."""
    if not data:
        return None
    
    result = []
    for i, item in enumerate(data):
        if i > max_iterations:
            break
            
        # Complex nested logic
        if item.get('type') == 'A':
            if item.get('value') > threshold:
                if mode == "auto":
                    processed = process_type_a(item, debug)
                elif mode == "manual":
                    processed = manual_process(item, output_format)
                else:
                    processed = default_process(item)
                result.append(processed)
        elif item.get('type') == 'B':
            if item.get('status') == 'active':
                if validate:
                    if validate_item(item):
                        result.append(process_type_b(item, debug))
                else:
                    result.append(process_type_b(item, debug))
        elif item.get('type') == 'C':
            # Similar logic repeated (duplication)
            if item.get('priority') > 5:
                if mode == "auto":
                    processed = process_type_c(item, debug)
                elif mode == "manual":
                    processed = manual_process_c(item, output_format)
                else:
                    processed = default_process_c(item)
                result.append(processed)
    
    return result

def process_type_a(item: Dict, debug: bool) -> Dict:
    """Process type A items."""
    # No error handling - should trigger error handling detection
    value = item['value'] * 2
    metadata = item['metadata']
    
    # Complex calculation
    if value > 100:
        result = {
            'original': value,
            'processed': value / 2,
            'metadata': metadata,
            'timestamp': os.path.getmtime(__file__)
        }
    else:
        result = {
            'original': value,
            'processed': value * 1.5,
            'metadata': metadata,
            'timestamp': os.path.getmtime(__file__)
        }
    
    return result

def process_type_b(item: Dict, debug: bool) -> Dict:
    """Process type B items - similar to type A (duplication)."""
    # No error handling - should trigger error handling detection
    value = item['value'] * 2
    metadata = item['metadata']
    
    # Similar complex calculation (duplication)
    if value > 100:
        result = {
            'original': value,
            'processed': value / 2,
            'metadata': metadata,
            'timestamp': os.path.getmtime(__file__)
        }
    else:
        result = {
            'original': value,
            'processed': value * 1.5,
            'metadata': metadata,
            'timestamp': os.path.getmtime(__file__)
        }
    
    return result

def process_type_c(item: Dict, debug: bool) -> Dict:
    """Process type C items - another duplicated function."""
    # No error handling - should trigger error handling detection
    value = item['value'] * 2
    metadata = item['metadata']
    
    # Again similar logic (duplication)
    if value > 100:
        result = {
            'original': value,
            'processed': value / 2,
            'metadata': metadata,
            'timestamp': os.path.getmtime(__file__)
        }
    else:
        result = {
            'original': value,
            'processed': value * 1.5,
            'metadata': metadata,
            'timestamp': os.path.getmtime(__file__)
        }
    
    return result

def manual_process(item: Dict, output_format: str) -> Dict:
    """Manual processing without documentation."""
    # Missing docstring details - should trigger documentation detection
    return item

def manual_process_c(item: Dict, output_format: str) -> Dict:
    """Manual processing for type C without documentation."""
    # Missing docstring details - should trigger documentation detection
    return item

def default_process(item: Dict) -> Dict:
    """Default processing."""
    return item

def default_process_c(item: Dict) -> Dict:
    """Default processing for type C."""
    return item

def validate_item(item: Dict) -> bool:
    """Validate item without error handling."""
    # No error handling for missing keys
    return item['valid'] and item['active']

# Missing documentation for this function
def undocumented_function(x, y):
    return x + y

# Main execution without error handling
if __name__ == "__main__":
    # Test data that should trigger various detections
    test_data = [
        {'type': 'A', 'value': 150, 'metadata': {'source': 'test'}, 'priority': 8},
        {'type': 'B', 'value': 75, 'metadata': {'source': 'test'}, 'status': 'active'},
        {'type': 'C', 'value': 200, 'metadata': {'source': 'test'}, 'priority': 10}
    ]
    
    # No error handling for the main processing
    results = complex_function(test_data)
    print(f"Processed {len(results)} items")
