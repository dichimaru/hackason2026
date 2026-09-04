Rails.application.routes.draw do
  scope :api, defaults: { format: :json } do
    get  "health",            to: "health#show"
    get  "people",                 to: "employees#index"
    get  "tasks",                  to: "areas#index"
    get  "lottery-results",        to: "duties#index"
    post "lottery-results/generate", to: "duties#generate"
  end
end
