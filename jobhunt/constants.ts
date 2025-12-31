import { Job, Application, AnalyticsData, User, ResumeData } from './types';

export const CURRENT_USER: User = {
  id: 'u1',
  name: 'Alex Johnson',
  email: 'alex.j@example.com',
  role: 'Senior Frontend Engineer',
  avatar: 'https://picsum.photos/seed/alex/100/100',
  plan: 'pro'
};

export const MOCK_RESUME: ResumeData = {
  fileName: 'Alex_Johnson_Resume_2024.pdf',
  uploadedAt: '2024-12-20T10:00:00Z',
  skills: ['React', 'TypeScript', 'Tailwind CSS', 'Node.js', 'PostgreSQL', 'AWS', 'Next.js', 'GraphQL'],
  experience: [
    { role: 'Senior Frontend Engineer', company: 'TechFlow', duration: '2021 - Present' },
    { role: 'Frontend Developer', company: 'StartUp Inc', duration: '2019 - 2021' }
  ],
  education: [
    { degree: 'BS Computer Science', school: 'University of Tech', year: '2019' }
  ]
};

export const MOCK_JOBS: Job[] = [
  {
    id: 'j1',
    title: 'Senior Frontend Engineer',
    company: { name: 'Stripe', logo: 'https://picsum.photos/seed/stripe/50/50', location: 'San Francisco, CA', size: '5000+', website: 'stripe.com' },
    location: 'Remote (US)',
    type: 'full-time',
    salaryMin: 160000,
    salaryMax: 220000,
    postedAt: '2024-05-20T09:00:00Z',
    matchScore: 94,
    skills: ['React', 'TypeScript', 'GraphQL', 'Stripe API'],
    matchedSkills: [
      { name: 'React', match: true, years: 5 },
      { name: 'TypeScript', match: true, years: 4 },
      { name: 'GraphQL', match: true },
      { name: 'Stripe API', match: false }
    ],
    description: 'We are looking for a Senior Frontend Engineer to build the future of payments infrastructure.',
    requirements: ['5+ years of experience', 'Deep understanding of React internals', 'Experience with large scale apps'],
    benefits: ['Competitive equity', '100% Health coverage', 'Remote stipend'],
    isRemote: true,
    status: 'new'
  },
  {
    id: 'j2',
    title: 'Staff Engineer, Design Systems',
    company: { name: 'Vercel', logo: 'https://picsum.photos/seed/vercel/50/50', location: 'Remote', size: '500-1000', website: 'vercel.com' },
    location: 'Remote',
    type: 'full-time',
    salaryMin: 190000,
    salaryMax: 260000,
    postedAt: '2024-05-19T14:30:00Z',
    matchScore: 91,
    skills: ['React', 'Next.js', 'Accessibility', 'CSS'],
    matchedSkills: [
      { name: 'React', match: true, years: 5 },
      { name: 'Next.js', match: true, years: 3 },
      { name: 'CSS', match: true },
      { name: 'Accessibility', match: false }
    ],
    description: 'Join the team building the best developer experience on the web.',
    requirements: ['Experience maintaining open source projects', 'Deep CSS knowledge', 'System design skills'],
    benefits: ['Unlimited PTO', 'Home office setup', 'Learning budget'],
    isRemote: true,
    status: 'new'
  },
  {
    id: 'j3',
    title: 'Frontend Developer',
    company: { name: 'Linear', logo: 'https://picsum.photos/seed/linear/50/50', location: 'San Francisco, CA', size: '50-100', website: 'linear.app' },
    location: 'Hybrid',
    type: 'full-time',
    salaryMin: 140000,
    salaryMax: 180000,
    postedAt: '2024-05-18T10:00:00Z',
    matchScore: 88,
    skills: ['React', 'MobX', 'Electron', 'Performance'],
    matchedSkills: [
      { name: 'React', match: true },
      { name: 'MobX', match: false },
      { name: 'Electron', match: false },
      { name: 'Performance', match: true }
    ],
    description: 'Build the tool you use to build software.',
    requirements: ['Obsession with performance', 'Eye for design details'],
    benefits: ['Top tier gear', 'Company retreats'],
    isRemote: false,
    status: 'viewed'
  },
  {
    id: 'j4',
    title: 'Product Engineer',
    company: { name: 'Notion', logo: 'https://picsum.photos/seed/notion/50/50', location: 'New York, NY', size: '500+', website: 'notion.so' },
    location: 'New York, NY',
    type: 'full-time',
    salaryMin: 150000,
    salaryMax: 200000,
    postedAt: '2024-05-15T11:00:00Z',
    matchScore: 85,
    skills: ['React', 'Flow', 'SQLite'],
    matchedSkills: [
        { name: 'React', match: true },
        { name: 'Flow', match: false },
        { name: 'SQLite', match: true }
    ],
    description: 'Making tools for thought.',
    requirements: ['Full stack capabilities', 'Product sense'],
    benefits: ['Lunch provided', 'Wellness stipend'],
    isRemote: false,
    status: 'viewed'
  },
  {
    id: 'j5',
    title: 'Software Engineer, UI',
    company: { name: 'Airbnb', logo: 'https://picsum.photos/seed/airbnb/50/50', location: 'Remote', size: '5000+', website: 'airbnb.com' },
    location: 'Remote',
    type: 'contract',
    salaryMin: 130000,
    salaryMax: 170000,
    postedAt: '2024-05-21T08:00:00Z',
    matchScore: 78,
    skills: ['React', 'GraphQL', 'Apollo'],
    matchedSkills: [
        { name: 'React', match: true },
        { name: 'GraphQL', match: true },
        { name: 'Apollo', match: false }
    ],
    description: 'Belong anywhere.',
    requirements: ['Experience with Design Systems', 'Testing expertise'],
    benefits: ['Travel credit'],
    isRemote: true,
    status: 'new'
  }
];

export const MOCK_APPLICATIONS: Application[] = [
  {
    id: 'a1',
    jobId: 'j1',
    job: MOCK_JOBS[0],
    status: 'screening',
    appliedAt: '2024-05-15T10:00:00Z',
    updatedAt: '2024-05-18T14:00:00Z',
    notes: 'Recruiter reached out via email. Scheduled intro call.',
    nextStep: 'Phone Screen',
    nextStepDate: '2024-05-25T14:00:00Z'
  },
  {
    id: 'a2',
    jobId: 'j2',
    job: MOCK_JOBS[1],
    status: 'applied',
    appliedAt: '2024-05-20T09:00:00Z',
    updatedAt: '2024-05-20T09:00:00Z',
    notes: 'Applied with referral from Sarah.',
  },
  {
    id: 'a3',
    jobId: 'j3',
    job: MOCK_JOBS[2],
    status: 'saved',
    appliedAt: '',
    updatedAt: '2024-05-19T10:00:00Z',
    notes: 'Need to update resume for this one.',
  },
  {
    id: 'a4',
    jobId: 'j4',
    job: MOCK_JOBS[3],
    status: 'interview',
    appliedAt: '2024-05-10T10:00:00Z',
    updatedAt: '2024-05-21T11:00:00Z',
    notes: 'Technical round passed. Final onsite next week.',
    nextStep: 'Onsite Interview',
    nextStepDate: '2024-05-28T10:00:00Z'
  }
];

export const ANALYTICS_DATA: AnalyticsData = {
  applicationsOverTime: [
    { date: 'Mon', count: 2 },
    { date: 'Tue', count: 5 },
    { date: 'Wed', count: 3 },
    { date: 'Thu', count: 8 },
    { date: 'Fri', count: 4 },
    { date: 'Sat', count: 1 },
    { date: 'Sun', count: 0 },
  ],
  funnel: [
    { stage: 'Viewed', count: 234, fill: '#818CF8' },
    { stage: 'Saved', count: 47, fill: '#6366F1' },
    { stage: 'Applied', count: 28, fill: '#4F46E5' },
    { stage: 'Interview', count: 7, fill: '#4338CA' },
    { stage: 'Offer', count: 2, fill: '#3730A3' },
  ],
  skillsMatch: [
    { name: 'React', score: 95 },
    { name: 'TypeScript', score: 90 },
    { name: 'Node.js', score: 75 },
    { name: 'AWS', score: 45 },
    { name: 'Python', score: 30 },
  ]
};
