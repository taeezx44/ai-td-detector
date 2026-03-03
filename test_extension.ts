// Test TypeScript file for AI-TD Detector Extension
// Contains patterns that should trigger AI-TD detection

interface DataItem {
    type: string;
    value: number;
    metadata: Record<string, any>;
    priority?: number;
    status?: string;
    valid?: boolean;
    active?: boolean;
}

interface ProcessingOptions {
    threshold?: number;
    mode?: 'auto' | 'manual';
    debug?: boolean;
    outputFormat?: string;
    validate?: boolean;
    maxIterations?: number;
    tolerance?: number;
}

interface ProcessedItem {
    original: number;
    processed: number;
    metadata: Record<string, any>;
    timestamp: Date;
}

// Complex function with high cyclomatic complexity
function complexDataProcessor(data: DataItem[], options: ProcessingOptions = {}): ProcessedItem[] | null {
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

    const results: ProcessedItem[] = [];
    
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
            if (item.priority && item.priority > 5) {
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
function processTypeA(item: DataItem, debug: boolean): ProcessedItem {
    // No error handling for missing properties
    const value = item.value * 2;
    const metadata = item.metadata;
    
    // Complex calculation
    if (value > 100) {
        return {
            original: value,
            processed: value / 2,
            metadata: metadata,
            timestamp: new Date()
        };
    } else {
        return {
            original: value,
            processed: value * 1.5,
            metadata: metadata,
            timestamp: new Date()
        };
    }
}

// Duplicated function - should trigger duplication detection
function processTypeB(item: DataItem, debug: boolean): ProcessedItem {
    // No error handling for missing properties
    const value = item.value * 2;
    const metadata = item.metadata;
    
    // Duplicated logic from processTypeA
    if (value > 100) {
        return {
            original: value,
            processed: value / 2,
            metadata: metadata,
            timestamp: new Date()
        };
    } else {
        return {
            original: value,
            processed: value * 1.5,
            metadata: metadata,
            timestamp: new Date()
        };
    }
}

// Another duplicated function
function processTypeC(item: DataItem, debug: boolean): ProcessedItem {
    // No error handling for missing properties
    const value = item.value * 2;
    const metadata = item.metadata;
    
    // Again duplicated logic
    if (value > 100) {
        return {
            original: value,
            processed: value / 2,
            metadata: metadata,
            timestamp: new Date()
        };
    } else {
        return {
            original: value,
            processed: value * 1.5,
            metadata: metadata,
            timestamp: new Date()
        };
    }
}

// Function with poor documentation
function manualProcess(item: DataItem, outputFormat: string): DataItem {
    // Missing proper JSDoc
    return item;
}

// Another poorly documented function
function manualProcessC(item: DataItem, outputFormat: string): DataItem {
    // Missing proper JSDoc
    return item;
}

function defaultProcess(item: DataItem): DataItem {
    return item;
}

function defaultProcessC(item: DataItem): DataItem {
    return item;
}

// Validation function without error handling
function validateItem(item: DataItem): boolean {
    // No error handling for undefined properties
    return (item.valid || false) && (item.active || false);
}

// Undocumented function
function undocumentedFunction(x: number, y: number): number {
    return x + y;
}

// Complex class with multiple issues
class DataProcessor {
    private config: ProcessingOptions;
    private processed: ProcessedItem[];

    constructor(config: ProcessingOptions) {
        this.config = config;
        this.processed = [];
    }
    
    // Complex method with high complexity
    processBatch(data: DataItem[]): ProcessedItem[] {
        // No error handling
        for (let i = 0; i < data.length; i++) {
            const item = data[i];
            
            if (item.type === 'A') {
                if (item.value > (this.config.threshold || 0.5)) {
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
    processItem(item: DataItem): ProcessedItem {
        return {
            original: item.value,
            processed: item.value * 2,
            metadata: item.metadata,
            timestamp: new Date()
        };
    }
    
    // Another undocumented method
    manualItem(item: DataItem): ProcessedItem {
        return {
            original: item.value,
            processed: item.value * 1.5,
            metadata: item.metadata,
            timestamp: new Date()
        };
    }
}

// Main execution without error handling
function main(): void {
    // Test data
    const testData: DataItem[] = [
        { type: 'A', value: 150, metadata: { source: 'test' }, priority: 8 },
        { type: 'B', value: 75, metadata: { source: 'test' }, status: 'active' },
        { type: 'C', value: 200, metadata: { source: 'test' }, priority: 10 }
    ];
    
    // No try-catch or error handling
    const results = complexDataProcessor(testData);
    console.log(`Processed ${results?.length || 0} items`);
    
    // No error handling for file operations
    const fs = require('fs');
    fs.writeFileSync('output.json', JSON.stringify(results, null, 2));
}

// Execute main function
main();
