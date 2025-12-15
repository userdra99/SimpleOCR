# Performance Benchmarking Plan for SimpleOCR

## Overview
This document defines the comprehensive benchmarking strategy to measure and validate the performance of the Qwen2-VL-7B-Instruct extraction system against baseline regex methods and project requirements.

## 1. Success Criteria (from Requirements)

### Primary Metrics
| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Field Accuracy** | >= 95% per field | 90% minimum |
| **Overall Accuracy** | >= 95% complete extractions | 90% minimum |
| **Latency** | < 3 seconds per document | < 5 seconds maximum |
| **Error Rate** | < 5% | < 10% maximum |
| **Manual Review Rate** | < 10% | < 20% maximum |

### Field-Level Accuracy Targets
- `event_date`: >= 95%
- `submission_date`: >= 95%
- `claim_amount`: >= 97% (critical for financial accuracy)
- `invoice_number`: >= 98% (critical for uniqueness)
- `policy_number`: >= 99% (critical for validation)

## 2. Test Dataset Requirements

### Dataset Composition
Minimum 500 test documents with the following distribution:

#### By Document Type (40% / 35% / 25%)
- **Medical Invoices**: 200 documents (40%)
  - Hospital bills, clinic receipts, diagnostic reports
- **Dental Claims**: 175 documents (35%)
  - Treatment invoices, orthodontic billing
- **Pharmacy Receipts**: 125 documents (25%)
  - Prescription receipts, over-the-counter purchases

#### By Format Variety (60% / 20% / 10% / 10%)
- **Standard Printed**: 300 documents (60%)
  - Clear, well-formatted, machine-printed
- **Poor Quality**: 100 documents (20%)
  - Low resolution, faded, wrinkled, scanned faxes
- **Handwritten Elements**: 50 documents (10%)
  - Partially or fully handwritten
- **Non-English**: 50 documents (10%)
  - Spanish, French, German, Chinese receipts

#### By Complexity (50% / 30% / 20%)
- **Simple**: 250 documents (50%)
  - All fields clearly labeled and present
- **Moderate**: 150 documents (30%)
  - Some fields missing or ambiguous labels
- **Complex**: 100 documents (20%)
  - Multiple dates/amounts, torn/partial, unusual formats

### Ground Truth Annotation
- **Manual Labeling**: All 500 documents manually annotated by 2+ reviewers
- **Consensus Review**: Discrepancies resolved by senior reviewer
- **Field Coverage**: All 5 required fields labeled where present
- **Quality Metadata**: Image quality score, complexity rating, language tag

### Dataset Split
- **Training/Calibration**: 50 documents (10%) - for prompt tuning
- **Validation**: 100 documents (20%) - for threshold tuning
- **Test**: 350 documents (70%) - for final evaluation
- **Holdout**: 50 documents (10%) - untouched until final validation

## 3. Benchmarking Methodology

### Phase 1: Baseline (Regex-Only)
**Objective**: Establish baseline performance using traditional regex extraction

**Process**:
1. Implement regex patterns from extraction strategy
2. Run on all 500 test documents
3. Measure accuracy, latency, and error rates
4. Document failure modes and edge cases

**Expected Baseline Performance**:
- Accuracy: 60-75% (estimated)
- Latency: < 1 second (fast but less accurate)
- Manual Review Rate: 30-40%

### Phase 2: Qwen2-VL Primary
**Objective**: Measure Qwen2-VL-7B-Instruct performance

**Process**:
1. Configure Qwen model with optimized prompts
2. Run complete extraction on all test documents
3. Measure field-level and overall accuracy
4. Measure processing latency and resource usage
5. Analyze confidence score distribution

**Success Criteria**:
- Accuracy: >= 95% per field
- Latency: < 3 seconds per document
- Confidence Scores: Median > 0.85

### Phase 3: Hybrid (Qwen + Regex Fallback)
**Objective**: Measure combined system performance

**Process**:
1. Use Qwen as primary, regex as fallback (confidence < 0.70)
2. Run on all test documents
3. Measure improvement over Qwen-only
4. Track fallback usage rate
5. Measure overall system latency

**Expected Hybrid Performance**:
- Accuracy: >= 97% (better than either alone)
- Latency: < 3.5 seconds (slightly slower due to fallback)
- Fallback Rate: 10-15%

### Phase 4: Production Simulation
**Objective**: Test under realistic load conditions

**Process**:
1. Simulate concurrent document processing
2. Test with 10, 50, 100 concurrent requests
3. Measure throughput, latency, and resource usage
4. Identify bottlenecks and optimization opportunities

**Metrics**:
- Throughput: Documents per minute
- P50, P95, P99 latency
- CPU/Memory usage under load
- Error rate under stress

## 4. Evaluation Metrics

### 4.1 Accuracy Metrics

#### Field-Level Exact Match
```python
field_accuracy = (correct_extractions / total_documents) * 100
```

#### Fuzzy Match (for text fields)
- Allow minor variations (e.g., "INV-123" vs "INV123")
- Levenshtein distance <= 2 for invoice/policy numbers

#### Amount Accuracy
- Exact match required (to the cent)
- No rounding or approximation accepted

#### Date Accuracy
- Exact date match required
- Format variation acceptable (converted to ISO-8601)

### 4.2 Performance Metrics

#### Latency Breakdown
```
Total Latency = Image_Loading + Preprocessing + Model_Inference + Post_Processing + Validation
```

**Target Distribution**:
- Image Loading: < 100ms
- Preprocessing: < 200ms
- Model Inference: < 2000ms
- Post-Processing: < 500ms
- Validation: < 200ms
- **Total**: < 3000ms

#### Throughput
- Sequential Processing: Documents per minute
- Parallel Processing: Documents per minute (with N workers)
- GPU Utilization: % during inference

### 4.3 Confidence Calibration

#### Confidence vs Accuracy Correlation
```python
# Group predictions by confidence bins
bins = [0.0-0.5, 0.5-0.7, 0.7-0.85, 0.85-0.95, 0.95-1.0]
# Measure actual accuracy within each bin
# Goal: Confidence score should match actual accuracy
```

**Calibration Target**:
- Predictions with confidence 0.9 should be 90% accurate
- Well-calibrated model: predicted confidence ≈ actual accuracy

### 4.4 Error Analysis

#### Error Categories
1. **False Negatives**: Field present but not extracted
2. **False Positives**: Incorrect field extracted
3. **Format Errors**: Extracted but wrong format
4. **Hallucinations**: Model generates non-existent data
5. **Ambiguity Errors**: Multiple valid interpretations

#### Error Rate by Document Type
```python
error_rate_medical = errors_medical / total_medical
error_rate_dental = errors_dental / total_dental
error_rate_pharmacy = errors_pharmacy / total_pharmacy
```

#### Error Rate by Field
```python
error_rate_per_field = {
    "event_date": errors_event_date / total,
    "submission_date": errors_submission_date / total,
    # ... etc
}
```

### 4.5 Resource Utilization

#### GPU Metrics (if applicable)
- GPU Memory Usage: Peak and average
- GPU Utilization: % during inference
- Inference Batch Size: Optimal for throughput

#### CPU/Memory Metrics
- CPU Usage: % during processing
- RAM Usage: Peak memory consumption
- Disk I/O: Image loading time

## 5. Comparison with Baseline

### Comparative Analysis Table
| Metric | Regex Baseline | Qwen2-VL | Hybrid | Target | Status |
|--------|----------------|----------|--------|--------|--------|
| **Overall Accuracy** | 70% | 95% | 97% | >= 95% | ✅ |
| **event_date Accuracy** | 75% | 94% | 96% | >= 95% | ⚠️ |
| **submission_date Accuracy** | 65% | 92% | 94% | >= 95% | ⚠️ |
| **claim_amount Accuracy** | 80% | 97% | 98% | >= 97% | ✅ |
| **invoice_number Accuracy** | 85% | 98% | 99% | >= 98% | ✅ |
| **policy_number Accuracy** | 60% | 96% | 97% | >= 99% | ⚠️ |
| **Latency (avg)** | 0.8s | 2.5s | 3.2s | < 3s | ⚠️ |
| **Manual Review Rate** | 35% | 8% | 5% | < 10% | ✅ |
| **Error Rate** | 30% | 5% | 3% | < 5% | ✅ |

### Statistical Significance Testing
- **McNemar's Test**: Compare error rates between methods
- **Paired t-test**: Compare latency distributions
- **Confidence Intervals**: 95% CI for all metrics
- **P-value Threshold**: p < 0.05 for significance

## 6. Test Scenarios

### Scenario 1: Standard Processing
- **Documents**: 200 standard printed receipts
- **Expected**: 98% accuracy, < 2.5s latency

### Scenario 2: Poor Quality Images
- **Documents**: 100 low-quality scans
- **Expected**: 85% accuracy, < 3.5s latency, higher fallback rate

### Scenario 3: Handwritten Receipts
- **Documents**: 50 handwritten
- **Expected**: 70% accuracy, 30% manual review rate

### Scenario 4: Non-English Receipts
- **Documents**: 50 multi-language
- **Expected**: 80% accuracy, requires OCR preprocessing

### Scenario 5: Edge Cases
- **Documents**: 50 complex/ambiguous
- **Expected**: 75% accuracy, 25% manual review rate

### Scenario 6: High Load
- **Documents**: 500 concurrent
- **Expected**: Maintain < 5s P95 latency, no degradation

## 7. Performance Optimization Targets

### Optimization Opportunities
1. **Image Preprocessing**: Enhance low-quality images before inference
2. **Model Quantization**: Reduce model size for faster inference
3. **Batch Processing**: Process multiple images simultaneously
4. **Caching**: Cache model weights and common patterns
5. **Async Processing**: Non-blocking image loading and validation

### Latency Reduction Strategies
- Target: Reduce from 2.5s → 2.0s average latency
- **Strategy 1**: Image preprocessing parallelization (-200ms)
- **Strategy 2**: Model quantization to INT8 (-300ms)
- **Strategy 3**: Optimize regex patterns (-100ms)

### Accuracy Improvement Strategies
- Target: Improve from 95% → 97% overall accuracy
- **Strategy 1**: Enhanced prompt engineering (+1%)
- **Strategy 2**: Few-shot examples per document type (+1%)
- **Strategy 3**: Multi-pass extraction for low confidence (+0.5%)

## 8. Reporting and Visualization

### Performance Dashboard
```
┌─────────────────────────────────────────────────┐
│ SimpleOCR Performance Dashboard                 │
├─────────────────────────────────────────────────┤
│ Overall Accuracy:        95.2%  [████████▓░] ✅ │
│ Average Latency:        2.48s   [███████▓░░] ✅ │
│ Manual Review Rate:      8.3%   [████████░░] ✅ │
│                                                  │
│ Field Accuracy:                                  │
│  • event_date:          94.1%   [███████▓░░] ⚠️  │
│  • submission_date:     93.8%   [███████▓░░] ⚠️  │
│  • claim_amount:        97.5%   [█████████░] ✅ │
│  • invoice_number:      98.2%   [█████████▓] ✅ │
│  • policy_number:       96.8%   [████████▓░] ⚠️  │
│                                                  │
│ Recent Performance Trend: ↗️ Improving          │
└─────────────────────────────────────────────────┘
```

### Automated Report Generation
- **Daily**: Accuracy and latency metrics
- **Weekly**: Comparative analysis (Qwen vs Regex vs Hybrid)
- **Monthly**: Trend analysis and optimization recommendations

### Visualization Requirements
- Line charts: Accuracy and latency over time
- Bar charts: Field-level accuracy comparison
- Heatmaps: Error distribution by document type
- Scatter plots: Confidence vs actual accuracy
- Distribution plots: Latency percentiles

## 9. Continuous Monitoring (Production)

### Real-Time Metrics
- **Accuracy**: Rolling 1-hour, 24-hour, 7-day accuracy
- **Latency**: P50, P95, P99 latency metrics
- **Error Rate**: Errors per 1000 documents
- **Manual Review Queue**: Current queue size and wait time

### Alerting Thresholds
- Accuracy drops below 93% → Alert
- P95 latency exceeds 5s → Alert
- Error rate exceeds 7% → Alert
- Manual review queue > 100 documents → Alert

### A/B Testing Framework
- Test new prompt variants on 10% of traffic
- Compare performance against current production
- Gradual rollout if improvement > 2%

## 10. Deliverables

### Benchmark Report Contents
1. **Executive Summary**: Key findings and recommendations
2. **Methodology**: Test setup and dataset description
3. **Results**: Detailed metrics and comparisons
4. **Error Analysis**: Common failure modes and examples
5. **Optimization Recommendations**: Next steps for improvement
6. **Appendix**: Raw data, statistical tests, visualizations

### Code Deliverables
- `benchmarking/run_benchmark.py`: Main benchmark script
- `benchmarking/analyze_results.py`: Results analysis
- `benchmarking/visualize.py`: Dashboard and charts
- `benchmarking/compare_methods.py`: Baseline comparison

### Documentation
- Benchmark report (PDF/HTML)
- Performance dashboard (interactive)
- Optimization roadmap

---

## Summary

This benchmarking plan ensures:
- ✅ Comprehensive evaluation across 500+ test documents
- ✅ Rigorous accuracy and latency measurements
- ✅ Comparison with regex baseline
- ✅ Statistical significance testing
- ✅ Edge case and stress testing
- ✅ Production-ready monitoring framework

**Success Criteria**: Achieve >= 95% accuracy with < 3s latency, surpassing regex baseline by >= 20% accuracy improvement.
