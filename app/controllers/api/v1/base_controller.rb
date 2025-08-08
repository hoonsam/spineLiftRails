class Api::V1::BaseController < ActionController::API
  before_action :authenticate_user!
  
  rescue_from ActiveRecord::RecordNotFound do |e|
    render json: { error: e.message }, status: :not_found
  end
  
  rescue_from ActiveRecord::RecordInvalid do |e|
    render json: { errors: e.record.errors.full_messages }, status: :unprocessable_entity
  end
  
  private
  
  def authenticate_user!
    token = request.headers['Authorization']&.split(' ')&.last
    return render_unauthorized unless token
    
    begin
      decoded_token = JWT.decode(token, Rails.application.secret_key_base, true, algorithm: 'HS256')
      @current_user = User.find(decoded_token.first['user_id'])
    rescue JWT::DecodeError, ActiveRecord::RecordNotFound
      render_unauthorized
    end
  end
  
  def current_user
    @current_user
  end
  
  def render_unauthorized
    render json: { error: 'Unauthorized' }, status: :unauthorized
  end
end