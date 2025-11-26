"""
ONNX Runtime for Fast ML Inference
"""
import logging
import time
from typing import Dict, List
import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

class ONNXPredictor:
    """Fast ML inference using ONNX Runtime"""
    
    def __init__(self, model_path: str):
        """
        Initialize ONNX model
        
        Args:
            model_path: Path to .onnx model file
        """
        try:
            self.session = ort.InferenceSession(
                model_path,
                providers=['CPUExecutionProvider']  # Use GPU if available: 'CUDAExecutionProvider'
            )
            
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            
            logger.info(f"✅ ONNX model loaded: {model_path}")
            logger.info(f"   Input: {self.input_name}, Output: {self.output_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load ONNX model: {e}")
            raise
    
    def predict(self, features: Dict) -> Dict:
        """
        Run inference on features
        
        Returns:
            {
                "risk_score": float,
                "risk_level": str,
                "inference_time_ms": float
            }
        """
        start_time = time.perf_counter()
        
        try:
            # ✅ Prepare input (convert dict to numpy array)
            input_array = self._prepare_input(features)
            
            # ✅ Run inference
            outputs = self.session.run([self.output_name], {self.input_name: input_array})
            risk_score = float(outputs[0][0])
            
            # ✅ Calculate inference time
            inference_time = (time.perf_counter() - start_time) * 1000  # ms
            
            # ✅ Classify risk level
            if risk_score >= 0.8:
                risk_level = "CRITICAL"
            elif risk_score >= 0.6:
                risk_level = "HIGH"
            elif risk_score >= 0.4:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            result = {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "inference_time_ms": inference_time,
                "model": "onnx"
            }
            
            # ✅ Log slow inferences
            if inference_time > 10:
                logger.warning(f"⚠️  Slow inference: {inference_time:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Inference failed: {e}")
            return {
                "risk_score": 0.5,
                "risk_level": "UNKNOWN",
                "inference_time_ms": 0,
                "error": str(e)
            }
    
    def _prepare_input(self, features: Dict) -> np.ndarray:
        """Convert feature dict to model input format"""
        # Example: Extract specific features in order
        feature_order = [
            "heart_rate", "spo2", "temperature", "respiratory_rate",
            "heart_rate_mean", "heart_rate_std", "heart_rate_trend",
            "spo2_mean", "spo2_std", "spo2_trend"
        ]
        
        values = [features.get(f, 0.0) for f in feature_order]
        return np.array([values], dtype=np.float32)