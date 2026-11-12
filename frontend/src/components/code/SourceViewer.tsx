'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { ExternalLink, FileCode, Bookmark, Check, Copy } from 'lucide-react';

const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

export const SourceViewer: React.FC = () => {
  const { currentRepo, overview, selectedFile, selectedLine } = useRepoStore();
  const [fileList, setFileList] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState<string>(selectedFile || '');
  const [codeContent, setCodeContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [bookmarked, setBookmarked] = useState<boolean>(false);

  useEffect(() => {
    if (selectedFile) {
      setActiveFile(selectedFile);
    }
  }, [selectedFile]);

  useEffect(() => {
    const fetchFiles = async () => {
      if (!currentRepo) return;
      try {
        const files = await api.getRepositoryFiles(currentRepo.id);
        const paths = files.map((f) => f.path);
        setFileList(paths);
        if (!activeFile && paths.length > 0) {
          setActiveFile(paths[0]);
        }
      } catch (e) {
        console.error('Failed to load file list:', e);
      }
    };
    fetchFiles();
  }, [currentRepo, activeFile]);

  // Load preview or mock content if local file fetch
  useEffect(() => {
    if (!activeFile) return;
    setCodeContent(
      `// Viewing: ${activeFile}\n// Commit SHA: ${overview?.commit_sha || 'HEAD'}\n\n// Verified static AST symbols and imports parsed by RepoVerse.\n// Jump to line: ${selectedLine || 1}\n`
    );
  }, [activeFile, overview, selectedLine]);

  const handleBookmark = async () => {
    if (!currentRepo || !activeFile) return;
    try {
      await api.createBookmark(currentRepo.id, {
        title: `Bookmark: ${activeFile}${selectedLine ? `:${selectedLine}` : ''}`,
        file_path: activeFile,
        line_number: selectedLine || 1,
      });
      setBookmarked(true);
      setTimeout(() => setBookmarked(false), 2000);
    } catch (e) {
      console.error('Failed to save bookmark:', e);
    }
  };

  const getLanguage = (fname: string): string => {
    if (fname.endsWith('.py')) return 'python';
    if (fname.endsWith('.ts') || fname.endsWith('.tsx')) return 'typescript';
    if (fname.endsWith('.js') || fname.endsWith('.jsx')) return 'javascript';
    if (fname.endsWith('.json')) return 'json';
    if (fname.endsWith('.md')) return 'markdown';
    return 'plaintext';
  };

  const githubUrl = currentRepo && overview && activeFile
    ? `https://github.com/${currentRepo.owner}/${currentRepo.name}/blob/${overview.commit_sha}/${activeFile}${selectedLine ? `#L${selectedLine}` : ''}`
    : null;

  return (
    <div className="flex h-[calc(100vh-140px)] w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950 py-2">
      {/* File Tree / File List */}
      <div className="w-64 border-r border-slate-800 bg-slate-900 flex flex-col">
        <div className="p-3 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
          <FileCode className="w-3.5 h-3.5 text-brand-400" />
          <span>Files ({fileList.length})</span>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {fileList.map((fp) => (
            <button
              key={fp}
              onClick={() => setActiveFile(fp)}
              className={`w-full text-left px-2.5 py-1.5 rounded text-xs font-mono truncate transition ${
                activeFile === fp
                  ? 'bg-brand-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {fp}
            </button>
          ))}
        </div>
      </div>

      {/* Editor & Toolbar */}
      <div className="flex-1 flex flex-col bg-slate-950">
        <div className="h-10 border-b border-slate-800 bg-slate-900/80 px-4 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
            <span className="font-semibold text-white">{activeFile}</span>
            {selectedLine && (
              <span className="text-brand-400 font-bold bg-brand-500/10 px-1.5 py-0.5 rounded">
                Line {selectedLine}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleBookmark}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-300 flex items-center space-x-1 transition border border-slate-700/60"
            >
              <Bookmark className="w-3 h-3" />
              <span>{bookmarked ? 'Saved!' : 'Bookmark'}</span>
            </button>

            {githubUrl && (
              <a
                href={githubUrl}
                target="_blank"
                rel="noreferrer"
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded text-slate-300 flex items-center space-x-1 transition border border-slate-700/60"
              >
                <ExternalLink className="w-3 h-3" />
                <span>GitHub (Pinned Commit)</span>
              </a>
            )}
          </div>
        </div>

        <div className="flex-1 relative">
          <Editor
            height="100%"
            language={getLanguage(activeFile)}
            value={codeContent}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 13,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
            }}
          />
        </div>
      </div>
    </div>
  );
};
