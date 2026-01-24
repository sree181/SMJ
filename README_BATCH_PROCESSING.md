# SMJ Batch Processing System (1985-1994)

A production-grade batch processing system for ingesting Strategic Management Journal papers from 1985-1994 with comprehensive entity extraction and 5-year temporal window management.

## 🎯 Overview

This system processes all SMJ papers from 1985-1994 in 5-year temporal windows:
- **1985-1989**: First temporal window
- **1990-1994**: Second temporal window

Each paper is processed with comprehensive entity extraction from all sections:
- Abstract, Introduction, Literature Review
- Methodology, Results, Discussion, Conclusion

## 🚀 Quick Start

### 1. Start Batch Processing
```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python batch_processor.py
```

### 2. Monitor Progress (Optional)
```bash
# In a separate terminal
python monitor_processing.py
```

### 3. Validate Results
```bash
python validate_extraction.py
```

## 📊 System Components

### 1. **BatchProcessor** (`batch_processor.py`)
- **Temporal Window Management**: Automatically creates 5-year windows
- **Parallel Processing**: Multi-threaded processing for efficiency
- **Comprehensive Extraction**: All entity types from all paper sections
- **Error Handling**: Robust error handling with detailed logging
- **Progress Tracking**: Real-time progress monitoring
- **Quality Control**: Validation and reporting

### 2. **ProcessingMonitor** (`monitor_processing.py`)
- **Real-time Dashboard**: Live statistics and progress
- **Knowledge Graph Stats**: Current entity counts
- **Processing Logs**: Recent processing activity
- **System Health**: Connection status and performance

### 3. **ExtractionValidator** (`validate_extraction.py`)
- **Data Quality Assessment**: Completeness and accuracy validation
- **Entity Quality Checks**: Length, duplication, and consistency
- **Relationship Validation**: Orphaned entities and relationship quality
- **Temporal Consistency**: Year distribution and data integrity
- **Quality Scoring**: Overall extraction quality assessment

## 🔧 Configuration

### Batch Processing Parameters (`batch_config.json`)
```json
{
  "processing": {
    "start_year": 1985,
    "end_year": 1994,
    "max_workers": 3,
    "window_size": 5
  },
  "extraction": {
    "max_text_length": 15000,
    "chunk_size": 3000,
    "extract_all_sections": true
  }
}
```

### Environment Variables
```env
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
OPENAI_API_KEY=your-openai-key
```

## 📈 Expected Results

### Entity Extraction Targets
- **Research Questions**: 50-100+ per window
- **Methodologies**: 30-60+ per window
- **Findings**: 60-120+ per window
- **Contributions**: 30-60+ per window
- **Entities**: 200-400+ per window
- **Relationships**: 100-300+ per window

### Quality Metrics
- **Success Rate**: >95% papers processed successfully
- **Entity Completeness**: >80% papers with minimal entity set
- **Processing Speed**: 2-5 papers per minute (depending on complexity)
- **Data Quality Score**: >80/100

## 🛠️ Advanced Usage

### Custom Processing Windows
```python
from batch_processor import BatchProcessor

processor = BatchProcessor(Path('.'))
# Process specific years
report = processor.process_all_windows(1985, 1990, max_workers=5)
```

### Parallel Processing Tuning
```python
# Adjust based on your system capacity
# More workers = faster processing but more memory usage
processor.process_all_windows(1985, 1994, max_workers=5)
```

### Quality Validation
```python
from validate_extraction import ExtractionValidator

validator = ExtractionValidator()
report = validator.generate_validation_report()
validator.print_validation_summary(report)
```

## 📊 Monitoring and Reporting

### Real-time Monitoring
- **Live Dashboard**: Current processing status
- **Entity Counts**: Real-time knowledge graph statistics
- **Error Tracking**: Failed papers and error details
- **Performance Metrics**: Processing speed and efficiency

### Detailed Reports
- **Processing Report**: Complete processing statistics
- **Validation Report**: Data quality assessment
- **Error Log**: Detailed error information
- **Entity Analysis**: Entity distribution and quality

## 🔍 Troubleshooting

### Common Issues

1. **Memory Issues**
   - Reduce `max_workers` in configuration
   - Process smaller temporal windows
   - Increase system memory

2. **API Rate Limits**
   - Reduce `max_workers` to 1-2
   - Add delays between requests
   - Use API key with higher limits

3. **Neo4j Connection Issues**
   - Check connection credentials
   - Verify Neo4j Aura instance status
   - Check network connectivity

4. **Processing Failures**
   - Check `batch_processing.log` for details
   - Verify PDF file integrity
   - Check OpenAI API key validity

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📁 Output Files

### Generated Reports
- `batch_processing_report_YYYYMMDD_HHMMSS.json`: Complete processing report
- `validation_report.json`: Data quality validation report
- `batch_processing.log`: Detailed processing logs

### Knowledge Graph Updates
- All extracted entities added to Neo4j
- Relationships established between entities
- Temporal metadata preserved
- Section-level context maintained

## 🎯 Success Criteria

### Processing Success
- ✅ All papers from 1985-1994 processed
- ✅ 5-year temporal windows maintained
- ✅ All entity types extracted
- ✅ Relationships established
- ✅ Quality validation passed

### Quality Metrics
- ✅ >95% success rate
- ✅ >80% papers with complete entity sets
- ✅ <5% data quality issues
- ✅ Temporal consistency maintained

## 🚀 Next Steps

After successful batch processing:

1. **Run Validation**: `python validate_extraction.py`
2. **Check Knowledge Graph**: Verify all entities in Neo4j
3. **Test Queries**: Use the chatbot to test extracted data
4. **Analyze Results**: Review processing reports
5. **Scale Up**: Process additional years if needed

## 📞 Support

For issues or questions:
1. Check the processing logs
2. Run validation scripts
3. Review configuration settings
4. Check system resources

---

**Built for Production-Grade SMJ Research Processing** 🎓
