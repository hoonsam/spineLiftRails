require 'net/http'
require 'json'
require 'uri'

# Get the first user's token using their session
user = User.first
token = JWT.encode({ user_id: user.id }, Rails.application.secret_key_base, 'HS256')

# Test the layers API
uri = URI.parse("http://localhost:3000/api/v1/projects/14/layers")
http = Net::HTTP.new(uri.host, uri.port)
request = Net::HTTP::Get.new(uri.request_uri)
request["Authorization"] = "Bearer #{token}"

response = http.request(request)
puts "Status: #{response.code}"
puts "Body: #{response.body}"

# Parse and pretty print if successful
if response.code == "200"
  data = JSON.parse(response.body)
  puts "\nFound #{data['data'].length} layers" if data['data']
end