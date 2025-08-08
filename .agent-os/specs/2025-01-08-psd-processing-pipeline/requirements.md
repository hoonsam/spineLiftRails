# PSD Processing Pipeline Requirements

## Overview
Complete the PSD file processing pipeline to enable automatic layer extraction and mesh generation when users upload PSD files.

## Functional Requirements

### 1. PSD Upload Processing
- **FR1.1**: System shall accept PSD file uploads up to 500MB
- **FR1.2**: System shall validate PSD file format before processing
- **FR1.3**: System shall extract all visible layers from PSD file
- **FR1.4**: System shall preserve layer names, positions, and hierarchy
- **FR1.5**: System shall save extracted layer images as PNG files

### 2. Background Processing
- **FR2.1**: PSD processing shall run asynchronously using background jobs
- **FR2.2**: System shall update project status during processing (pending → processing → completed/failed)
- **FR2.3**: System shall handle processing failures gracefully with error messages
- **FR2.4**: System shall support processing cancellation

### 3. Layer Management
- **FR3.1**: System shall create Layer records for each extracted layer
- **FR3.2**: System shall attach layer images using Active Storage
- **FR3.3**: System shall maintain layer order/position from PSD
- **FR3.4**: System shall store layer metadata (bounds, opacity, blend mode)

### 4. Progress Tracking
- **FR4.1**: System shall report processing progress in real-time
- **FR4.2**: Progress updates shall include current step and percentage
- **FR4.3**: System shall broadcast updates via WebSocket to connected clients

### 5. Error Handling
- **FR5.1**: System shall validate file integrity before processing
- **FR5.2**: System shall handle corrupted PSD files gracefully
- **FR5.3**: System shall retry failed operations up to 3 times
- **FR5.4**: System shall log all errors with context for debugging

## Non-Functional Requirements

### Performance
- **NFR1.1**: PSD extraction shall complete within 30 seconds for files up to 100MB
- **NFR1.2**: System shall process multiple PSDs concurrently (up to 5)
- **NFR1.3**: Memory usage shall not exceed 1GB per PSD processing job

### Reliability
- **NFR2.1**: System shall maintain 99% success rate for valid PSD files
- **NFR2.2**: Failed jobs shall not affect other concurrent jobs
- **NFR2.3**: System shall recover from Python service crashes

### Scalability
- **NFR3.1**: Architecture shall support horizontal scaling of workers
- **NFR3.2**: System shall queue jobs when workers are busy
- **NFR3.3**: Performance shall degrade gracefully under load

### Security
- **NFR4.1**: Uploaded files shall be scanned for malicious content
- **NFR4.2**: Temporary files shall be cleaned up after processing
- **NFR4.3**: File access shall be restricted to authorized users

## Constraints

### Technical Constraints
- **TC1**: Must use existing Python service for PSD processing
- **TC2**: Must integrate with Rails Active Storage
- **TC3**: Must use Redis for job queuing (currently missing)
- **TC4**: Must maintain compatibility with psd-tools library

### Business Constraints
- **BC1**: Must maintain existing API contract
- **BC2**: Cannot break existing frontend functionality
- **BC3**: Must complete implementation within 1 week

## Assumptions

1. Redis will be installed and configured
2. Python service is running and accessible
3. Sufficient disk space for temporary files
4. Network connectivity between Rails and Python service
5. Users have modern browsers supporting WebSockets

## Dependencies

### External Dependencies
- Redis server for Sidekiq
- Python FastAPI service
- psd-tools Python library
- Active Storage configured

### Internal Dependencies
- User authentication system
- Project model and controller
- Layer model and associations
- WebSocket infrastructure

## Acceptance Criteria

1. User can upload PSD file and see processing status
2. Layers are automatically extracted and saved
3. Progress updates appear in real-time
4. Failed uploads show meaningful error messages
5. System handles concurrent uploads smoothly
6. All extracted layers are viewable in the UI