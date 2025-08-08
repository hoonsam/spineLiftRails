# This file should ensure the existence of records required to run the application in every environment (production,
# development, test). The code here should be idempotent so that it can be executed at any point in every environment.
# The data can then be loaded with the bin/rails db:seed command (or created alongside the database with db:setup).

# Create demo user
demo_user = User.find_or_create_by!(email: 'demo@example.com') do |user|
  user.password = 'password123'
  user.name = 'Demo User'
end

puts "Demo user created: #{demo_user.email}"
