'use client';

import { useEffect, useState } from 'react';
import { collectionAPI, ingestAPI } from '@/lib/api';
import { Plus, FolderOpen, Upload, Link2, X, FileText, Activity, Check } from 'lucide-react';
import toast from 'react-hot-toast';

interface Collection {
  id: number;
  name: string;
  description: string;
  document_count: number;
}

interface Props {
  selectedId: number | null;
  onSelect: (id: number) => void;
  onUploadStart: (jobId: string) => void;
  activeJobs: number;
}

export default function CollectionPanel({ selectedId, onSelect, onUploadStart, activeJobs }: Props) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [uploadMode, setUploadMode] = useState<'file' | 'url' | null>(null);
  const [url, setUrl] = useState('');
  const [urlTitle, setUrlTitle] = useState('');

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      const response = await collectionAPI.list();
      setCollections(response.data);
      if (response.data.length > 0 && !selectedId) {
        onSelect(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to load collections:', error);
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    
    try {
      await collectionAPI.create({ name: newName, description: newDesc });
      setNewName('');
      setNewDesc('');
      setShowCreate(false);
      loadCollections();
      toast.success('Collection created!');
    } catch (error) {
      toast.error('Failed to create collection');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedId) return;

    try {
      const response = await ingestAPI.uploadFile(selectedId, file);
      toast.success(`Processing ${file.name}...`);
      onUploadStart(response.data.job_id);
      setUploadMode(null);
    } catch (error) {
      toast.error('Upload failed');
    }
  };

  const handleURLSubmit = async () => {
    if (!url.trim() || !urlTitle.trim() || !selectedId) return;

    try {
      const response = await ingestAPI.ingestURL({
        collection_id: selectedId,
        url,
        title: urlTitle,
      });
      toast.success('Processing URL...');
      onUploadStart(response.data.job_id);
      setUrl('');
      setUrlTitle('');
      setUploadMode(null);
    } catch (error) {
      toast.error('Failed to add URL');
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Collections Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-700">Collections</h3>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4 text-slate-600" />
          </button>
        </div>

        {showCreate && (
          <div className="mb-3 p-3 bg-slate-50 rounded-xl animate-slide-up">
            <input
              type="text"
              placeholder="Collection name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                className="flex-1 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {collections.map((collection) => (
            <button
              key={collection.id}
              onClick={() => onSelect(collection.id)}
              className={`w-full text-left p-3 rounded-xl transition-all relative ${
                selectedId === collection.id
                  ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-2 border-blue-200 shadow-sm'
                  : 'hover:bg-slate-50 border-2 border-transparent'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className={`mt-0.5 ${selectedId === collection.id ? 'text-blue-600' : 'text-slate-400'}`}>
                  <FolderOpen className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900 text-sm">{collection.name}</p>
                  {collection.description && (
                    <p className="text-xs text-slate-500 mt-0.5">{collection.description}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-600">
                      <FileText className="w-3 h-3" />
                      {collection.document_count} {collection.document_count === 1 ? 'doc' : 'docs'}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Upload Section */}
      {selectedId && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">Add Documents</h3>
            {activeJobs > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-blue-600">
                <Activity className="w-3 h-3 animate-pulse" />
                {activeJobs} processing
              </div>
            )}
          </div>

          {!uploadMode ? (
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setUploadMode('file')}
                className="p-3 bg-slate-50 hover:bg-slate-100 rounded-lg transition-all group card-hover"
              >
                <Upload className="w-5 h-5 text-slate-600 group-hover:text-blue-600 mx-auto mb-1 transition-colors" />
                <span className="text-xs text-slate-600 group-hover:text-slate-900">Upload File</span>
              </button>
              <button
                onClick={() => setUploadMode('url')}
                className="p-3 bg-slate-50 hover:bg-slate-100 rounded-lg transition-all group card-hover"
              >
                <Link2 className="w-5 h-5 text-slate-600 group-hover:text-blue-600 mx-auto mb-1 transition-colors" />
                <span className="text-xs text-slate-600 group-hover:text-slate-900">Add URL</span>
              </button>
            </div>
          ) : uploadMode === 'file' ? (
            <div className="p-3 bg-slate-50 rounded-xl animate-slide-up">
              <label className="block cursor-pointer">
                <div className="p-6 border-2 border-dashed border-slate-300 rounded-lg hover:border-blue-400 hover:bg-white transition-all text-center group">
                  <Upload className="w-8 h-8 text-slate-400 group-hover:text-blue-500 mx-auto mb-2 transition-colors" />
                  <p className="text-sm text-slate-600 group-hover:text-slate-900">Click to select file</p>
                  <p className="text-xs text-slate-400 mt-1">PDF, TXT, MD</p>
                </div>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="hidden"
                  accept=".pdf,.txt,.md"
                />
              </label>
              <button
                onClick={() => setUploadMode(null)}
                className="w-full mt-2 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="p-3 bg-slate-50 rounded-xl animate-slide-up">
              <input
                type="text"
                placeholder="Page title"
                value={urlTitle}
                onChange={(e) => setUrlTitle(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2 transition-all"
              />
              <input
                type="url"
                placeholder="https://..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2 transition-all"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleURLSubmit}
                  disabled={!url.trim() || !urlTitle.trim()}
                  className="flex-1 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Add URL
                </button>
                <button
                  onClick={() => setUploadMode(null)}
                  className="px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Processing Indicator */}
          {activeJobs > 0 && (
            <div className="mt-3 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200 animate-pulse">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-ping"></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <span className="text-sm font-medium text-blue-700">Processing documents...</span>
              </div>
              <p className="text-xs text-blue-600 mt-1">This may take a few moments</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}