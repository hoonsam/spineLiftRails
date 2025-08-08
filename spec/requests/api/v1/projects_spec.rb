require 'rails_helper'

RSpec.describe "Api::V1::Projects", type: :request do
  let(:user) { create(:user) }
  let(:auth_headers) do
    token = JWT.encode(
      { user_id: user.id, exp: 24.hours.from_now.to_i },
      Rails.application.secret_key_base,
      'HS256'
    )
    { 'Authorization' => "Bearer #{token}" }
  end
  
  describe "GET /api/v1/projects" do
    it "returns a list of projects" do
      create_list(:project, 3, user: user)
      
      get "/api/v1/projects", headers: auth_headers
      
      expect(response).to have_http_status(:success)
      json = JSON.parse(response.body)
      expect(json['data'].length).to eq(3)
    end
    
    it "returns unauthorized without token" do
      get "/api/v1/projects"
      
      expect(response).to have_http_status(:unauthorized)
    end
  end
  
  describe "POST /api/v1/projects" do
    let(:psd_file) do
      fixture_file_upload('test.psd', 'image/vnd.adobe.photoshop')
    end
    
    it "creates a new project with PSD file" do
      expect {
        post "/api/v1/projects", 
          params: { name: "Test Project", psd_file: psd_file },
          headers: auth_headers
      }.to change(Project, :count).by(1)
      
      expect(response).to have_http_status(:created)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']['name']).to eq("Test Project")
      expect(json['data']['attributes']['status']).to eq("pending")
    end
  end
end