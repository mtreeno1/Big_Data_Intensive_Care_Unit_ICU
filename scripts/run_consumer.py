#!/usr/bin/env python3
"""
Run Kafka Consumer with Data Validation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from src.kafka_consumer.consumer import VitalSignsConsumer
from src.stream_processing.data_validator import MedicalDataValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedConsumer(VitalSignsConsumer):
    """Consumer with data validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = MedicalDataValidator()
        # ✅ FIX: Use separate dict for validation stats
        self.validation_stats = {"validated": 0, "invalid": 0, "quality_issues": 0}
    
    def process_callback(self, reading):
        """Process with validation"""
        try:
            # Validate data
            cleaned_reading, is_valid = self.validator.validate_and_clean(reading)
            
            if not is_valid:
                self.validation_stats["invalid"] += 1
                logger.warning(f"⚠️  Invalid data for {reading.get('patient_id')}")
                return False
            
            # Log data quality issues
            if "data_quality_issues" in cleaned_reading:
                self.validation_stats["quality_issues"] += 1
                issues = cleaned_reading['data_quality_issues']
                logger.warning(f"⚠️  {reading.get('patient_id')}: {issues}")
            
            self.validation_stats["validated"] += 1
            
            # Update the reading with cleaned version
            reading.update(cleaned_reading)
            
            # Continue with parent's processing
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}", exc_info=True)
            return False
    
    def log_validation_summary(self):
        """Log validation statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Valid messages: {self.validation_stats['validated']}")
        logger.info(f"⚠️  Quality issues: {self.validation_stats['quality_issues']}")
        logger.info(f"❌ Invalid messages: {self.validation_stats['invalid']}")
        
        total = (self.validation_stats['validated'] + 
                self.validation_stats['invalid'])
        if total > 0:
            success_rate = (self.validation_stats['validated'] / total) * 100
            logger.info(f"🎯 Validation success rate: {success_rate:.2f}%")
        
        logger.info("=" * 70)

def main():
    """Run consumer with validation"""
    
    logger.info("\n" + "=" * 70)
    logger.info("🏥 ICU CONSUMER WITH DATA VALIDATION")
    logger.info("=" * 70)
    logger.info("⏳ Starting consumer...")
    
    consumer = None
    
    try:
        consumer = EnhancedConsumer()
        consumer.consume_messages(
            process_callback=consumer.process_callback
        )
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Shutting down by user request...")
    
    except Exception as e:
        logger.error(f"❌ Consumer error: {e}", exc_info=True)
    
    finally:
        if consumer:
            # Log validation stats first
            consumer.log_validation_summary()
            
            # Close consumer (will log its own summary)
            consumer.close()

if __name__ == "__main__":
    main()