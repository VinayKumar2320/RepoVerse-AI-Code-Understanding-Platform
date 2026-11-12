import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    url: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(64), default="main")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    primary_language: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    snapshots: Mapped[List["RepositorySnapshot"]] = relationship("RepositorySnapshot", back_populates="repository", cascade="all, delete-orphan")
    jobs: Mapped[List["AnalysisJob"]] = relationship("AnalysisJob", back_populates="repository", cascade="all, delete-orphan")


class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True, nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    branch: Mapped[str] = mapped_column(String(64), default="main")
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    status: Mapped[str] = mapped_column(String(32), default="pending") # pending, analyzing, completed, failed
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    languages_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    overview_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="snapshots")
    files: Mapped[List["SourceFile"]] = relationship("SourceFile", back_populates="snapshot", cascade="all, delete-orphan")
    symbols: Mapped[List["CodeSymbol"]] = relationship("CodeSymbol", back_populates="snapshot", cascade="all, delete-orphan")
    graph_nodes: Mapped[List["GraphNode"]] = relationship("GraphNode", back_populates="snapshot", cascade="all, delete-orphan")
    graph_edges: Mapped[List["GraphEdge"]] = relationship("GraphEdge", back_populates="snapshot", cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True, nullable=False)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued") # queued, cloning, parsing, building_graph, completed, failed
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String(128), default="Job initiated")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="jobs")


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True, nullable=False)
    path: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(64), default="unknown")
    category: Mapped[str] = mapped_column(String(32), default="source") # source, test, config, doc, build, asset
    loc: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    snapshot: Mapped["RepositorySnapshot"] = relationship("RepositorySnapshot", back_populates="files")
    symbols: Mapped[List["CodeSymbol"]] = relationship("CodeSymbol", back_populates="file", cascade="all, delete-orphan")


class CodeSymbol(Base):
    __tablename__ = "code_symbols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True, nullable=False)
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_files.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    qualified_name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # function, method, class, module, endpoint, interface
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    snapshot: Mapped["RepositorySnapshot"] = relationship("RepositorySnapshot", back_populates="symbols")
    file: Mapped["SourceFile"] = relationship("SourceFile", back_populates="symbols")


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(128), primary_key=True) # canonical node key
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # Package, Directory, File, Module, Class, Function, Endpoint
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    qualified_name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1) # 1=Package/Boundary, 2=Module, 3=Symbol
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    snapshot: Mapped["RepositorySnapshot"] = relationship("RepositorySnapshot", back_populates="graph_nodes")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True, nullable=False)
    source_node_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    edge_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # CONTAINS, IMPORTS, CALLS, INHERITS, DEFINES, TESTS
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(32), default="statically_resolved") # observed_syntax, statically_resolved, inferred
    source_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    snapshot: Mapped["RepositorySnapshot"] = relationship("RepositorySnapshot", back_populates="graph_edges")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    symbol_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class QuestionHistory(Base):
    __tablename__ = "question_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True, nullable=False)
    experience_level: Mapped[str] = mapped_column(String(32), default="developer")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
