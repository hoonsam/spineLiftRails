# Parameter Validation and Optimization Specification

## Overview

This document specifies the parameter validation system for mesh generation, including validation rules, optimization strategies, and preset management.

## Parameter Structure

### Core Parameters

```ruby
# app/models/mesh_parameters.rb
class MeshParameters
  include ActiveModel::Model
  include ActiveModel::Validations
  
  PARAMETERS = {
    detail_factor: {
      type: :float,
      range: 0.001..0.050,
      default: 0.01,
      description: "Controls mesh detail level. Lower values preserve more detail.",
      ui_step: 0.001
    },
    alpha_threshold: {
      type: :integer,
      range: 0..255,
      default: 10,
      description: "Minimum alpha value to consider a pixel opaque.",
      ui_step: 5
    },
    concave_factor: {
      type: :float,
      range: 0.0..100.0,
      default: 0.0,
      description: "Preserves concave shapes. Higher values maintain more concavity.",
      ui_step: 5.0
    },
    internal_vertex_density: {
      type: :integer,
      range: 0..100,
      default: 0,
      description: "Density of internal vertices. 0 disables internal vertices.",
      ui_step: 5
    },
    blur_kernel_size: {
      type: :integer,
      range: 1..21,
      default: 1,
      description: "Blur kernel size for mask smoothing. Must be odd.",
      ui_step: 2,
      validator: :validate_odd_number
    },
    binary_threshold: {
      type: :integer,
      range: 0..255,
      default: 128,
      description: "Threshold for binary mask conversion.",
      ui_step: 10
    },
    min_contour_area: {
      type: :float,
      range: 1..1000,
      default: 10,
      description: "Minimum contour area to consider.",
      ui_step: 5
    },
    density_scaling_factor: {
      type: :float,
      range: 100..10000,
      default: 1000.0,
      description: "Scaling factor for vertex density calculation.",
      ui_step: 100
    },
    min_triangle_area: {
      type: :float,
      range: 0.1..100,
      default: 1.0,
      description: "Minimum triangle area in the mesh.",
      ui_step: 0.1
    }
  }.freeze
  
  # Define attributes dynamically
  PARAMETERS.each_key do |param|
    attr_accessor param
  end
  
  # Dynamic validations
  PARAMETERS.each do |param, config|
    validates param, 
      presence: true,
      numericality: {
        greater_than_or_equal_to: config[:range].min,
        less_than_or_equal_to: config[:range].max
      }
    
    # Add custom validator if specified
    if config[:validator]
      validate config[:validator]
    end
  end
  
  def initialize(params = {})
    # Set defaults
    PARAMETERS.each do |param, config|
      value = params[param] || config[:default]
      send("#{param}=", cast_value(value, config[:type]))
    end
  end
  
  def to_h
    PARAMETERS.keys.each_with_object({}) do |param, hash|
      hash[param] = send(param)
    end
  end
  
  private
  
  def cast_value(value, type)
    case type
    when :float
      value.to_f
    when :integer
      value.to_i
    else
      value
    end
  end
  
  def validate_odd_number
    if blur_kernel_size.present? && blur_kernel_size.even?
      self.blur_kernel_size += 1
    end
  end
end
```

### Parameter Presets

```ruby
# app/models/mesh_parameter_preset.rb
class MeshParameterPreset < ApplicationRecord
  belongs_to :user, optional: true
  
  validates :name, presence: true, uniqueness: { scope: :user_id }
  validates :parameters, presence: true
  
  scope :global, -> { where(user_id: nil, is_default: true) }
  scope :for_user, ->(user) { where(user: user).or(global) }
  
  # Default presets
  SYSTEM_PRESETS = [
    {
      name: 'High Detail',
      description: 'Maximum detail preservation for complex shapes',
      parameters: {
        detail_factor: 0.005,
        alpha_threshold: 5,
        concave_factor: 80.0,
        internal_vertex_density: 50,
        blur_kernel_size: 1,
        binary_threshold: 128,
        min_contour_area: 5,
        density_scaling_factor: 2000.0,
        min_triangle_area: 0.5
      }
    },
    {
      name: 'Balanced',
      description: 'Good balance between quality and performance',
      parameters: {
        detail_factor: 0.01,
        alpha_threshold: 10,
        concave_factor: 40.0,
        internal_vertex_density: 20,
        blur_kernel_size: 3,
        binary_threshold: 128,
        min_contour_area: 10,
        density_scaling_factor: 1000.0,
        min_triangle_area: 1.0
      }
    },
    {
      name: 'Performance',
      description: 'Optimized for fast processing and smaller file size',
      parameters: {
        detail_factor: 0.02,
        alpha_threshold: 20,
        concave_factor: 0.0,
        internal_vertex_density: 0,
        blur_kernel_size: 5,
        binary_threshold: 140,
        min_contour_area: 20,
        density_scaling_factor: 500.0,
        min_triangle_area: 2.0
      }
    },
    {
      name: 'Simple Shapes',
      description: 'For basic geometric shapes and icons',
      parameters: {
        detail_factor: 0.03,
        alpha_threshold: 50,
        concave_factor: 0.0,
        internal_vertex_density: 0,
        blur_kernel_size: 7,
        binary_threshold: 160,
        min_contour_area: 50,
        density_scaling_factor: 300.0,
        min_triangle_area: 5.0
      }
    }
  ].freeze
  
  def self.seed_defaults!
    SYSTEM_PRESETS.each do |preset_data|
      find_or_create_by!(
        name: preset_data[:name],
        user_id: nil,
        is_default: true
      ) do |preset|
        preset.description = preset_data[:description]
        preset.parameters = preset_data[:parameters]
      end
    end
  end
  
  def apply_to(mesh_parameters)
    parameters.each do |key, value|
      mesh_parameters.send("#{key}=", value) if mesh_parameters.respond_to?("#{key}=")
    end
    mesh_parameters
  end
end
```

## Validation Service

```ruby
# app/services/mesh/parameter_validation_service.rb
module Mesh
  class ParameterValidationService
    attr_reader :parameters, :image
    
    def initialize(parameters, image: nil)
      @parameters = parameters
      @image = image
    end
    
    def validate!
      # Basic parameter validation
      mesh_params = MeshParameters.new(parameters)
      
      unless mesh_params.valid?
        raise ValidationError, format_errors(mesh_params.errors)
      end
      
      # Image-specific validation if provided
      if image
        validate_for_image!(mesh_params)
      end
      
      # Optimize parameters
      optimized = optimize_parameters(mesh_params)
      
      optimized.to_h
    end
    
    private
    
    def validate_for_image!(mesh_params)
      # Adjust parameters based on image characteristics
      if image_too_large?
        recommend_performance_settings(mesh_params)
      elsif image_has_transparency?
        validate_alpha_settings(mesh_params)
      end
    end
    
    def image_too_large?
      return false unless image
      
      image.width > 2048 || image.height > 2048
    end
    
    def image_has_transparency?
      return false unless image
      
      # Check if image has alpha channel
      image.metadata[:channels] == 4
    end
    
    def recommend_performance_settings(mesh_params)
      if mesh_params.internal_vertex_density > 30
        add_warning(
          "Large image detected. Consider reducing internal_vertex_density to improve performance."
        )
      end
      
      if mesh_params.detail_factor < 0.01
        add_warning(
          "Large image with high detail may result in slow processing."
        )
      end
    end
    
    def validate_alpha_settings(mesh_params)
      if mesh_params.alpha_threshold > 200
        add_warning(
          "High alpha threshold may exclude semi-transparent areas."
        )
      end
    end
    
    def optimize_parameters(mesh_params)
      optimized = mesh_params.dup
      
      # Auto-adjust blur kernel to be odd
      if optimized.blur_kernel_size.even?
        optimized.blur_kernel_size += 1
      end
      
      # Adjust density based on detail factor
      if optimized.detail_factor < 0.005 && optimized.internal_vertex_density == 0
        optimized.internal_vertex_density = 10
        add_info("Added internal vertices for high detail mesh")
      end
      
      optimized
    end
    
    def format_errors(errors)
      errors.full_messages.join(', ')
    end
    
    def add_warning(message)
      @warnings ||= []
      @warnings << message
    end
    
    def add_info(message)
      @info ||= []
      @info << message
    end
  end
end
```

## Parameter Optimization Engine

```ruby
# app/services/mesh/parameter_optimizer.rb
module Mesh
  class ParameterOptimizer
    attr_reader :image, :target
    
    OPTIMIZATION_TARGETS = {
      quality: {
        vertex_budget: nil,
        triangle_budget: nil,
        priority: :detail
      },
      balanced: {
        vertex_budget: 1000,
        triangle_budget: 2000,
        priority: :balanced
      },
      performance: {
        vertex_budget: 500,
        triangle_budget: 1000,
        priority: :speed
      },
      mobile: {
        vertex_budget: 300,
        triangle_budget: 600,
        priority: :size
      }
    }.freeze
    
    def initialize(image, target: :balanced)
      @image = image
      @target = OPTIMIZATION_TARGETS[target] || OPTIMIZATION_TARGETS[:balanced]
    end
    
    def optimize
      base_params = analyze_image
      
      case target[:priority]
      when :detail
        optimize_for_quality(base_params)
      when :speed
        optimize_for_performance(base_params)
      when :size
        optimize_for_size(base_params)
      else
        optimize_balanced(base_params)
      end
    end
    
    private
    
    def analyze_image
      analyzer = ImageAnalyzer.new(image)
      
      {
        has_transparency: analyzer.has_transparency?,
        complexity: analyzer.shape_complexity,
        edge_density: analyzer.edge_density,
        dominant_features: analyzer.dominant_features
      }
    end
    
    def optimize_for_quality(analysis)
      params = MeshParameters.new
      
      # Maximum detail preservation
      params.detail_factor = case analysis[:complexity]
                            when :high then 0.003
                            when :medium then 0.005
                            else 0.008
                            end
      
      # Preserve concave shapes
      params.concave_factor = analysis[:edge_density] > 0.7 ? 80.0 : 60.0
      
      # Add internal vertices for smooth deformation
      params.internal_vertex_density = 30
      
      # Minimal smoothing
      params.blur_kernel_size = 1
      
      params
    end
    
    def optimize_for_performance(analysis)
      params = MeshParameters.new
      
      # Reduce detail for speed
      params.detail_factor = 0.02
      
      # Skip concave preservation
      params.concave_factor = 0.0
      
      # No internal vertices
      params.internal_vertex_density = 0
      
      # Aggressive smoothing
      params.blur_kernel_size = 7
      
      # Higher thresholds
      params.min_contour_area = 50
      params.min_triangle_area = 5.0
      
      params
    end
    
    def optimize_balanced(analysis)
      params = MeshParameters.new
      
      # Adaptive detail based on complexity
      params.detail_factor = lerp(0.008, 0.015, analysis[:complexity_score])
      
      # Moderate concave preservation
      params.concave_factor = analysis[:has_concave_shapes] ? 40.0 : 20.0
      
      # Limited internal vertices
      params.internal_vertex_density = 
        target[:vertex_budget] ? calculate_density_for_budget : 15
      
      params
    end
    
    def calculate_density_for_budget
      # Estimate vertices from image size and detail
      estimated_boundary = image.perimeter * 0.1
      remaining_budget = target[:vertex_budget] - estimated_boundary
      
      # Convert to density parameter
      (remaining_budget / (image.width * image.height) * 1000).clamp(0, 50)
    end
    
    def lerp(min, max, t)
      min + (max - min) * t.clamp(0, 1)
    end
  end
end
```

## Validation UI Components

```ruby
# app/components/mesh_parameter_form_component.rb
class MeshParameterFormComponent < ViewComponent::Base
  def initialize(parameters:, presets: [], image: nil)
    @parameters = parameters
    @presets = presets
    @image = image
  end
  
  private
  
  def parameter_field(param_name)
    config = MeshParameters::PARAMETERS[param_name]
    
    tag.div(class: "parameter-field", data: { parameter: param_name }) do
      safe_join([
        label_tag(param_name, config[:description]),
        parameter_input(param_name, config),
        parameter_preview(param_name, config)
      ])
    end
  end
  
  def parameter_input(param_name, config)
    case config[:type]
    when :float
      range_field_tag(
        param_name,
        @parameters.send(param_name),
        min: config[:range].min,
        max: config[:range].max,
        step: config[:ui_step],
        class: "parameter-slider",
        data: {
          action: "change->mesh-parameters#updateValue",
          target: "mesh-parameters.#{param_name}"
        }
      )
    when :integer
      number_field_tag(
        param_name,
        @parameters.send(param_name),
        min: config[:range].min,
        max: config[:range].max,
        step: config[:ui_step],
        class: "parameter-input"
      )
    end
  end
  
  def parameter_preview(param_name, config)
    tag.div(class: "parameter-preview") do
      tag.span(@parameters.send(param_name), class: "current-value")
    end
  end
end
```

## Validation API Endpoint

```ruby
# app/controllers/api/v1/mesh_parameters_controller.rb
module Api
  module V1
    class MeshParametersController < ApiController
      def validate
        validator = Mesh::ParameterValidationService.new(
          params[:parameters],
          image: find_image
        )
        
        result = validator.validate!
        
        render json: {
          valid: true,
          parameters: result,
          warnings: validator.warnings,
          info: validator.info
        }
      rescue Mesh::ValidationError => e
        render json: {
          valid: false,
          errors: e.message
        }, status: :unprocessable_entity
      end
      
      def optimize
        optimizer = Mesh::ParameterOptimizer.new(
          find_image,
          target: params[:target]&.to_sym || :balanced
        )
        
        optimized_params = optimizer.optimize
        
        render json: {
          parameters: optimized_params.to_h,
          estimated_vertices: optimizer.estimated_vertices,
          estimated_triangles: optimizer.estimated_triangles,
          processing_time: optimizer.estimated_time
        }
      end
      
      private
      
      def find_image
        return nil unless params[:image_id]
        
        current_user.images.find(params[:image_id])
      end
    end
  end
end
```

## Testing Strategy

```ruby
# spec/services/mesh/parameter_validation_service_spec.rb
RSpec.describe Mesh::ParameterValidationService do
  describe '#validate!' do
    context 'with valid parameters' do
      let(:params) { { detail_factor: 0.01, alpha_threshold: 10 } }
      
      it 'returns validated parameters' do
        result = described_class.new(params).validate!
        
        expect(result[:detail_factor]).to eq(0.01)
        expect(result[:alpha_threshold]).to eq(10)
      end
    end
    
    context 'with out-of-range parameters' do
      let(:params) { { detail_factor: 0.1 } } # Too high
      
      it 'raises validation error' do
        expect {
          described_class.new(params).validate!
        }.to raise_error(Mesh::ValidationError, /must be less than or equal to/)
      end
    end
    
    context 'with image context' do
      let(:large_image) { double(width: 4096, height: 4096) }
      let(:params) { { internal_vertex_density: 50 } }
      
      it 'adds performance warnings for large images' do
        validator = described_class.new(params, image: large_image)
        validator.validate!
        
        expect(validator.warnings).to include(/Consider reducing internal_vertex_density/)
      end
    end
  end
end
```