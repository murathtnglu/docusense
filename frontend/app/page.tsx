'use client';

import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import CollectionPanel from '@/components/CollectionPanel';
import ChatInterface from '@/components/ChatInterface';
import { ingestAPI } from '@/lib/api';
import { Sparkles, Layers, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Home() {
  const [selectedCollection, setSelectedCollection] = useState<number | null>(null);
  const [activeJobs, setActiveJobs] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Poll for job status
  useEffect(() => {
    if (activeJobs.length === 0) return;

    const interval = setInterval(async () => {
      const stillActive: string[] = [];
      
      for (const jobId of activeJobs) {
        try {
          const response = await ingestAPI.getStatus(jobId);
          const status = response.data;
          
          if (status.status === 'completed') {
            toast.success(`Document ready for queries!`);
          } else if (status.status === 'failed') {
            toast.error(`Processing failed`);
          } else {
            stillActive.push(jobId);
          }
        } catch (error) {
          console.error('Failed to check job status:', error);
        }
      }
      
      setActiveJobs(stillActive);
    }, 2000);

    return () => clearInterval(interval);
  }, [activeJobs]);

  const handleUploadStart = (jobId: string) => {
    setActiveJobs((prev) => [...prev, jobId]);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <Toaster 
        position="top-center"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#fff',
            borderRadius: '12px',
          },
        }}
      />
      
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden`}>
        <div className="w-80 h-full bg-white/80 backdrop-blur-xl border-r border-slate-200/50 flex flex-col">
          {/* Logo */}
          <div className="p-6 border-b border-slate-200/50">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-cyan-500 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                  DocuSense
                </h1>
                <p className="text-xs text-slate-500">AI Document Intelligence</p>
              </div>
            </div>
          </div>

          {/* Collection Panel */}
          <div className="flex-1 overflow-y-auto">
            <CollectionPanel
              selectedId={selectedCollection}
              onSelect={setSelectedCollection}
              onUploadStart={handleUploadStart}
              activeJobs={activeJobs.length}
            />
          </div>

          {/* Stats */}
          <div className="p-4 border-t border-slate-200/50">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <Layers className="w-4 h-4 text-blue-600" />
                  <span className="text-xs text-slate-600">Collections</span>
                </div>
                <p className="text-lg font-bold text-slate-900 mt-1">3</p>
              </div>
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <Zap className="w-4 h-4 text-purple-600" />
                  <span className="text-xs text-slate-600">Queries</span>
                </div>
                <p className="text-lg font-bold text-slate-900 mt-1">24</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {!selectedCollection ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-md animate-slide-up">
              <div className="w-20 h-20 bg-gradient-to-tr from-blue-600 to-cyan-500 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-blue-500/25">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-slate-900 mb-3">
                Welcome to DocuSense
              </h2>
              <p className="text-slate-600 mb-8">
                Select a collection from the sidebar to start asking questions about your documents
              </p>
              <button
                onClick={() => setSidebarOpen(true)}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all"
              >
                Get Started
              </button>
            </div>
          </div>
        ) : (
          <ChatInterface 
            collectionId={selectedCollection}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
            sidebarOpen={sidebarOpen}
          />
        )}
      </div>
    </div>
  );
}