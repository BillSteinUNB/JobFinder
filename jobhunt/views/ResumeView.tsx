import React, { useState } from 'react';
import { useAppStore } from '../store';
import { FileText, UploadCloud, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

const ResumeView: React.FC = () => {
  const { resume } = useAppStore();
  const [isUploading, setIsUploading] = useState(false);
  
  const handleUpload = () => {
      setIsUploading(true);
      setTimeout(() => setIsUploading(false), 2000); // Simulate upload
  };

  return (
    <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">My Resume</h1>

            {/* Current Resume Card */}
            <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Current File</h2>
                <div className="flex items-center gap-4 p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-zinc-50 dark:bg-zinc-900/50">
                    <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 text-red-600 rounded-lg flex items-center justify-center shrink-0">
                        <FileText size={24} />
                    </div>
                    <div className="flex-1">
                        <h3 className="font-medium text-zinc-900 dark:text-white">{resume.fileName}</h3>
                        <p className="text-sm text-zinc-500">Uploaded on {new Date(resume.uploadedAt).toLocaleDateString()}</p>
                    </div>
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-sm font-medium">
                        <CheckCircle size={16} />
                        Parsed
                    </div>
                </div>
            </div>

            {/* Parsing Status */}
            <div className="bg-indigo-50 dark:bg-indigo-900/10 p-6 rounded-xl border border-indigo-100 dark:border-indigo-900/20">
                <div className="flex items-start gap-4">
                    <div className="mt-1">
                        <RefreshCw className="text-indigo-600 animate-spin-slow" size={20} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-indigo-900 dark:text-indigo-200">AI Analysis Active</h3>
                        <p className="text-indigo-700 dark:text-indigo-300 text-sm mt-1">
                            Your resume has been successfully embedded into our vector database. We are actively matching you against 234 new jobs.
                        </p>
                    </div>
                </div>
            </div>

            {/* Extracted Data */}
            <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Extracted Profile</h2>
                    <button className="text-sm text-primary-600 hover:text-primary-700">Edit Profile</button>
                </div>
                
                <div className="space-y-8">
                    {/* Skills */}
                    <div>
                        <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">Skills</h3>
                        <div className="flex flex-wrap gap-2">
                            {resume.skills.map(skill => (
                                <span key={skill} className="px-3 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-full text-sm border border-zinc-200 dark:border-zinc-700">
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Experience */}
                    <div>
                         <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">Experience</h3>
                         <div className="space-y-4">
                             {resume.experience.map((exp, i) => (
                                 <div key={i} className="pl-4 border-l-2 border-zinc-200 dark:border-zinc-800">
                                     <h4 className="font-medium text-zinc-900 dark:text-white">{exp.role}</h4>
                                     <p className="text-sm text-zinc-500">{exp.company} • {exp.duration}</p>
                                 </div>
                             ))}
                         </div>
                    </div>
                </div>
            </div>
            
            {/* Upload Area */}
            <div 
                className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-colors cursor-pointer
                ${isUploading ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10' : 'border-zinc-300 dark:border-zinc-700 hover:border-primary-500 dark:hover:border-primary-500'}`}
                onClick={handleUpload}
            >
                <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4">
                    <UploadCloud size={28} className="text-zinc-400" />
                </div>
                <h3 className="font-medium text-zinc-900 dark:text-white mb-1">
                    {isUploading ? 'Uploading...' : 'Upload New Resume'}
                </h3>
                <p className="text-sm text-zinc-500 max-w-sm">
                    Drag and drop your PDF here, or click to browse. Max 5MB.
                </p>
            </div>

        </div>
    </div>
  );
};

export default ResumeView;
