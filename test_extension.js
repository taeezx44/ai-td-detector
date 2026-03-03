// Test JavaScript file for AI-TD Detector Extension
// Contains patterns that should trigger AI-TD detection

const fs = require('fs');
const path = require('path');

// Complex function with high cyclomatic complexity
function complexDataProcessor(data, options = {}) {
    const {
        threshold = 0.5,
        mode = 'auto',
        debug = false,
        outputFormat = 'json',
        validate = true,
        maxIterations = 1000,
        tolerance = 0.001
    } = options;

    if (!data || data.length === 0) {
        return null;
    }

    const results = [];
    
    for (let i = 0; i < data.length; i++) {
        if (i > maxIterations) break;
        
        const item = data[i];
        
        // Complex nested conditional logic
        if (item.type === 'A') {
            if (item.value > threshold) {
                if (mode === 'auto') {
                    const processed = processTypeA(item, debug);
                    results.push(processed);
                } else if (mode === 'manual') {
                    const processed = manualProcess(item, outputFormat);
                    results.push(processed);
                } else {
                    const processed = defaultProcess(item);
                    results.push(processed);
                }
            }
        } else if (item.type === 'B') {
            if (item.status === 'active') {
                if (validate) {
                    if (validateItem(item)) {
                        const processed = processTypeB(item, debug);
                        results.push(processed);
                    }
                } else {
                    const processed = processTypeB(item, debug);
                    results.push(processed);
                }
            }
        } else if (item.type === 'C') {
            // Duplicated logic pattern
            if (item.priority > 5) {
                if (mode === 'auto') {
                    const processed = processTypeC(item, debug);
                    results.push(processed);
                } else if (mode === 'manual') {
                    const processed = manualProcessC(item, outputFormat);
                    results.push(processed);
                } else {
                    const processed = defaultProcessC(item);
                    results.push(processed);
                }
            }
        }
    }
    
    return results;
}

// Function without proper error handling
function processTypeA(item, debug) {
    // No error handling for missing properties
    const value = item.value * 2;
    const metadata = item.metadata;
    
    // Complex calculation
    if (value > 100) {
        return {
            original: value,
            processed: value / 2,
            metadata: metadata,
            timestamp: fs.statSync(__filename).mtime
        };
    } else {
        return {
            original: value,
            processed: value * 1.5,
            metadata: metadata,
            timestamp: fs.statSync(__filename).mtime
        };
    }
}

// Duplicated function - should trigger duplication detection
function processTypeB(item, debug) {
    // No error handling for missing properties
    const value = item.value * 2;
    const metadata = item.metadata;
    
    // Duplicated logic from processTypeA
    if (value > 100) {
        return {
            original: value,
            processed: value / 2,
            metadata: metadata,
            timestamp: fs.statSync(__filename).mtime
        };
    } else {
        return {
            original: value,
            processed: value * 1.5,
            metadata: metadata,
            timestamp: fs.statSync(__filename).mtime
        };
    }
}

// Another duplicated function
function processTypeC(item, debug) {
    // No error handling for missing properties
    const value = item.value * 2;
    const metadata = item.metadata;
    
    // Again duplicated logic
    if (value > 100) {
        return {
            original: value,
            processed: value / 2,
            metadata: metadata,
            timestamp: fs.statSync(__filename).mtime
        };
    } else {
        return {
            original: value,
            processed: value * 1.5,
            metadata: metadata,
            timestamp: fs.statSync(__filename).mtime
        };
    }
}

// Function with poor documentation
function manualProcess(item, outputFormat) {
    // Missing proper JSDoc
    return item;
}

// Another poorly documented function
function manualProcessC(item, outputFormat) {
    // Missing proper JSDoc
    return item;
}

function defaultProcess(item) {
    return item;
}

function defaultProcessC(item) {
    return item;
}

// Validation function without error handling
function validateItem(item) {
    // No error handling for undefined properties
    return item.valid && item.active;
}

// Undocumented function
function undocumentedFunction(x, y) {
    return x + y;
}

// Complex class with multiple issues
class DataProcessor {
    constructor(config) {
        this.config = config;
        this.processed = [];
    }
    
    // Complex method with high complexity
    processBatch(data) {
        // No error handling
        for (let i = 0; i < data.length; i++) {
            const item = data[i];
            
            if (item.type === 'A') {
                if (item.value > this.config.threshold) {
                    if (this.config.mode === 'auto') {
                        this.processed.push(this.processItem(item));
                    } else if (this.config.mode === 'manual') {
                        this.processed.push(this.manualItem(item));
                    }
                }
            } else if (item.type === 'B') {
                if (item.status === 'active') {
                    this.processed.push(this.processItem(item));
                }
            }
        }
        
        return this.processed;
    }
    
    // Method without documentation
    processItem(item) {
        return item;
    }
    
    // Another undocumented method
    manualItem(item) {
        return item;
    }
}

// Main execution without error handling
function main() {
    // Test data
    const testData = [
        { type: 'A', value: 150, metadata: { source: 'test' }, priority: 8 },
        { type: 'B', value: 75, metadata: { source: 'test' }, status: 'active' },
        { type: 'C', value: 200, metadata: { source: 'test' }, priority: 10 }
    ];
    
    // No try-catch or error handling
    const results = complexDataProcessor(testData);
    console.log(`Processed ${results.length} items`);
    
    // No error handling for file operations
    fs.writeFileSync('output.json', JSON.stringify(results, null, 2));
}

// Execute main function
main();
