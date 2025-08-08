require 'sidekiq/web'

Rails.application.routes.draw do
  devise_for :users
  
  # Mount Sidekiq Web UI (protected by authentication)
  authenticate :user do
    mount Sidekiq::Web => '/sidekiq'
  end
  
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Render dynamic PWA files from app/views/pwa/* (remember to link manifest in application.html.erb)
  # get "manifest" => "rails/pwa#manifest", as: :pwa_manifest
  # get "service-worker" => "rails/pwa#service_worker", as: :pwa_service_worker

  # Defines the root path route ("/")
  # root "posts#index"
  
  # API routes
  namespace :api do
    namespace :v1 do
      # Authentication
      post 'auth/login', to: 'auth#login'
      post 'auth/register', to: 'auth#register'
      get 'auth/me', to: 'auth#me'
      
      # Projects
      resources :projects do
        member do
          get 'processing_status'
          post 'cancel_processing'
          post 'processing_callback'
        end
        
        resources :layers, only: [:index, :show, :update] do
          resource :mesh, only: [:show, :update] do
            member do
              put 'update_parameters'
            end
          end
        end
      end
      
      # Progress callback endpoint for Python service
      post 'mesh_progress', to: 'mesh_progress#create'
    end
  end
  
  # Mount ActionCable
  mount ActionCable.server => '/cable'
end
