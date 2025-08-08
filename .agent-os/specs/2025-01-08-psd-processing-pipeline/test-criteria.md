# PSD Processing Pipeline - Test Criteria

## Unit Test Scenarios

### 1. Model Tests

#### Project Model Tests
```ruby
# spec/models/project_spec.rb
RSpec.describe Project, type: :model do
  describe '#processing_progress' do
    it 'returns 0 when no layers' do
      project = create(:project, total_layers_count: 0)
      expect(project.processing_progress).to eq(0)
    end
    
    it 'calculates correct percentage' do
      project = create(:project, 
        total_layers_count: 10, 
        processed_layers_count: 3
      )
      expect(project.processing_progress).to eq(30)
    end
  end
  
  describe 'status transitions' do
    it 'transitions from pending to processing' do
      project = create(:project, status: :pending)
      expect { project.processing! }.to change { project.status }
        .from('pending').to('processing')
    end
  end
end
```

#### Layer Model Tests
```ruby
# spec/models/layer_spec.rb
RSpec.describe Layer, type: :model do
  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_presence_of(:position) }
    it { should validate_numericality_of(:opacity).is_greater_than_or_equal_to(0).is_less_than_or_equal_to(1) }
  end
  
  describe 'metadata storage' do
    it 'stores PSD metadata as JSON' do
      layer = create(:layer, psd_metadata: { blend_mode: 'normal', locked: false })
      expect(layer.psd_metadata['blend_mode']).to eq('normal')
    end
  end
end
```

### 2. Service Tests

#### PsdProcessingService Tests
```ruby
# spec/services/psd_processing_service_spec.rb
RSpec.describe PsdProcessingService do
  describe '.extract_layers' do
    let(:project) { create(:project, :with_psd_file) }
    
    context 'with valid PSD' do
      before do
        stub_request(:post, "http://localhost:8001/api/extract_layers")
          .to_return(
            status: 200,
            body: { layers: [{ name: 'Layer 1', width: 100, height: 100 }] }.to_json
          )
      end
      
      it 'returns layer data' do
        result = described_class.extract_layers(project)
        expect(result).to be_an(Array)
        expect(result.first['name']).to eq('Layer 1')
      end
    end
    
    context 'with service error' do
      before do
        stub_request(:post, "http://localhost:8001/api/extract_layers")
          .to_return(status: 500, body: { error: 'Processing failed' }.to_json)
      end
      
      it 'raises PsdProcessingError' do
        expect { described_class.extract_layers(project) }
          .to raise_error(PsdProcessingService::PsdProcessingError)
      end
    end
  end
end
```

#### PsdProcessor Tests
```ruby
# spec/services/psd_processor_spec.rb
RSpec.describe PsdProcessor do
  let(:project) { create(:project, :with_psd_file) }
  let(:processor) { described_class.new(project) }
  
  describe '#execute' do
    before do
      allow(PsdProcessingService).to receive(:extract_layers).and_return([
        { 'name' => 'Layer 1', 'width' => 100, 'height' => 100, 'image_data' => 'base64data' }
      ])
    end
    
    it 'creates layers for each extracted layer' do
      expect { processor.execute }.to change { project.layers.count }.by(1)
    end
    
    it 'updates project status to completed' do
      processor.execute
      expect(project.reload.status).to eq('completed')
    end
    
    it 'broadcasts progress updates' do
      expect(ProjectChannel).to receive(:broadcast_to).at_least(:once)
      processor.execute
    end
    
    it 'creates processing logs' do
      expect { processor.execute }.to change { ProcessingLog.count }.by_at_least(3)
    end
  end
end
```

### 3. Job Tests

```ruby
# spec/jobs/process_psd_job_spec.rb
RSpec.describe ProcessPsdJob, type: :job do
  let(:project) { create(:project) }
  
  it 'calls PsdProcessor' do
    processor = instance_double(PsdProcessor)
    expect(PsdProcessor).to receive(:new).with(project).and_return(processor)
    expect(processor).to receive(:execute)
    
    described_class.perform_now(project.id)
  end
  
  context 'with errors' do
    it 'updates project status to failed' do
      allow(PsdProcessor).to receive(:new).and_raise(StandardError, 'Test error')
      
      described_class.perform_now(project.id)
      
      expect(project.reload.status).to eq('failed')
      expect(project.error_message).to eq('Test error')
    end
  end
end
```

## Integration Test Cases

### 1. API Integration Tests

```ruby
# spec/requests/api/v1/projects_spec.rb
RSpec.describe "Projects API", type: :request do
  describe "POST /api/v1/projects" do
    context "with PSD file" do
      let(:psd_file) { fixture_file_upload('test.psd', 'image/vnd.adobe.photoshop') }
      
      it "creates project and queues processing job" do
        expect {
          post api_v1_projects_path, params: {
            project: { name: 'Test Project', psd_file: psd_file }
          }
        }.to change { Project.count }.by(1)
          .and have_enqueued_job(ProcessPsdJob)
      end
    end
  end
  
  describe "GET /api/v1/projects/:id/processing_status" do
    let(:project) { create(:project, status: :processing, total_layers_count: 5, processed_layers_count: 2) }
    
    it "returns processing status" do
      get api_v1_project_processing_status_path(project)
      
      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']['progress']).to eq(40)
      expect(json['data']['attributes']['status']).to eq('processing')
    end
  end
end
```

### 2. WebSocket Integration Tests

```ruby
# spec/channels/project_channel_spec.rb
RSpec.describe ProjectChannel, type: :channel do
  let(:project) { create(:project) }
  
  it "successfully subscribes" do
    subscribe(project_id: project.id)
    expect(subscription).to be_confirmed
    expect(subscription).to have_stream_from("project:#{project.id}")
  end
  
  it "broadcasts progress updates" do
    subscribe(project_id: project.id)
    
    expect {
      ProjectChannel.broadcast_to(project, { event: 'progress_update', progress: 50 })
    }.to have_broadcasted_to("project:#{project.id}")
      .with(hash_including(event: 'progress_update', progress: 50))
  end
end
```

## End-to-End Test Flows

### 1. Complete PSD Processing Flow
```javascript
// e2e/psd-processing.spec.js
describe('PSD Processing', () => {
  it('processes PSD file from upload to completion', () => {
    // Login
    cy.visit('/login');
    cy.get('[data-cy=email]').type('demo@example.com');
    cy.get('[data-cy=password]').type('password123');
    cy.get('[data-cy=submit]').click();
    
    // Upload PSD
    cy.get('[data-cy=file-upload]').attachFile('test.psd');
    cy.get('[data-cy=project-name]').type('Test Project');
    cy.get('[data-cy=create-project]').click();
    
    // Verify processing starts
    cy.get('[data-cy=processing-status]').should('be.visible');
    cy.get('[data-cy=progress-bar]').should('exist');
    
    // Wait for completion
    cy.get('[data-cy=status]', { timeout: 30000 }).should('contain', 'completed');
    
    // Verify layers created
    cy.get('[data-cy=layer-list]').should('be.visible');
    cy.get('[data-cy=layer-item]').should('have.length.greaterThan', 0);
  });
});
```

### 2. Error Handling Flow
```javascript
describe('PSD Processing Errors', () => {
  it('handles corrupted PSD file', () => {
    cy.visit('/projects/new');
    cy.get('[data-cy=file-upload]').attachFile('corrupted.psd');
    cy.get('[data-cy=create-project]').click();
    
    cy.get('[data-cy=error-message]').should('contain', 'Invalid PSD file');
  });
  
  it('handles processing timeout', () => {
    cy.intercept('POST', '/api/v1/projects', { fixture: 'timeout-project.json' });
    
    cy.visit('/projects/new');
    cy.get('[data-cy=file-upload]').attachFile('large.psd');
    cy.get('[data-cy=create-project]').click();
    
    cy.get('[data-cy=status]', { timeout: 60000 }).should('contain', 'failed');
    cy.get('[data-cy=error-message]').should('contain', 'Processing timeout');
  });
});
```

## Performance Benchmarks

### 1. Processing Time Benchmarks
| File Size | Layers | Expected Time | Max Time |
|-----------|--------|---------------|----------|
| < 10MB | 1-5 | < 5s | 10s |
| 10-50MB | 5-20 | < 15s | 30s |
| 50-100MB | 20-50 | < 30s | 60s |
| 100-500MB | 50+ | < 120s | 300s |

### 2. Memory Usage Benchmarks
```ruby
# spec/performance/memory_spec.rb
RSpec.describe 'Memory Usage', type: :performance do
  it 'uses less than 500MB for 100MB PSD' do
    project = create(:project, :with_large_psd)
    
    memory_before = GetProcessMem.new.mb
    ProcessPsdJob.perform_now(project.id)
    memory_after = GetProcessMem.new.mb
    
    expect(memory_after - memory_before).to be < 500
  end
end
```

### 3. Concurrent Processing
```ruby
RSpec.describe 'Concurrent Processing', type: :performance do
  it 'handles 5 simultaneous uploads' do
    projects = create_list(:project, 5, :with_psd_file)
    
    elapsed = Benchmark.realtime do
      projects.each { |p| ProcessPsdJob.perform_later(p.id) }
      Timeout.timeout(60) { wait_for_jobs_to_finish }
    end
    
    expect(elapsed).to be < 60
    expect(projects.map(&:reload).map(&:status)).to all(eq('completed'))
  end
end
```

## Acceptance Criteria

### Feature: PSD Upload and Processing
```gherkin
Feature: PSD Upload and Processing
  As a user
  I want to upload PSD files
  So that layers can be extracted for mesh generation

  Scenario: Successful PSD upload
    Given I am logged in
    When I upload a valid PSD file
    Then I should see processing status
    And I should see real-time progress updates
    And layers should be extracted successfully
    
  Scenario: Invalid file upload
    Given I am logged in
    When I upload a non-PSD file
    Then I should see an error message
    And no processing should start
    
  Scenario: Large file handling
    Given I am logged in
    When I upload a 200MB PSD file
    Then processing should complete within 2 minutes
    And all layers should be extracted
    
  Scenario: Processing cancellation
    Given I have an upload in progress
    When I click cancel processing
    Then processing should stop
    And project status should be "cancelled"
```

### Feature: Real-time Updates
```gherkin
Feature: Real-time Progress Updates
  As a user
  I want to see real-time progress
  So I know the status of my upload

  Scenario: Progress bar updates
    Given I have uploaded a PSD file
    When processing starts
    Then I should see the progress bar at 0%
    And the progress bar should update in real-time
    And reach 100% when complete
    
  Scenario: Status log updates
    Given processing is in progress
    When each layer is processed
    Then I should see a new log entry
    And the timestamp should be current
```

## Test Data Requirements

### 1. Test PSD Files
- `test-small.psd` - 5MB, 3 layers
- `test-medium.psd` - 50MB, 10 layers  
- `test-large.psd` - 200MB, 50 layers
- `test-corrupted.psd` - Invalid file
- `test-empty.psd` - Valid but no layers

### 2. Test User Data
- Regular user account
- Admin user account
- User with storage quota exceeded
- User with multiple projects

### 3. Mock Responses
- Successful extraction response
- Failed extraction response
- Timeout response
- Progress callback responses

## Monitoring & Metrics

### 1. Success Metrics
- Processing success rate > 95%
- Average processing time < 30s for files under 100MB
- WebSocket connection stability > 99%
- Zero data loss during processing

### 2. Error Metrics
- Error rate < 5%
- Timeout rate < 1%
- Memory error rate < 0.1%
- Recovery success rate > 90%

### 3. Performance Metrics
- API response time p95 < 200ms
- WebSocket latency < 100ms
- Memory usage per job < 500MB
- CPU usage per job < 80%