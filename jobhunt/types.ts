export type ViewState = 'dashboard' | 'search' | 'resume' | 'applications' | 'analytics' | 'settings';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar: string;
  plan: 'free' | 'pro';
}

export type JobType = 'full-time' | 'part-time' | 'contract' | 'internship';
export type ExperienceLevel = 'entry' | 'mid' | 'senior' | 'staff' | 'lead';

export interface Company {
  name: string;
  logo: string;
  location: string;
  size: string;
  website: string;
}

export interface MatchedSkill {
  name: string;
  match: boolean;
  years?: number;
}

export interface Job {
  id: string;
  title: string;
  company: Company;
  location: string;
  type: JobType;
  salaryMin: number;
  salaryMax: number;
  postedAt: string; // ISO date
  matchScore: number;
  skills: string[];
  matchedSkills: MatchedSkill[];
  description: string;
  requirements: string[];
  benefits: string[];
  isRemote: boolean;
  status?: 'new' | 'viewed';
  // Additional fields from API
  url?: string;
  category?: string;
  explanation?: string;
  breakdown?: Record<string, number>;
}

export type ApplicationStatus = 'saved' | 'applied' | 'screening' | 'interview' | 'offer' | 'rejected';

export interface Application {
  id: string;
  jobId: string;
  job: Job;
  status: ApplicationStatus;
  appliedAt: string;
  updatedAt: string;
  notes: string;
  nextStep?: string;
  nextStepDate?: string;
}

export interface ResumeData {
  fileName: string | null;
  uploadedAt: string | null;
  skills: string[];
  experience: { role: string; company: string; duration: string }[];
  education: { degree: string; school: string; year: string }[];
  preferredLocation?: string | null;
  minSalary?: number | null;
}

export interface AnalyticsData {
  applicationsOverTime: { date: string; count: number }[];
  funnel: { stage: string; count: number; fill: string }[];
  skillsMatch: { name: string; score: number }[];
  totalJobs?: number;
  totalApplications?: number;
  avgMatchScore?: number;
}
