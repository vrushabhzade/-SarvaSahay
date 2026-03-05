"""
SarvaSahay Document Processing Service
OCR-based document extraction and validation using Tesseract
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
from datetime import datetime
import hashlib


class DocumentType(str, Enum):
    """Supported document types"""
    AADHAAR = "aadhaar"
    PAN = "pan"
    LAND_RECORDS = "land_records"
    BANK_PASSBOOK = "bank_passbook"
    RATION_CARD = "ration_card"
    VOTER_ID = "voter_id"


class DocumentQuality(str, Enum):
    """Document quality assessment"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNREADABLE = "unreadable"


class DocumentProcessor:
    """
    OCR-based document processor using Tesseract
    Handles image preprocessing, text extraction, and validation
    """
    
    def __init__(self):
        self.processed_documents = {}  # In-memory storage for demo
        
        # OCR configuration for Indian documents
        self.tesseract_config = r'--oem 3 --psm 6'
        
        # Document patterns for validation
        self.patterns = {
            DocumentType.AADHAAR: r'\d{4}\s?\d{4}\s?\d{4}',
            DocumentType.PAN: r'[A-Z]{5}[0-9]{4}[A-Z]{1}',
            DocumentType.VOTER_ID: r'[A-Z]{3}[0-9]{7}',
        }
    
    def process_document(
        self, 
        image_data: np.ndarray, 
        document_type: DocumentType,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process document image with OCR and validation
        Implements secure document handling - raw images are deleted after processing
        
        Args:
            image_data: Image as numpy array
            document_type: Type of document being processed
            user_profile: Optional user profile for cross-validation
            
        Returns:
            Dictionary containing extracted data, quality score, and validation results
        """
        if image_data is None or image_data.size == 0:
            raise ValueError("Image data cannot be empty")
        
        try:
            # Step 1: Preprocess image
            preprocessed_image = self._preprocess_image(image_data)
            
            # Step 2: Assess image quality
            quality_score, quality_level = self._assess_image_quality(preprocessed_image)
            
            # Step 3: Extract text using OCR
            extracted_text = self._extract_text(preprocessed_image)
            
            # Step 4: Parse document-specific data
            parsed_data = self._parse_document_data(extracted_text, document_type)
            
            # Step 5: Validate extracted data
            validation_results = self._validate_extracted_data(
                parsed_data, 
                document_type,
                user_profile
            )
            
            # Step 6: Generate document ID and store
            document_id = self._generate_document_id(document_type, parsed_data)
            
            result = {
                "document_id": document_id,
                "document_type": document_type.value,
                "extracted_text": extracted_text,
                "parsed_data": parsed_data,
                "quality_score": quality_score,
                "quality_level": quality_level.value,
                "validation_results": validation_results,
                "processed_at": datetime.utcnow().isoformat(),
                "improvement_suggestions": self._generate_improvement_suggestions(
                    quality_level, 
                    validation_results
                )
            }
            
            # Store processed document (metadata only, not raw image)
            self.processed_documents[document_id] = result
            
            return result
        
        finally:
            # SECURITY: Delete raw image data from memory after processing
            # This ensures sensitive document images are not retained
            self._secure_delete_image(image_data)
            if 'preprocessed_image' in locals():
                self._secure_delete_image(preprocessed_image)
    
    def _secure_delete_image(self, image_data: np.ndarray) -> None:
        """
        Securely delete image data from memory
        Overwrites memory before deletion to prevent recovery
        
        Args:
            image_data: Image array to delete
        """
        if image_data is not None and isinstance(image_data, np.ndarray):
            # Overwrite with zeros before deletion
            image_data.fill(0)
            # Delete reference
            del image_data
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        Uses OpenCV for enhancement
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Noise reduction using bilateral filter
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Adaptive thresholding for better text contrast
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Morphological operations to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        # Deskew if needed
        processed = self._deskew_image(processed)
        
        return processed
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Correct image skew/rotation"""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Rotate image if angle is significant
        if abs(angle) > 0.5:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, 
                M, 
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return rotated
        
        return image
    
    def _assess_image_quality(self, image: np.ndarray) -> Tuple[float, DocumentQuality]:
        """
        Assess image quality for OCR readiness
        Returns quality score (0-1) and quality level
        """
        # Calculate sharpness using Laplacian variance
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness = np.mean(image)
        
        # Calculate contrast
        contrast = image.std()
        
        # Normalize metrics
        sharpness_score = min(laplacian_var / 500, 1.0)  # Normalize to 0-1
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal around 127
        contrast_score = min(contrast / 50, 1.0)  # Normalize to 0-1
        
        # Weighted quality score
        quality_score = (
            0.5 * sharpness_score +
            0.3 * contrast_score +
            0.2 * brightness_score
        )
        
        # Determine quality level
        if quality_score >= 0.8:
            quality_level = DocumentQuality.EXCELLENT
        elif quality_score >= 0.6:
            quality_level = DocumentQuality.GOOD
        elif quality_score >= 0.4:
            quality_level = DocumentQuality.ACCEPTABLE
        elif quality_score >= 0.2:
            quality_level = DocumentQuality.POOR
        else:
            quality_level = DocumentQuality.UNREADABLE
        
        return quality_score, quality_level
    
    def _extract_text(self, image: np.ndarray) -> str:
        """Extract text from preprocessed image using Tesseract OCR"""
        try:
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(image)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                pil_image,
                config=self.tesseract_config,
                lang='eng+hin'  # English and Hindi
            )
            
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {str(e)}")
    
    def _parse_document_data(
        self, 
        text: str, 
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """Parse document-specific data from extracted text"""
        parsed_data = {}
        
        if document_type == DocumentType.AADHAAR:
            parsed_data = self._parse_aadhaar(text)
        elif document_type == DocumentType.PAN:
            parsed_data = self._parse_pan(text)
        elif document_type == DocumentType.LAND_RECORDS:
            parsed_data = self._parse_land_records(text)
        elif document_type == DocumentType.BANK_PASSBOOK:
            parsed_data = self._parse_bank_passbook(text)
        elif document_type == DocumentType.RATION_CARD:
            parsed_data = self._parse_ration_card(text)
        elif document_type == DocumentType.VOTER_ID:
            parsed_data = self._parse_voter_id(text)
        
        return parsed_data

    
    def _parse_aadhaar(self, text: str) -> Dict[str, Any]:
        """Parse Aadhaar card data"""
        data = {}
        
        # Extract Aadhaar number
        aadhaar_match = re.search(self.patterns[DocumentType.AADHAAR], text)
        if aadhaar_match:
            aadhaar = aadhaar_match.group().replace(' ', '')
            data['aadhaar_number'] = aadhaar
        
        # Extract name (usually after "Name:" or similar)
        name_patterns = [
            r'Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'नाम[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.IGNORECASE)
            if name_match:
                data['name'] = name_match.group(1).strip()
                break
        
        # Extract date of birth
        dob_patterns = [
            r'DOB[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Birth[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})',
            r'जन्म[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})'
        ]
        for pattern in dob_patterns:
            dob_match = re.search(pattern, text, re.IGNORECASE)
            if dob_match:
                data['date_of_birth'] = dob_match.group(1)
                break
        
        # Extract gender
        if re.search(r'\b(Male|MALE|पुरुष)\b', text):
            data['gender'] = 'male'
        elif re.search(r'\b(Female|FEMALE|महिला)\b', text):
            data['gender'] = 'female'
        
        # Extract address
        address_match = re.search(
            r'Address[:\s]+(.+?)(?=\n\n|\Z)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if address_match:
            data['address'] = address_match.group(1).strip()
        
        return data
    
    def _parse_pan(self, text: str) -> Dict[str, Any]:
        """Parse PAN card data"""
        data = {}
        
        # Extract PAN number
        pan_match = re.search(self.patterns[DocumentType.PAN], text)
        if pan_match:
            data['pan_number'] = pan_match.group()
        
        # Extract name
        name_match = re.search(
            r'Name[:\s]+([A-Z][A-Z\s]+)', 
            text, 
            re.IGNORECASE
        )
        if name_match:
            data['name'] = name_match.group(1).strip()
        
        # Extract father's name
        father_match = re.search(
            r"Father['\s]+Name[:\s]+([A-Z][A-Z\s]+)", 
            text, 
            re.IGNORECASE
        )
        if father_match:
            data['father_name'] = father_match.group(1).strip()
        
        # Extract date of birth
        dob_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', text)
        if dob_match:
            data['date_of_birth'] = dob_match.group(1)
        
        return data
    
    def _parse_land_records(self, text: str) -> Dict[str, Any]:
        """Parse land records document"""
        data = {}
        
        # Extract survey number
        survey_patterns = [
            r'Survey\s+No[.:\s]+(\d+[/-]?\d*)',
            r'सर्वे\s+नं[.:\s]+(\d+[/-]?\d*)'
        ]
        for pattern in survey_patterns:
            survey_match = re.search(pattern, text, re.IGNORECASE)
            if survey_match:
                data['survey_number'] = survey_match.group(1)
                break
        
        # Extract land area
        area_patterns = [
            r'Area[:\s]+([\d.]+)\s*(Acre|Hectare|acres|hectares)',
            r'क्षेत्रफल[:\s]+([\d.]+)\s*(एकर|हेक्टेयर)'
        ]
        for pattern in area_patterns:
            area_match = re.search(pattern, text, re.IGNORECASE)
            if area_match:
                data['land_area'] = float(area_match.group(1))
                data['land_unit'] = area_match.group(2).lower()
                break
        
        # Extract owner name
        owner_patterns = [
            r'Owner[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'मालक[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        for pattern in owner_patterns:
            owner_match = re.search(pattern, text, re.IGNORECASE)
            if owner_match:
                data['owner_name'] = owner_match.group(1).strip()
                break
        
        # Extract village
        village_match = re.search(
            r'Village[:\s]+([A-Za-z\s]+)', 
            text, 
            re.IGNORECASE
        )
        if village_match:
            data['village'] = village_match.group(1).strip()
        
        return data
    
    def _parse_bank_passbook(self, text: str) -> Dict[str, Any]:
        """Parse bank passbook data"""
        data = {}
        
        # Extract account number
        account_patterns = [
            r'Account\s+No[.:\s]+(\d{9,18})',
            r'A/C\s+No[.:\s]+(\d{9,18})',
            r'खाता\s+नं[.:\s]+(\d{9,18})'
        ]
        for pattern in account_patterns:
            account_match = re.search(pattern, text, re.IGNORECASE)
            if account_match:
                data['account_number'] = account_match.group(1)
                break
        
        # Extract IFSC code
        ifsc_match = re.search(r'IFSC[:\s]+([A-Z]{4}0[A-Z0-9]{6})', text, re.IGNORECASE)
        if ifsc_match:
            data['ifsc_code'] = ifsc_match.group(1)
        
        # Extract account holder name
        name_match = re.search(
            r'Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 
            text, 
            re.IGNORECASE
        )
        if name_match:
            data['account_holder_name'] = name_match.group(1).strip()
        
        # Extract bank name
        bank_patterns = [
            r'(State Bank of India|SBI|HDFC|ICICI|Axis|Punjab National|Bank of Baroda)',
        ]
        for pattern in bank_patterns:
            bank_match = re.search(pattern, text, re.IGNORECASE)
            if bank_match:
                data['bank_name'] = bank_match.group(1)
                break
        
        return data
    
    def _parse_ration_card(self, text: str) -> Dict[str, Any]:
        """Parse ration card data"""
        data = {}
        
        # Extract ration card number
        ration_match = re.search(r'Card\s+No[.:\s]+([A-Z0-9]{10,15})', text, re.IGNORECASE)
        if ration_match:
            data['ration_card_number'] = ration_match.group(1)
        
        # Extract card type (APL/BPL)
        if re.search(r'\b(APL|Above Poverty Line)\b', text, re.IGNORECASE):
            data['card_type'] = 'APL'
        elif re.search(r'\b(BPL|Below Poverty Line)\b', text, re.IGNORECASE):
            data['card_type'] = 'BPL'
        
        # Extract head of family
        head_match = re.search(
            r'Head[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 
            text, 
            re.IGNORECASE
        )
        if head_match:
            data['head_of_family'] = head_match.group(1).strip()
        
        return data
    
    def _parse_voter_id(self, text: str) -> Dict[str, Any]:
        """Parse voter ID card data"""
        data = {}
        
        # Extract voter ID number
        voter_match = re.search(self.patterns[DocumentType.VOTER_ID], text)
        if voter_match:
            data['voter_id_number'] = voter_match.group()
        
        # Extract name
        name_match = re.search(
            r'Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 
            text, 
            re.IGNORECASE
        )
        if name_match:
            data['name'] = name_match.group(1).strip()
        
        # Extract date of birth
        dob_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', text)
        if dob_match:
            data['date_of_birth'] = dob_match.group(1)
        
        return data
    
    def _validate_extracted_data(
        self,
        parsed_data: Dict[str, Any],
        document_type: DocumentType,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate extracted data against patterns and user profile
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "inconsistencies": []
        }
        
        # Validate document-specific patterns
        if document_type == DocumentType.AADHAAR:
            if 'aadhaar_number' in parsed_data:
                if not re.match(r'^\d{12}$', parsed_data['aadhaar_number']):
                    validation_results["errors"].append(
                        "Invalid Aadhaar number format"
                    )
                    validation_results["is_valid"] = False
            else:
                validation_results["errors"].append("Aadhaar number not found")
                validation_results["is_valid"] = False
        
        elif document_type == DocumentType.PAN:
            if 'pan_number' in parsed_data:
                if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', parsed_data['pan_number']):
                    validation_results["errors"].append(
                        "Invalid PAN number format"
                    )
                    validation_results["is_valid"] = False
            else:
                validation_results["errors"].append("PAN number not found")
                validation_results["is_valid"] = False
        
        # Cross-validate with user profile if provided
        if user_profile:
            inconsistencies = self._cross_validate_with_profile(
                parsed_data, 
                document_type,
                user_profile
            )
            if inconsistencies:
                validation_results["inconsistencies"] = inconsistencies
                validation_results["warnings"].append(
                    "Data inconsistencies found with user profile"
                )
        
        return validation_results
    
    def _cross_validate_with_profile(
        self,
        parsed_data: Dict[str, Any],
        document_type: DocumentType,
        user_profile: Dict[str, Any]
    ) -> List[str]:
        """Cross-validate extracted data with user profile"""
        inconsistencies = []
        
        # Check Aadhaar number
        if document_type == DocumentType.AADHAAR:
            if 'documents' in user_profile and user_profile['documents'].get('aadhaar'):
                profile_aadhaar = user_profile['documents']['aadhaar']
                extracted_aadhaar = parsed_data.get('aadhaar_number')
                if extracted_aadhaar and profile_aadhaar != extracted_aadhaar:
                    inconsistencies.append(
                        f"Aadhaar mismatch: Profile has {profile_aadhaar}, "
                        f"document shows {extracted_aadhaar}"
                    )
            
            # Check gender
            if 'gender' in parsed_data and 'demographics' in user_profile:
                profile_gender = user_profile['demographics'].get('gender')
                extracted_gender = parsed_data['gender']
                if profile_gender and profile_gender != extracted_gender:
                    inconsistencies.append(
                        f"Gender mismatch: Profile has {profile_gender}, "
                        f"document shows {extracted_gender}"
                    )
        
        # Check PAN number
        elif document_type == DocumentType.PAN:
            if 'documents' in user_profile and user_profile['documents'].get('pan'):
                profile_pan = user_profile['documents']['pan']
                extracted_pan = parsed_data.get('pan_number')
                if extracted_pan and profile_pan != extracted_pan:
                    inconsistencies.append(
                        f"PAN mismatch: Profile has {profile_pan}, "
                        f"document shows {extracted_pan}"
                    )
        
        # Check land ownership
        elif document_type == DocumentType.LAND_RECORDS:
            if 'land_area' in parsed_data and 'economic' in user_profile:
                profile_land = user_profile['economic'].get('land_ownership', 0)
                extracted_land = parsed_data['land_area']
                
                # Convert to acres if needed
                if parsed_data.get('land_unit') == 'hectare':
                    extracted_land *= 2.47105  # Convert hectares to acres
                
                # Allow 10% tolerance
                if abs(profile_land - extracted_land) > profile_land * 0.1:
                    inconsistencies.append(
                        f"Land ownership mismatch: Profile has {profile_land} acres, "
                        f"document shows {extracted_land} acres"
                    )
        
        return inconsistencies
    
    def _generate_improvement_suggestions(
        self,
        quality_level: DocumentQuality,
        validation_results: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for improving document quality or data"""
        suggestions = []
        
        # Quality-based suggestions
        if quality_level == DocumentQuality.POOR:
            suggestions.append("Image quality is poor. Please retake photo in better lighting")
            suggestions.append("Ensure document is flat and all corners are visible")
            suggestions.append("Avoid shadows and glare on the document")
        elif quality_level == DocumentQuality.UNREADABLE:
            suggestions.append("Image is unreadable. Please retake with a clearer photo")
            suggestions.append("Clean the camera lens and hold phone steady")
            suggestions.append("Use natural daylight or bright indoor lighting")
        elif quality_level == DocumentQuality.ACCEPTABLE:
            suggestions.append("Image quality is acceptable but could be improved")
            suggestions.append("Try taking photo from directly above the document")
        
        # Validation-based suggestions
        if not validation_results["is_valid"]:
            suggestions.append("Document validation failed. Please verify document authenticity")
            for error in validation_results["errors"]:
                suggestions.append(f"Issue found: {error}")
        
        if validation_results["inconsistencies"]:
            suggestions.append("Data inconsistencies detected with your profile")
            suggestions.append("Please review and update your profile if needed")
        
        return suggestions
    
    def _generate_document_id(
        self, 
        document_type: DocumentType, 
        parsed_data: Dict[str, Any]
    ) -> str:
        """Generate unique document ID"""
        key_data = f"{document_type.value}-{str(parsed_data)}-{datetime.utcnow().timestamp()}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def get_processed_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve processed document by ID"""
        return self.processed_documents.get(document_id)
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user (filtered by user_id if stored)"""
        # In real implementation, filter by user_id from database
        return list(self.processed_documents.values())
