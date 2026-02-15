from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

class ValidationLevel(Enum):
    """Validation result levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FAILED = "failed"

@dataclass
class ValidationResult:
    """Results from validation framework"""
    level: ValidationLevel
    confidence_score: float
    passed_checks: List[str]
    failed_checks: List[str]
    warnings: List[str]
    details: Dict[str, Any]
    
    def is_safe_to_use(self) -> bool:
        """Check if answer is safe to use in production"""
        return self.level in [ValidationLevel.HIGH, ValidationLevel.MEDIUM]

class MultiStageValidator:
    """
    Multi-stage validation framework for LLM outputs
    
    This is especially critical when using smaller models, as they are
    more prone to hallucination and extraction errors.
    """
    
    def __init__(
        self,
        retrieval_threshold: float = 0.3,
        alignment_threshold: float = 0.5,
        min_confidence: float = 0.6
    ):
        """
        Initialize validator with thresholds
        
        Args:
            retrieval_threshold: Minimum retrieval score to consider context relevant
            alignment_threshold: Minimum alignment between answer and sources
            min_confidence: Minimum overall confidence for HIGH validation
        """
        self.retrieval_threshold = retrieval_threshold
        self.alignment_threshold = alignment_threshold
        self.min_confidence = min_confidence
    
    def validate(
        self,
        query: str,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Run full multi-stage validation
        
        Args:
            query: Original user query
            answer: LLM-generated answer
            retrieved_chunks: Retrieved context chunks with scores
            
        Returns:
            ValidationResult with detailed assessment
        """
        passed_checks = []
        failed_checks = []
        warnings = []
        details = {}
        
        retrieval_score = self._check_retrieval_quality(retrieved_chunks)
        details["retrieval_score"] = retrieval_score
        
        if retrieval_score >= self.retrieval_threshold:
            passed_checks.append("retrieval_quality")
        else:
            failed_checks.append("retrieval_quality")
            warnings.append(f"Low retrieval quality (score: {retrieval_score:.2f})")
        
        alignment_score = self._check_source_alignment(answer, retrieved_chunks)
        details["alignment_score"] = alignment_score
        
        if alignment_score >= self.alignment_threshold:
            passed_checks.append("source_alignment")
        else:
            failed_checks.append("source_alignment")
            warnings.append("Answer may not be well-supported by sources")
        
        hallucination_check = self._detect_hallucination(answer, retrieved_chunks)
        details["hallucination_indicators"] = hallucination_check
        
        if not hallucination_check["likely_hallucination"]:
            passed_checks.append("hallucination_check")
        else:
            failed_checks.append("hallucination_check")
            warnings.extend(hallucination_check["indicators"])
        
        numerical_check = self._check_numerical_accuracy(answer, retrieved_chunks)
        details["numerical_accuracy"] = numerical_check
        
        if numerical_check["has_numbers"]:
            if numerical_check["validated"]:
                passed_checks.append("numerical_accuracy")
            else:
                failed_checks.append("numerical_accuracy")
                warnings.append("Numbers in answer may not match source documents")
        
        confidence_score = self._calculate_confidence(
            retrieval_score,
            alignment_score,
            len(passed_checks),
            len(failed_checks)
        )
        
        level = self._determine_validation_level(
            confidence_score,
            failed_checks
        )
        
        return ValidationResult(
            level=level,
            confidence_score=confidence_score,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            details=details
        )
    
    def _check_retrieval_quality(
        self, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Stage 1: Check quality of retrieved context
        
        Returns score 0-1 based on retrieval confidence
        """
        if not retrieved_chunks:
            return 0.0
        
        scores = [
            chunk.get("combined_score", 0.0) 
            for chunk in retrieved_chunks
        ]
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _check_source_alignment(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Stage 2: Check if answer aligns with retrieved sources
        
        Uses token overlap as a proxy for alignment
        """
        if not retrieved_chunks or not answer:
            return 0.0
        
        answer_tokens = set(answer.lower().split())
        
        source_text = " ".join([
            chunk.get("text", "") 
            for chunk in retrieved_chunks
        ])
        source_tokens = set(source_text.lower().split())
        
        if not answer_tokens:
            return 0.0
        
        overlap = answer_tokens.intersection(source_tokens)
        alignment_score = len(overlap) / len(answer_tokens)
        
        return alignment_score
    
    def _detect_hallucination(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Stage 3: Detect potential hallucinations
        
        Looks for common hallucination patterns in small models
        """
        indicators = []
        likely_hallucination = False
        
        if "cannot find" in answer.lower() or "not available" in answer.lower():
            if len(answer.split()) > 20:
                indicators.append("Contradictory: Claims no info but provides detail")
                likely_hallucination = True
        
        has_specifics = bool(re.search(r'\d+\.?\d*%|\$\d+|[A-Z][a-z]+ \d{1,2}, \d{4}', answer))
        has_citations = "Source" in answer or "According to" in answer
        
        if has_specifics and not has_citations and len(retrieved_chunks) > 0:
            indicators.append("Specific claims without source attribution")
        
        if retrieved_chunks:
            source_length = sum(len(c.get("text", "")) for c in retrieved_chunks)
            if len(answer) > source_length * 0.5:
                indicators.append("Answer length exceeds reasonable extraction ratio")
        
        if len(indicators) >= 2:
            likely_hallucination = True
        
        return {
            "likely_hallucination": likely_hallucination,
            "indicators": indicators,
            "confidence": 1.0 - (len(indicators) * 0.3)
        }
    
    def _check_numerical_accuracy(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Stage 4: Validate numerical accuracy
        
        Critical for financial documents - numbers must be exact
        """
        answer_numbers = self._extract_numbers(answer)
        
        if not answer_numbers:
            return {
                "has_numbers": False,
                "validated": True
            }
        
        source_text = " ".join([c.get("text", "") for c in retrieved_chunks])
        source_numbers = self._extract_numbers(source_text)
        validated = all(num in source_numbers for num in answer_numbers)
        
        return {
            "has_numbers": True,
            "validated": validated,
            "answer_numbers": answer_numbers,
            "matched_count": sum(1 for num in answer_numbers if num in source_numbers),
            "total_count": len(answer_numbers)
        }
    
    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numerical values from text"""
        patterns = [
            r'\d+\.?\d*%',
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            r'\d+\.?\d*'
        ]
        
        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text))
        
        return numbers
    
    def _calculate_confidence(
        self,
        retrieval_score: float,
        alignment_score: float,
        passed_count: int,
        failed_count: int
    ) -> float:
        """Calculate overall confidence score"""
        confidence = (
            0.3 * retrieval_score +
            0.3 * alignment_score +
            0.4 * (passed_count / max(passed_count + failed_count, 1))
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _determine_validation_level(
        self,
        confidence_score: float,
        failed_checks: List[str]
    ) -> ValidationLevel:
        """Determine final validation level"""
        
        critical_failures = {"retrieval_quality", "numerical_accuracy"}
        has_critical_failure = bool(set(failed_checks) & critical_failures)
        
        if has_critical_failure:
            return ValidationLevel.FAILED
        
        if confidence_score >= self.min_confidence:
            return ValidationLevel.HIGH
        elif confidence_score >= 0.4:
            return ValidationLevel.MEDIUM
        else:
            return ValidationLevel.LOW