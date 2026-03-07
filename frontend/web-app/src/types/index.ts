/**
 * TypeScript Type Definitions
 * Shared types across the application
 */

// User Profile
export interface UserProfile {
  id?: string;
  name: string;
  age: number;
  gender: 'male' | 'female' | 'other';
  phone: string;
  state: string;
  district: string;
  income: number;
  caste?: string;
  occupation?: string;
  landHolding?: number;
  familySize?: number;
  language: 'en' | 'hi' | 'mr';
  createdAt?: string;
  updatedAt?: string;
}

// Government Scheme
export interface Scheme {
  id: string;
  name: string;
  nameHindi?: string;
  nameMarathi?: string;
  description: string;
  category: string;
  benefits: string;
  estimatedBenefit?: string;
  eligibilityCriteria: string[];
  requiredDocuments: string[];
  applicationDeadline?: string;
  governmentDepartment: string;
  officialWebsite?: string;
}

// Eligibility Result
export interface EligibilityResult {
  profileId: string;
  eligibleSchemes: EligibleScheme[];
  processingTime: string;
  timestamp: string;
}

export interface EligibleScheme extends Scheme {
  eligibilityScore: number;
  matchedCriteria: string[];
  missingDocuments: string[];
}

// Document
export interface Document {
  id: string;
  profileId: string;
  type: DocumentType;
  fileName: string;
  fileUrl: string;
  status: 'pending' | 'verified' | 'rejected';
  ocrText?: string;
  uploadedAt: string;
  verifiedAt?: string;
}

export type DocumentType = 
  | 'aadhaar'
  | 'pan'
  | 'ration_card'
  | 'land_records'
  | 'income_certificate'
  | 'caste_certificate'
  | 'bank_passbook'
  | 'other';

// Application
export interface Application {
  id: string;
  profileId: string;
  schemeId: string;
  schemeName: string;
  status: ApplicationStatus;
  submittedAt: string;
  updatedAt: string;
  documents: string[];
  formData: Record<string, any>;
  trackingNumber?: string;
}

export type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'documents_verified'
  | 'approved'
  | 'rejected'
  | 'payment_processed';

// Application Tracking
export interface ApplicationTracking {
  applicationId: string;
  status: ApplicationStatus;
  history: TrackingEvent[];
  estimatedCompletionDate?: string;
}

export interface TrackingEvent {
  status: ApplicationStatus;
  timestamp: string;
  description: string;
  updatedBy?: string;
}

// Auth
export interface LoginRequest {
  phone: string;
}

export interface VerifyOTPRequest {
  phone: string;
  otp: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: UserProfile;
}

// API Response
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: number;
    message: string;
    details?: any;
  };
  timestamp: string;
}

// Form Data
export interface ProfileFormData {
  personalInfo: {
    name: string;
    age: number;
    gender: string;
    phone: string;
  };
  addressInfo: {
    state: string;
    district: string;
    village?: string;
    pincode?: string;
  };
  economicInfo: {
    income: number;
    occupation?: string;
    landHolding?: number;
  };
  familyInfo: {
    familySize?: number;
    dependents?: number;
  };
  otherInfo: {
    caste?: string;
    language: string;
  };
}

// Notification
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}
