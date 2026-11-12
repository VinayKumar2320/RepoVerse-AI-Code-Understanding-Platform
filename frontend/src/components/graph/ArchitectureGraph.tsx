'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  Node,
  Edge,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { ArchitectureGraphResponse, GraphNode } from '../../types';
import { Layers, Search, Filter, ZoomIn, ZoomOut, Maximize2, ExternalLink, Code } from 'lucide-react';

export const ArchitectureGraph: React.FC = () => {
  const { currentRepo, setSelectedFile } = useRepoStore();
  const [level, setLevel] = useState<number>(2);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const fetchGraph = useCallback(async () => {
    if (!currentRepo) return;
    setLoading(true);
    try {
      const data: ArchitectureGraphResponse = await api.getArchitectureGraph(currentRepo.id, level);

      // Simple grid / hierarchy layout calculation
      const cols = 5;
      const nodeDistanceX = 260;
      const nodeDistanceY = 140;

      const flowNodes: Node[] = data.nodes.map((n, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);

        let bgColor = '#1e293b';
        let borderColor = '#475569';
        let textColor = '#e2e8f0';

        if (n.entity_type === 'Package' || n.entity_type === 'Directory') {
          bgColor = '#1e1b4b';
          borderColor = '#6366f1';
          textColor = '#c7d2fe';
        } else if (n.entity_type === 'Endpoint') {
          bgColor = '#064e3b';
          borderColor = '#10b981';
          textColor = '#a7f3d0';
        } else if (n.entity_type === 'Class') {
          bgColor = '#3b0764';
          borderColor = '#a855f7';
          textColor = '#f3e8ff';
        } else if (n.entity_type === 'ExternalDependency') {
          bgColor = '#312e81';
          borderColor = '#818cf8';
          textColor = '#e0e7ff';
        }

        return {
          id: n.id,
          position: { x: col * nodeDistanceX + 40, y: row * nodeDistanceY + 40 },
          data: {
            label: (
              <div className="p-3 text-left w-52 overflow-hidden">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-black/40 text-slate-300">
                    {n.entity_type}
                  </span>
                  {n.file_path && (
                    <span className="text-[10px] text-slate-400 font-mono">
                      {n.file_path.split('.').pop()}
                    </span>
                  )}
                </div>
                <div className="font-semibold text-xs truncate" title={n.label}>
                  {n.label}
                </div>
                {n.file_path && (
                  <div className="text-[10px] text-slate-400 truncate mt-0.5" title={n.file_path}>
                    {n.file_path}
                  </div>
                )}
              </div>
            ),
            rawNode: n,
          },
          style: {
            background: bgColor,
            borderColor: borderColor,
            borderWidth: '1.5px',
            borderRadius: '8px',
            color: textColor,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
          },
        };
      });

      const edgeColors: Record<string, string> = {
        IMPORTS: '#818cf8',
        CALLS: '#34d399',
        DEFINES: '#64748b',
        CONTAINS: '#475569',
        DEPENDS_ON: '#a78bfa',
        INHERITS: '#f43f5e',
      };

      const flowEdges: Edge[] = data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.edge_type,
        animated: e.edge_type === 'CALLS',
        style: { stroke: edgeColors[e.edge_type] || '#64748b', strokeWidth: 1.5 },
        labelStyle: { fill: '#94a3b8', fontSize: 9, fontWeight: 500 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColors[e.edge_type] || '#64748b',
          width: 14,
          height: 14,
        },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (e) {
      console.error('Failed to load architecture graph:', e);
    } finally {
      setLoading(false);
    }
  }, [currentRepo, level, setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    if (node.data?.rawNode) {
      setSelectedNode(node.data.rawNode as GraphNode);
    }
  }, []);

  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) return nodes;
    const q = searchQuery.toLowerCase();
    return nodes.map((n) => {
      const match =
        (n.data?.rawNode as GraphNode)?.label.toLowerCase().includes(q) ||
        (n.data?.rawNode as GraphNode)?.file_path?.toLowerCase().includes(q);
      return {
        ...n,
        style: {
          ...n.style,
          opacity: match ? 1 : 0.2,
          borderWidth: match ? '3px' : '1px',
          borderColor: match ? '#38bdf8' : n.style?.borderColor,
        },
      };
    });
  }, [nodes, searchQuery]);

  return (
    <div className="flex h-[calc(100vh-140px)] w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
      {/* React Flow Canvas */}
      <div className="flex-1 relative h-full">
        {/* Controls Toolbar */}
        <div className="absolute top-4 left-4 z-10 flex items-center space-x-2 bg-slate-900/95 border border-slate-800 p-1.5 rounded-lg shadow-lg">
          {/* Level Switcher */}
          <div className="flex items-center space-x-1 border-r border-slate-800 pr-2 mr-1">
            <span className="text-xs text-slate-400 font-semibold px-2">Level:</span>
            {[
              { id: 1, label: 'Packages' },
              { id: 2, label: 'Modules' },
              { id: 3, label: 'Symbols' },
            ].map((lvl) => (
              <button
                key={lvl.id}
                onClick={() => setLevel(lvl.id)}
                className={`px-2.5 py-1 text-xs rounded-md font-medium transition ${
                  level === lvl.id
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search graph nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1 bg-slate-950 border border-slate-800 rounded-md text-xs text-slate-200 focus:outline-none focus:border-brand-500 w-44"
            />
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 z-10 bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg text-[10px] space-y-1 shadow-md">
          <div className="text-slate-400 font-bold uppercase tracking-wider mb-1">Edge Legend</div>
          <div className="flex items-center space-x-2"><span className="w-2.5 h-2.5 rounded-full bg-indigo-400 inline-block"></span><span className="text-slate-300">IMPORTS</span></div>
          <div className="flex items-center space-x-2"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span><span className="text-slate-300">CALLS</span></div>
          <div className="flex items-center space-x-2"><span className="w-2.5 h-2.5 rounded-full bg-purple-400 inline-block"></span><span className="text-slate-300">DEPENDS_ON</span></div>
        </div>

        {loading ? (
          <div className="h-full flex items-center justify-center text-slate-400 text-sm">
            Building graph...
          </div>
        ) : (
          <ReactFlow
            nodes={filteredNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            colorMode="dark"
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
            <Controls className="bg-slate-900 border border-slate-800 rounded-md text-slate-300 fill-slate-300" />
            <MiniMap
              className="bg-slate-900 border border-slate-800 rounded-md overflow-hidden"
              nodeColor={(n: any) => n.style?.borderColor || '#6366f1'}
            />
          </ReactFlow>
        )}
      </div>

      {/* Node Details Inspection Side Panel */}
      {selectedNode && (
        <div className="w-80 border-l border-slate-800 bg-slate-900 p-5 overflow-y-auto flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="px-2 py-0.5 text-[10px] uppercase font-bold rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                {selectedNode.entity_type}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-500 hover:text-slate-300 text-xs"
              >
                Close
              </button>
            </div>

            <div className="mt-4">
              <h4 className="text-base font-bold text-white break-all">{selectedNode.label}</h4>
              <p className="text-xs text-slate-400 font-mono mt-1 break-all">
                {selectedNode.qualified_name}
              </p>
            </div>

            {selectedNode.file_path && (
              <div className="mt-4 p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">
                  Source Location
                </span>
                <span className="text-xs font-mono text-indigo-300 break-all">
                  {selectedNode.file_path}
                </span>
              </div>
            )}

            {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
              <div className="mt-4">
                <span className="text-xs font-semibold text-slate-300 block mb-2">Properties</span>
                <div className="space-y-1.5 text-xs text-slate-400">
                  {selectedNode.metadata.loc && <div>LOC: <span className="text-slate-200">{selectedNode.metadata.loc}</span></div>}
                  {selectedNode.metadata.language && <div>Language: <span className="text-slate-200">{selectedNode.metadata.language}</span></div>}
                  {selectedNode.metadata.start_line && (
                    <div>Lines: <span className="text-slate-200">{selectedNode.metadata.start_line} - {selectedNode.metadata.end_line}</span></div>
                  )}
                  {selectedNode.metadata.docstring && (
                    <div className="mt-2 p-2 bg-slate-950 rounded text-slate-300 font-mono text-[11px]">
                      {selectedNode.metadata.docstring}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {selectedNode.file_path && (
            <button
              onClick={() => setSelectedFile(selectedNode.file_path!, selectedNode.metadata?.start_line)}
              className="w-full mt-6 py-2 px-3 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition shadow"
            >
              <Code className="w-3.5 h-3.5" />
              <span>Inspect Source Code</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};
