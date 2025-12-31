import React, { useRef, useCallback } from 'react';
import { FileText, UploadCloud, CheckCircle, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useResumeProfile, useUploadResume } from '../hooks';

const ResumeView: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { data: resume, isLoading, error } = useResumeProfile();
  const uploadMutation = useUploadResume();

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate({ file });
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [uploadMutation]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      uploadMutation.mutate({ file });
    }
  }, [uploadMutation]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="h-8 w-40 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" />
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <div className="h-20 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  const hasResume = resume && resume.fileName;

  return (
    <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">My Resume</h1>

        {/* Error Banner */}
        {(error || uploadMutation.isError) && (
          <div className="bg-red-50 dark:bg-red-900/10 p-4 rounded-xl border border-red-200 dark:border-red-900/20 flex items-start gap-3">
            <AlertCircle className="text-red-600 shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-semibold text-red-900 dark:text-red-200">Upload Error</h3>
              <p className="text-red-700 dark:text-red-300 text-sm mt-1">
                {uploadMutation.error?.message || error?.message || 'Failed to load resume profile'}
              </p>
            </div>
          </div>
        )}

        {/* Success Banner */}
        {uploadMutation.isSuccess && (
          <div className="bg-emerald-50 dark:bg-emerald-900/10 p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/20 flex items-start gap-3">
            <CheckCircle className="text-emerald-600 shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-semibold text-emerald-900 dark:text-emerald-200">Resume Uploaded!</h3>
              <p className="text-emerald-700 dark:text-emerald-300 text-sm mt-1">
                Your resume has been parsed and embedded. Job matches will now be personalized.
              </p>
            </div>
          </div>
        )}

        {/* Current Resume Card */}
        {hasResume && (
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-white mb-6">Current File</h2>
            <div className="flex items-center gap-4 p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg bg-zinc-50 dark:bg-zinc-900/50">
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 text-red-600 rounded-lg flex items-center justify-center shrink-0">
                <FileText size={24} />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-zinc-900 dark:text-white">{resume.fileName}</h3>
                <p className="text-sm text-zinc-500">
                  Uploaded on {resume.uploadedAt ? new Date(resume.uploadedAt).toLocaleDateString() : 'Unknown'}
                </p>
              </div>
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-sm font-medium">
                <CheckCircle size={16} />
                Parsed
              </div>
            </div>
          </div>
        )}

        {/* Parsing Status */}
        {hasResume && (
          <div className="bg-indigo-50 dark:bg-indigo-900/10 p-6 rounded-xl border border-indigo-100 dark:border-indigo-900/20">
            <div className="flex items-start gap-4">
              <div className="mt-1">
                <RefreshCw className="text-indigo-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-indigo-900 dark:text-indigo-200">AI Analysis Active</h3>
                <p className="text-indigo-700 dark:text-indigo-300 text-sm mt-1">
                  Your resume has been successfully embedded into our vector database. 
                  We are actively matching you against available jobs.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Extracted Data */}
        {hasResume && (
          <div className="bg-white dark:bg-[#18181B] p-6 rounded-xl border border-zinc-200 dark:border-zinc-800">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">Extracted Profile</h2>
            </div>
            
            <div className="space-y-8">
              {/* Skills */}
              <div>
                <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
                  Skills ({resume.skills?.length || 0})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {resume.skills && resume.skills.length > 0 ? (
                    resume.skills.map(skill => (
                      <span 
                        key={skill} 
                        className="px-3 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-full text-sm border border-zinc-200 dark:border-zinc-700"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-zinc-500 text-sm">No skills extracted yet</span>
                  )}
                </div>
              </div>

              {/* Experience */}
              {resume.experience && resume.experience.length > 0 && (
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
              )}

              {/* Education */}
              {resume.education && resume.education.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">Education</h3>
                  <div className="space-y-4">
                    {resume.education.map((edu, i) => (
                      <div key={i} className="pl-4 border-l-2 border-zinc-200 dark:border-zinc-800">
                        <h4 className="font-medium text-zinc-900 dark:text-white">{edu.degree}</h4>
                        <p className="text-sm text-zinc-500">{edu.school} • {edu.year}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Upload Area */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
        />
        <div 
          className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-colors cursor-pointer
          ${uploadMutation.isPending 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10' 
            : 'border-zinc-300 dark:border-zinc-700 hover:border-primary-500 dark:hover:border-primary-500'
          }`}
          onClick={handleUploadClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4">
            {uploadMutation.isPending ? (
              <Loader2 size={28} className="text-primary-500 animate-spin" />
            ) : (
              <UploadCloud size={28} className="text-zinc-400" />
            )}
          </div>
          <h3 className="font-medium text-zinc-900 dark:text-white mb-1">
            {uploadMutation.isPending 
              ? 'Uploading & Parsing...' 
              : hasResume 
                ? 'Upload New Resume' 
                : 'Upload Your Resume'
            }
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
