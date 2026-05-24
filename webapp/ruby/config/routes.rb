Rails.application.routes.draw do
  scope :api, defaults: { format: :json } do
    get  "health",            to: "health#show"
    get  "employees",         to: "employees#index"
    get  "areas",             to: "areas#index"
    get  "duties",            to: "duties#index"
    post "duties/generate",   to: "duties#generate"
  end
end
