FactoryBot.define do
  factory :processing_log do
    project { nil }
    step { "MyString" }
    status { "MyString" }
    message { "MyText" }
    metadata { "" }
  end
end
