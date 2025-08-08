class Api::V1::AuthController < Api::V1::BaseController
  skip_before_action :authenticate_user!, only: [:login, :register]
  
  def me
    render json: {
      user: UserSerializer.new(current_user).serializable_hash
    }
  end
  
  def login
    user = User.find_by(email: params[:email])
    
    if user&.valid_password?(params[:password])
      token = generate_token(user)
      render json: {
        token: token,
        user: UserSerializer.new(user).serializable_hash
      }
    else
      render json: { error: 'Invalid credentials' }, status: :unauthorized
    end
  end
  
  def register
    user = User.new(user_params)
    
    if user.save
      token = generate_token(user)
      render json: {
        token: token,
        user: UserSerializer.new(user).serializable_hash
      }, status: :created
    else
      render json: { errors: user.errors.full_messages }, status: :unprocessable_entity
    end
  end
  
  private
  
  def user_params
    params.permit(:email, :password, :password_confirmation, :name)
  end
  
  def generate_token(user)
    JWT.encode(
      { user_id: user.id, exp: 24.hours.from_now.to_i },
      Rails.application.secret_key_base,
      'HS256'
    )
  end
end